#!/usr/bin/env python3
"""Coordinator-owned, flock-protected study ledger with recorded budget grants.

Initialize one ledger on the laptop/coordinator, reserve there before any local or
remote launch, then finish there using the returned run_job JSON. Remote workers
never create their own ledger. Outstanding reservations survive interruptions;
only an explicit finish/reconcile backed by an actual record releases them.
Reservation sizes include CPU-cap overshoot margin. No new reservation can exceed
the remaining global or category allocation; measured overshoot is charged in full.
"""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import sys
import uuid

from run_job import add_caps, atomic_json, positive, run_job, utc

TOTAL_US = 24 * 3600 * 1000000
INITIAL = {"native": 4, "kernel": 12, "compiled": 4, "assembly": 4}


def micros(seconds):
    return math.ceil(positive(seconds) * 1000000)


class Ledger:
    def __init__(self, path):
        self.path = Path(path).resolve()

    @contextlib.contextmanager
    def transaction(self, create=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_name(self.path.name + ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.path.exists():
                state = json.loads(self.path.read_text())
                if state["coordinator_host"] != socket.gethostname():
                    raise ValueError("ledger writes belong to the coordinator host")
                grants = state.get("budget_grants", {})
                granted = sum(sum(entry["allocations_us"].values()) for entry in grants.values())
                if (state["total_cpu_us"] != TOTAL_US + granted or
                        set(state["allocations_us"]) != set(INITIAL) or
                        any(type(value) is not int or value < 0
                            for value in state["allocations_us"].values()) or
                        sum(state["allocations_us"].values()) != state["total_cpu_us"]):
                    raise ValueError("invalid global ledger limit or unrecorded budget grant")
            elif create:
                state = {"format": "othello-study6-ledger-v1",
                         "coordinator_host": socket.gethostname(), "created_utc": utc(),
                         "total_cpu_us": TOTAL_US,
                         "allocations_us": {key: hours * 3600 * 1000000 for key, hours in INITIAL.items()},
                         "reservations": {}, "finished": {}}
            else:
                raise ValueError("initialize the single coordinator ledger explicitly with init")
            yield state
            atomic_json(self.path, state)
            directory = os.open(self.path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)

    def init(self):
        with self.transaction(create=True) as state:
            return self.summary(state)

    @staticmethod
    def summary(state):
        charged = sum(record["charged_cpu_us"] for record in state["finished"].values())
        reserved = sum(record["reserved_cpu_us"] for record in state["reservations"].values())
        withheld = sum(record["cpu_us"] for record in state.get("withheld", {}).values())
        categories = {}
        for category, allocation in state["allocations_us"].items():
            used = sum(r["charged_cpu_us"] for r in state["finished"].values() if r["category"] == category)
            held = sum(r["reserved_cpu_us"] for r in state["reservations"].values() if r["category"] == category)
            excluded = sum(r["cpu_us"] for r in state.get("withheld", {}).values() if r["category"] == category)
            categories[category] = {"allocation_cpu_seconds": allocation / 1e6,
                                    "charged_cpu_seconds": used / 1e6,
                                    "reserved_cpu_seconds": held / 1e6,
                                    "withheld_cpu_seconds": excluded / 1e6,
                                    "available_cpu_seconds": (allocation - used - held - excluded) / 1e6}
        total = state["total_cpu_us"]
        return {"coordinator_host": state["coordinator_host"], "total_cpu_seconds": total / 1e6,
                "charged_cpu_seconds": charged / 1e6, "reserved_cpu_seconds": reserved / 1e6,
                "withheld_cpu_seconds": withheld / 1e6,
                "available_cpu_seconds": (total - charged - reserved - withheld) / 1e6,
                "budget_grants": state.get("budget_grants", {}),
                "categories": categories, "outstanding": state["reservations"]}

    def status(self):
        with self.transaction() as state:
            return self.summary(state)

    def reserve(self, category, seconds, job=None):
        amount = micros(seconds)
        with self.transaction() as state:
            summary = self.summary(state)
            if category not in summary["categories"]:
                raise ValueError("unknown category")
            if amount > round(summary["available_cpu_seconds"] * 1e6):
                raise ValueError("insufficient global CPU budget")
            if amount > round(summary["categories"][category]["available_cpu_seconds"] * 1e6):
                raise ValueError("insufficient category CPU budget; explicitly reassign unused allocation")
            identifier = uuid.uuid4().hex
            entry = {"reservation_id": identifier, "category": category,
                     "reserved_cpu_us": amount, "reserved_cpu_seconds": amount / 1e6,
                     "job": job, "reserved_utc": utc()}
            state["reservations"][identifier] = entry
            return dict(entry)

    def finish(self, identifier, record_path):
        path = Path(record_path).resolve()
        raw = path.read_bytes()
        record = json.loads(raw)
        if record.get("reservation_id") != identifier:
            raise ValueError("actual job record does not match reservation")
        cpu = record.get("cpu_seconds")
        if not isinstance(cpu, (int, float)) or not math.isfinite(cpu) or cpu < 0:
            raise ValueError("actual record requires finite nonnegative CPU seconds")
        if "rusage" not in record or "exit_code" not in record or not record.get("finished_utc"):
            raise ValueError("actual record is incomplete; reservation remains outstanding")
        usage = record["rusage"]
        exact = usage.get("user_seconds", -1) + usage.get("system_seconds", -1)
        if not math.isclose(cpu, exact, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("record CPU does not match final rusage")
        charged = math.ceil(cpu * 1e6)
        with self.transaction() as state:
            if identifier in state["finished"]:
                previous = state["finished"][identifier]
                if previous["record_sha256"] == hashlib.sha256(raw).hexdigest():
                    return dict(previous)
                raise ValueError("reservation already finished with a different record")
            if identifier not in state["reservations"]:
                raise ValueError("unknown reservation")
            entry = state["reservations"].pop(identifier)
            entry.update(charged_cpu_us=charged, actual_cpu_seconds=cpu,
                         record=str(path), record_sha256=hashlib.sha256(raw).hexdigest(),
                         machine=record.get("machine"), accepted=record.get("accepted", False),
                         finished_utc=utc(), reservation_exceeded=charged > entry["reserved_cpu_us"])
            state["finished"][identifier] = entry
            return dict(entry)

    def reassign(self, origin, destination, seconds):
        amount = micros(seconds)
        with self.transaction() as state:
            categories = self.summary(state)["categories"]
            if origin not in categories or destination not in categories or origin == destination:
                raise ValueError("provide distinct known categories")
            if amount > round(categories[origin]["available_cpu_seconds"] * 1e6):
                raise ValueError("only unused, unreserved allocation can be reassigned")
            state["allocations_us"][origin] -= amount
            state["allocations_us"][destination] += amount
            return self.summary(state)

    def extend(self, grant_id, allocations, note):
        """Record an authorized additional stage without resetting past usage."""
        if not grant_id.strip() or not note.strip() or not allocations:
            raise ValueError("budget extension requires an identifier, allocations and authorization note")
        if any(category not in INITIAL for category in allocations):
            raise ValueError("unknown category")
        amounts = {category: micros(seconds) for category, seconds in allocations.items()}
        with self.transaction() as state:
            grants = state.setdefault("budget_grants", {})
            if grant_id in grants:
                if (grants[grant_id]["allocations_us"] != amounts or
                        grants[grant_id]["note"] != note):
                    raise ValueError("budget grant identifier already used with different details")
                return self.summary(state)
            grants[grant_id] = {"allocations_us": amounts, "note": note, "created_utc": utc()}
            state["total_cpu_us"] += sum(amounts.values())
            for category, amount in amounts.items():
                state["allocations_us"][category] += amount
            return self.summary(state)

    def withhold(self, category, seconds, note):
        """Exclude a conservative allowance; never label it measured CPU."""
        amount = micros(seconds)
        if not note.strip():
            raise ValueError("a withholding explanation is required")
        with self.transaction() as state:
            summary = self.summary(state)
            if category not in summary["categories"]:
                raise ValueError("unknown category")
            if amount > round(summary["categories"][category]["available_cpu_seconds"] * 1e6):
                raise ValueError("insufficient category allowance")
            identifier = uuid.uuid4().hex
            entry = {"category": category, "cpu_us": amount, "note": note, "created_utc": utc()}
            state.setdefault("withheld", {})[identifier] = entry
            return {"withholding_id": identifier, **entry}

    def import_record(self, category, record_path, note):
        """Charge a real pre-ledger run without altering or backdating its record."""
        path = Path(record_path).resolve()
        raw = path.read_bytes()
        record = json.loads(raw)
        cpu = record.get("cpu_seconds")
        if record.get("reservation_id") is not None:
            raise ValueError("reserved jobs must use finish")
        if not note.strip() or not isinstance(cpu, (int, float)) or not math.isfinite(cpu) or cpu < 0:
            raise ValueError("a note and finite final CPU are required")
        usage = record.get("rusage", {})
        if "exit_code" not in record or not record.get("finished_utc") or not math.isclose(
                cpu, usage.get("user_seconds", -1) + usage.get("system_seconds", -1),
                rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("prior record requires complete final rusage")
        identifier = "import-" + hashlib.sha256(raw).hexdigest()
        charged = math.ceil(cpu * 1e6)
        with self.transaction() as state:
            if identifier in state["finished"]:
                previous = state["finished"][identifier]
                if previous["category"] != category:
                    raise ValueError("record was already charged to a different category")
                return dict(previous)
            summary = self.summary(state)
            if category not in summary["categories"]:
                raise ValueError("unknown category")
            entry = {"reservation_id": None, "kind": "imported-prior-run", "category": category,
                     "job": record.get("label"), "reserved_cpu_us": 0,
                     "charged_cpu_us": charged, "actual_cpu_seconds": cpu,
                     "record": str(path), "record_sha256": hashlib.sha256(raw).hexdigest(),
                     "machine": record.get("machine"), "accepted": record.get("accepted", False),
                     "finished_utc": utc(), "note": note, "reservation_exceeded": True}
            state["finished"][identifier] = entry
            return dict(entry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path,
                        help="explicit path to the sole coordinator ledger")
    subs = parser.add_subparsers(dest="action", required=True)
    subs.add_parser("init")
    subs.add_parser("status")
    reserve = subs.add_parser("reserve")
    reserve.add_argument("category", choices=INITIAL)
    reserve.add_argument("seconds", type=positive)
    reserve.add_argument("--job")
    for name in ("finish", "reconcile"):
        finish = subs.add_parser(name)
        finish.add_argument("reservation_id")
        finish.add_argument("record", type=Path)
    reassign = subs.add_parser("reassign")
    reassign.add_argument("origin", choices=INITIAL)
    reassign.add_argument("destination", choices=INITIAL)
    reassign.add_argument("seconds", type=positive)
    extend = subs.add_parser("extend")
    extend.add_argument("grant_id")
    extend.add_argument("--note", required=True)
    for category in INITIAL:
        extend.add_argument("--" + category + "-seconds", type=positive)
    hold = subs.add_parser("withhold")
    hold.add_argument("category", choices=INITIAL)
    hold.add_argument("seconds", type=positive)
    hold.add_argument("--note", required=True)
    prior = subs.add_parser("import-record")
    prior.add_argument("category", choices=INITIAL)
    prior.add_argument("record", type=Path)
    prior.add_argument("--note", required=True)
    local = subs.add_parser("local-run")
    local.add_argument("category", choices=INITIAL)
    local.add_argument("label")
    local.add_argument("output", type=Path)
    local.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    local.add_argument("--expected-source-sha256")
    local.add_argument("--reserve-seconds", type=positive,
                       help="CPU cap plus conservative aggregate overshoot allowance")
    add_caps(local)
    split = sys.argv.index("--") if "--" in sys.argv else len(sys.argv)
    args = parser.parse_args(sys.argv[1:split])
    ledger = Ledger(args.ledger)
    try:
        if args.action == "init":
            result = ledger.init()
        elif args.action == "status":
            result = ledger.status()
        elif args.action == "reserve":
            result = ledger.reserve(args.category, args.seconds, args.job)
        elif args.action in ("finish", "reconcile"):
            result = ledger.finish(args.reservation_id, args.record)
        elif args.action == "reassign":
            result = ledger.reassign(args.origin, args.destination, args.seconds)
        elif args.action == "extend":
            allocations = {category: getattr(args, category + "_seconds")
                           for category in INITIAL
                           if getattr(args, category + "_seconds") is not None}
            result = ledger.extend(args.grant_id, allocations, args.note)
        elif args.action == "withhold":
            result = ledger.withhold(args.category, args.seconds, args.note)
        elif args.action == "import-record":
            result = ledger.import_record(args.category, args.record, args.note)
        else:
            if split == len(sys.argv) or not sys.argv[split + 1:]:
                parser.error("local-run requires -- COMMAND")
            import re
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.label):
                parser.error("invalid label")
            margin = max(1, (os.cpu_count() or 1) * 0.1)
            reserved = args.reserve_seconds if args.reserve_seconds is not None else args.cpu_limit + margin
            if reserved < args.cpu_limit + margin:
                parser.error("reservation must cover CPU cap plus conservative machine sampling margin")
            entry = ledger.reserve(args.category, reserved, args.label)
            # Any exception/crash leaves this reservation outstanding for explicit reconciliation.
            print(json.dumps(entry), flush=True)
            result = run_job(args.label, sys.argv[split + 1:], args.output, root=args.root,
                             timeout=args.timeout, cpu_limit=args.cpu_limit,
                             rss_limit_gib=args.rss_limit_gib, log_limit_mib=args.log_limit_mib,
                             expected_source_sha256=args.expected_source_sha256,
                             reservation_id=entry["reservation_id"])
            ledger.finish(entry["reservation_id"], args.output / (args.label + ".json"))
            print(json.dumps(result, indent=2))
            return 0 if result["accepted"] else 1
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
