#!/usr/bin/env python3
"""Run a Linux process group under resource caps and retain auditable measurements.

wait4 reports exact final CPU for the command and its reaped descendants. Linux
subreaper adoption also accounts for orphan descendants. Samples of /proc provide
tree RSS and a monotonic CPU lower bound: children shorter than the sample interval
can be missed, so this is not an exact instantaneous aggregate CPU enforcement.
RLIMIT_CPU separately limits each process; reservations must allow for sampling
overshoot. Final wait4 CPU, including overshoot, is always charged by study6.
"""
from __future__ import annotations
import argparse
import contextlib
import ctypes
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import re
import selectors
import shutil
import signal
import socket
import stat
import subprocess
import time

from provenance import source_identity

LOCK_ROOT_ENV = "OTHELLO_STUDY6_LOCK_ROOT"
LOCK_FD_ENV = "OTHELLO_STUDY6_LOCK_FD"
_held_locks = {}


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("caps must be finite and positive")
    return number


def build_lock_path(root: Path) -> Path:
    build = (root.resolve() / "_build").resolve()
    build.mkdir(parents=True, exist_ok=True)
    return build / ".study6.lock"


@contextlib.contextmanager
def build_lock(root: Path):
    root = Path(root).resolve()
    previous = _held_locks.get(root)
    borrowed = previous if previous is not None else _inherited_lock(root)
    if borrowed is not None:
        _held_locks[root] = borrowed
        try:
            yield
        finally:
            if previous is None:
                _held_locks.pop(root, None)
        # The inherited open file description belongs to the ancestor. Neither
        # unlocking nor closing it here may end that ancestor's critical section.
        return
    with build_lock_path(root).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _held_locks[root] = lock.fileno()
        try:
            yield
        finally:
            _held_locks.pop(root, None)


def _inherited_lock(root):
    if os.environ.get(LOCK_ROOT_ENV) != str(root):
        return None
    try:
        fd = int(os.environ[LOCK_FD_ENV])
        descriptor = os.fstat(fd)
        canonical = build_lock_path(root).stat()
    except (KeyError, ValueError, OSError):
        return None
    if not stat.S_ISREG(descriptor.st_mode) or (descriptor.st_dev, descriptor.st_ino) != (canonical.st_dev, canonical.st_ino):
        return None
    # Environment text is only a hint. flock verifies actual ownership: a
    # duplicated inherited description succeeds while a competing open fails.
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise ValueError("inherited build lock descriptor conflicts with the canonical lock") from error
    except OSError:
        return None
    return fd


def tree_sample(group, known=()):
    processes = {}
    ticks = os.sysconf("SC_CLK_TCK")
    pages = os.sysconf("SC_PAGE_SIZE")
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            raw = (path / "stat").read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            processes[int(path.name)] = {
                "parent": int(fields[1]), "group": int(fields[2]), "start": fields[19],
                "cpu": (int(fields[11]) + int(fields[12])) / ticks,
                "rss_kib": max(0, int(fields[21])) * pages // 1024,
            }
        except (OSError, ValueError, IndexError):
            continue
    # Nested runners start new sessions. Follow ancestry as well as the initial
    # process group, including orphans adopted by this dedicated subreaper.
    included = {pid for pid, p in processes.items()
                if p["group"] == group or (pid, p["start"]) in known}
    while True:
        expanded = included | {pid for pid, p in processes.items() if p["parent"] in included}
        if expanded == included:
            break
        included = expanded
    return {(pid, processes[pid]["start"]): processes[pid] for pid in included}


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    with temporary.open("w") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def run_job(label, command, output, *, root, timeout=7200, cpu_limit=7200,
            rss_limit_gib=16, log_limit_mib=8, reservation_id=None,
            expected_source_sha256=None, metadata=None, locked=False):
    for value in (timeout, cpu_limit, rss_limit_gib, log_limit_mib):
        positive(value)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", label):
        raise ValueError("invalid label")
    if not command:
        raise ValueError("command is required")
    root = Path(root).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    # The caller can hold this lock while preparing the command/cache metadata.
    with (contextlib.nullcontext() if locked else build_lock(root)):
        return _run(label, command, output, root, timeout, cpu_limit,
                    rss_limit_gib, log_limit_mib, reservation_id,
                    expected_source_sha256, metadata)


def _run(label, command, output, root, timeout, cpu_limit, rss_limit_gib,
         log_limit_mib, reservation_id, expected_source_sha256, metadata):
    source = source_identity(root)
    executable = shutil.which(command[0])
    if not executable:
        candidate = root / command[0]
        if candidate.is_file():
            executable = str(candidate)
    if not executable:
        raise FileNotFoundError(command[0])
    executable = Path(executable).resolve()
    command = [str(executable), *command[1:]]
    result = {"format": "othello-job-v2", "label": label, **source,
              "argv": command, "command": command, "flags": command[1:],
              "executable_path": str(executable),
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "machine": socket.gethostname(), "platform": list(os.uname()),
              "root": str(root), "build_lock": str(build_lock_path(root)),
              "reservation_id": reservation_id,
              "expected_source_sha256": expected_source_sha256,
              "timeout_seconds": timeout, "cpu_limit_seconds": cpu_limit,
              "rss_stop_threshold_gib": rss_limit_gib, "log_limit_mib": log_limit_mib,
              "cache_state": {"interfaces_before": len(list(root.rglob("*.agdai")))},
              "disk_free_bytes_before": shutil.disk_usage(root).free,
              "started_utc": utc(), "sample_interval_seconds": 0.05,
              "cpu_accounting": "wait4, including reaped descendants and adopted Linux orphans",
              "sampling_caveat": "Transient children may escape /proc CPU/RSS samples; CPU cap can overshoot; RLIMIT_CPU is per process."}
    if metadata:
        result.update(metadata)
    result["interfaces_before"] = result["cache_state"]["interfaces_before"]
    result["memory_before"] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, data = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            result["memory_before"][key + "_kib"] = int(data.split()[0])
    # PR_SET_CHILD_SUBREAPER makes orphaned grandchildren waitable by this runner.
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "cannot enable Linux child subreaper")
    def limits():
        seconds = max(1, math.ceil(cpu_limit))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    started = time.monotonic()
    lock_fd = _held_locks.get(root)
    if lock_fd is None:
        # locked=True is still the caller's promise; build_lock callers also
        # receive descriptor propagation without changing its yield value.
        lock_fd = _inherited_lock(root)
    environment = os.environ.copy()
    environment.pop(LOCK_ROOT_ENV, None)
    environment.pop(LOCK_FD_ENV, None)
    if lock_fd is not None:
        environment.update({LOCK_ROOT_ENV: str(root), LOCK_FD_ENV: str(lock_fd)})
    process = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, start_new_session=True,
                               preexec_fn=limits, env=environment,
                               pass_fds=() if lock_fd is None else (lock_fd,))
    os.set_blocking(process.stdout.fileno(), False)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    usage = {"user_seconds": 0.0, "system_seconds": 0.0,
             "max_rss_kib": 0, "minor_faults": 0, "major_faults": 0,
             "voluntary_context_switches": 0, "involuntary_context_switches": 0}
    observed = {}
    peak = 0
    log_bytes = 0
    stop_reason = None
    code = None
    pipe_open = True
    interrupted = False
    def kill_group():
        # Nested runners create their own sessions. Kill descendants in those
        # sessions too, while their parent links are still available in /proc.
        parents, starts = {}, {}
        for path in Path("/proc").iterdir():
            if path.name.isdigit():
                try:
                    raw = (path / "stat").read_text()
                    fields = raw[raw.rfind(")") + 2:].split()
                    parents[int(path.name)] = int(fields[1])
                    starts[int(path.name)] = fields[19]
                except (OSError, ValueError, IndexError):
                    continue
        descendants = {process.pid} | {pid for pid, start in observed if starts.get(pid) == start}
        while True:
            expanded = descendants | {pid for pid, parent in parents.items() if parent in descendants}
            if expanded == descendants:
                break
            descendants = expanded
        for pid in descendants - {process.pid}:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    previous_signals = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    for sig in previous_signals:
        signal.signal(sig, interrupt)
    with (output / (label + ".log")).open("wb") as log:
        try:
            while True:
                while True:
                    try:
                        pid, status, ru = os.wait4(-1, os.WNOHANG)
                    except ChildProcessError:
                        break
                    if not pid:
                        break
                    usage["user_seconds"] += ru.ru_utime
                    usage["system_seconds"] += ru.ru_stime
                    usage["max_rss_kib"] = max(usage["max_rss_kib"], ru.ru_maxrss)
                    for key, attr in (("minor_faults", "ru_minflt"), ("major_faults", "ru_majflt"),
                                      ("voluntary_context_switches", "ru_nvcsw"),
                                      ("involuntary_context_switches", "ru_nivcsw")):
                        usage[key] += getattr(ru, attr)
                    if pid == process.pid:
                        code = os.waitstatus_to_exitcode(status)
                        process.returncode = code
                sample = tree_sample(process.pid, observed)
                peak = max(peak, sum(entry["rss_kib"] for entry in sample.values()))
                for pid, entry in sample.items():
                    observed[pid] = max(observed.get(pid, 0), entry["cpu"])
                sampled_cpu = max(sum(observed.values()), usage["user_seconds"] + usage["system_seconds"])
                if not stop_reason:
                    if time.monotonic() - started >= timeout:
                        stop_reason = "timeout"
                    elif sampled_cpu >= cpu_limit:
                        stop_reason = "cpu-limit"
                    elif peak >= rss_limit_gib * 1024 ** 2:
                        stop_reason = "rss-threshold"
                    elif code in (-signal.SIGXCPU, -signal.SIGKILL) and sampled_cpu >= math.floor(cpu_limit):
                        stop_reason = "cpu-limit"
                    if stop_reason:
                        kill_group()
                if code is not None and not sample and not pipe_open:
                    break
                for key, _ in selector.select(0.05):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        pipe_open = False
                        continue
                    available = max(0, int(log_limit_mib * 1024 ** 2) - log_bytes)
                    log.write(chunk[:available])
                    log_bytes += len(chunk[:available])
                    if len(chunk) > available and not stop_reason:
                        stop_reason = "log-size"
                        kill_group()
        except BaseException:
            interrupted = True
            stop_reason = "interrupted"
            kill_group()
            while True:
                try:
                    pid, status, ru = os.wait4(-1, 0)
                except ChildProcessError:
                    break
                usage["user_seconds"] += ru.ru_utime
                usage["system_seconds"] += ru.ru_stime
                usage["max_rss_kib"] = max(usage["max_rss_kib"], ru.ru_maxrss)
                if pid == process.pid:
                    code = os.waitstatus_to_exitcode(status)
                    process.returncode = code
        finally:
            selector.close()
            process.stdout.close()
            for sig, handler in previous_signals.items():
                signal.signal(sig, handler)
    wall_seconds = time.monotonic() - started
    if stop_reason is None and usage["user_seconds"] + usage["system_seconds"] >= cpu_limit:
        stop_reason = "cpu-limit"
    try:
        unchanged = source_identity(root)["source_sha256"] == source["source_sha256"]
    except (ValueError, OSError):
        unchanged = False
    expected_matches = expected_source_sha256 is None or expected_source_sha256 == source["source_sha256"]
    result.update(exit_code=code, exit_status=code, stop_reason=stop_reason,
                  wall_seconds=wall_seconds,
                  cpu_seconds=usage["user_seconds"] + usage["system_seconds"],
                  rusage=usage, sampled_tree_cpu_seconds=sum(observed.values()),
                  peak_tree_rss_kib=peak, peak_rss_kib=max(peak, usage["max_rss_kib"]),
                  peak_rss_gib=max(peak, usage["max_rss_kib"]) / 1024 ** 2,
                  log_bytes=log_bytes, source_unchanged=unchanged,
                  expected_source_matches=expected_matches, finished_utc=utc(),
                  disk_free_bytes_after=shutil.disk_usage(root).free,
                  interfaces_after=len(list(root.rglob("*.agdai"))))
    result["cache_state"]["interfaces_after"] = result["interfaces_after"]
    result["accepted"] = code == 0 and stop_reason is None and unchanged and expected_matches and not interrupted
    atomic_json(output / (label + ".json"), result)
    return result


def add_caps(parser):
    parser.add_argument("--timeout", type=positive, default=7200)
    parser.add_argument("--cpu-limit", type=positive, default=7200)
    parser.add_argument("--rss-limit-gib", type=positive, default=16)
    parser.add_argument("--log-limit-mib", type=positive, default=8)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--reservation-id")
    parser.add_argument("--expected-source-sha256")
    add_caps(parser)
    # Explicit -- separates wrapper options from the command's arbitrary options.
    import sys
    if "--" not in sys.argv:
        parser.error("use -- before COMMAND")
    split = sys.argv.index("--")
    args = parser.parse_args(sys.argv[1:split])
    import re
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.label):
        parser.error("invalid label")
    result = run_job(args.label, sys.argv[split + 1:], args.output, root=args.root,
                     timeout=args.timeout, cpu_limit=args.cpu_limit,
                     rss_limit_gib=args.rss_limit_gib, log_limit_mib=args.log_limit_mib,
                     reservation_id=args.reservation_id,
                     expected_source_sha256=args.expected_source_sha256)
    print(json.dumps(result, indent=2))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
