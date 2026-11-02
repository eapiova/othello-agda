"""Untrusted, separately approved canonical-state row and linkage experiment.

This never launches native search or production. It repeats the existing 200
row assertions in fresh sources and checks their conditional full-map bridge.
The coordinator owns the enclosing CPU reservation and its sole outer charge.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import threading

import assembly6
from canonical_sample_parts6 import emit_canonical
import full_map_pilot6 as pilot
import new_row_bridge6 as bridge
from provenance import digest_entries, source_identity
from readonly_dependencies6 import command
from run_job import atomic_json, build_lock, run_job, utc
from wire_workflow6 import require

SCOPE = 'canonical-state-row-bridge-pilot6-v1'
ANSWER = 'Sì, autorizzo il test canonico'
SCOPE60 = SCOPE + '-floor60'
ANSWER60 = 'Sì, solo il test con soglia 60 GiB'
ROW_PREFIX = 'Tests.CanonicalDirectLower34176'
BRIDGE_PREFIX = 'Tests.CanonicalDirectFullBridge6'
SAMPLE_SHA = '11cb8b363ad0475378c78051bffbd58b3ebcf23a7eb0eed2dae289d3fbf14b9e'
FULL_MANIFEST_SHA = '883e3457b43bbbb0110bed3611b44617af43922f3ce2daa5a8bd56376673daff'


def approved(plan_raw, approval):
    spec = json.loads(plan_raw)
    floor = spec.get('free_disk_gib')
    require(type(floor) is int and floor in (60, 80), 'only reviewed60/80GiB scopes allowed')
    scope, answer = (SCOPE60, ANSWER60) if floor == 60 else (SCOPE, ANSWER)
    require(spec.get('scope') == scope, 'disk floor and reviewed scope differ')
    if floor == 60:
        require(spec.get('temporary_disk_floor_exception') is True
                and approval.get('temporary_disk_floor_exception') is True,
                'explicit test-only disk-floor exception required')
    required = dict(scope=scope, answer=answer, cpu_max_seconds=600,
                    hard_memory_gib=12, artifact_cap_gib=12, free_disk_gib=floor,
                    part=34176, repeated_boolean_rows=200, new_distinct_game_rows=0)
    require(approval.get('approved') is True
            and approval.get('plan_sha256') == hashlib.sha256(plan_raw).hexdigest()
            and all(approval.get(k) == v for k, v in required.items())
            and approval.get('native_search_allowed') is False
            and approval.get('production_authorized') is False,
            'distinct600CPU canonical pilot approval, explicitly repeating200 rows, required')
    return floor


def storage(current, extra=0, *, floor=80):
    """The global80GiB policy stays in pilot.storage; only this pilot may use60."""
    if floor == 80:
        return pilot.storage(current, extra)
    require(floor == 60, 'unreviewed disk floor refused')
    used = int(subprocess.check_output(['du','-s','-B1',str(current.parent)],text=True).split()[0])
    free = shutil.disk_usage(current).free
    require(used + extra < 12*2**30 and free-extra >= 60*2**30,
            'scoped60GiB floor or12GiB artifact limit reached; originals retained')
    return dict(allocated_study_bytes=used, free_bytes=free, reserved_extra_bytes=extra,
                artifact_cap_bytes=12*2**30, free_floor_bytes=60*2**30,
                temporary_disk_floor_exception=True, checked_utc=utc())


@contextlib.contextmanager
def watched_storage(current, out, *, floor=80):
    if floor == 80:
        with pilot.watched_storage(current, out):
            yield
        return
    require(floor == 60, 'unreviewed watcher floor refused')
    stop, errors = threading.Event(), []
    def watch():
        while not stop.wait(15):
            try:
                atomic_json(out/'storage.json', storage(current,64*2**20,floor=floor))
            except BaseException as error:
                errors.append(str(error)); os.kill(os.getpid(),signal.SIGTERM); return
    thread = threading.Thread(target=watch,daemon=True); thread.start()
    try:
        yield
    finally:
        stop.set(); thread.join()
        if errors:
            atomic_json(out/'storage-stop.json',dict(errors=errors,finished_utc=utc()))
    require(not errors,'scoped storage watcher stopped the pilot')


def checked_modules(log):
    return re.findall(r'(?m)^\s*Checking (\S+) \(', log)


def _command(machine, target, check, *, row=None, heap='-M1200M'):
    argv = command(machine, target, check, pilot.DONOR)
    i = argv.index('--') + 1
    includes = ['-i', str(bridge.FULL/'src'), '-i', str(bridge.ALIGNED/'src')]
    if row is not None:
        includes += ['-i', str(row/'src')]
    argv[i+4:i+4] = includes
    argv[argv.index('-M2700M')] = heap
    return argv


def run(current, out, plan_path, approval_path, sample_path):
    raw = plan_path.read_bytes(); spec = json.loads(raw)
    floor = approved(raw, json.loads(approval_path.read_text()))
    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == spec['worker_sha256'],
            'reviewed pilot worker differs')
    cap = resource.getrlimit(resource.RLIMIT_CPU)[0]
    require(cap != resource.RLIM_INFINITY and 0 < cap <= 540, '540CPU capped outer required')
    groups = [s[3:] for s in Path('/proc/self/cgroup').read_text().splitlines() if s.startswith('0::')]
    require(len(groups) == 1, 'one hard memory cgroup required')
    cg = Path('/sys/fs/cgroup') / groups[0].lstrip('/')
    maximum = (cg/'memory.max').read_text().strip()
    require(maximum.isdigit() and 0 < int(maximum) <= 12*2**30
            and (cg/'memory.swap.max').read_text().strip() == '0',
            'hard12GiB memory with no swap required')
    require(not out.exists() and not any(p.is_symlink() for p in (out, *out.parents)),
            'fresh pilot output required; no automatic retry')
    require(hashlib.sha256(sample_path.read_bytes()).hexdigest() == SAMPLE_SHA,
            'exact prepared200-row sample required')
    sample = json.loads(sample_path.read_text())
    sample['states'] = {int(j): v for j, v in sample['states'].items()}
    require(len(sample['cases']) == 1 and sample['cases'][0]['part'] == 34176
            and sample['cases'][0]['rows'] == 200 and len(sample['states']) == 503,
            'exact prepared row fixture required')
    storage(current,64*2**20,floor=floor)
    expected = {pilot.DONOR: (pilot.DONOR_SOURCE_SHA, pilot.DONOR_POOL_SHA),
                bridge.FULL: (bridge.FULL_SOURCE_SHA, bridge.FULL_POOL_SHA),
                bridge.ALIGNED: (bridge.ALIGNED_SOURCE, bridge.ALIGNED_POOL),
                bridge.ROW_BASE/'part-34176': (bridge.ROW_SOURCE, bridge.ROW_POOL)}
    with contextlib.ExitStack() as stack:
        for donor in sorted(expected):
            stack.enter_context(build_lock(donor))
        before = {}
        for donor, (source_sha, pool_sha) in expected.items():
            identity, pool = source_identity(donor), assembly6.interfaces(donor)
            require(identity['source_sha256'] == source_sha and digest_entries(pool) == pool_sha,
                    'immutable accepted donor changed')
            before[donor] = identity, pool
        _, _, _, machine = pilot.donor_identity()
        manifest_path = bridge.FULL/'results/full-state-map6.json'
        require(hashlib.sha256(manifest_path.read_bytes()).hexdigest() == FULL_MANIFEST_SHA,
                'complete accepted lower map manifest differs')
        full = json.loads(manifest_path.read_text())
        row, routes = out/'row-check', out/'bridge-check'
        layout = emit_canonical(row, sample, full, prefix=ROW_PREFIX)
        shutil.copy2(current/'othello.agda-lib', row/'othello.agda-lib')
        paths = bridge.emit(routes, full, sample, row_prefix=ROW_PREFIX, prefix=BRIDGE_PREFIX,
                            state_exports=layout['canonical_state_exports'])
        require(layout['generated_sha256'] == spec['row_generated_sha256']
                and paths['generated_sha256'] == spec['bridge_generated_sha256'],
                'generated experiment differs from reviewed prototypes')
        report = dict(format='othello-canonical-state-row-bridge-pilot6-v1', accepted=False,
                      status='checking-rows', created_utc=utc(), row_layout=layout, bridge_layout=paths,
                      repeated_boolean_rows=200, new_distinct_game_rows=0, native_search_allowed=False,
                      free_disk_gib=floor, temporary_disk_floor_exception=floor==60,
                      production_authorized=False, initial_problem2_proved=False,
                      optimal_initial_pair_proved=False, plan_sha256=hashlib.sha256(raw).hexdigest())
        atomic_json(out/'report.json', report)
        stack.enter_context(build_lock(row))
        with watched_storage(current,out,floor=floor):
            row_source = source_identity(row)
            report['row_storage_admission'] = storage(current,64*2**20,floor=floor)
            atomic_json(out/'report.json',report)
            row_rec = run_job('canonical-rows34176', _command(machine, ROW_PREFIX+'.Part34176', row),
                out/'records', root=row, locked=True, expected_source_sha256=row_source['source_sha256'],
                timeout=400, cpu_limit=240, rss_limit_gib=1.5, log_limit_mib=4,
                metadata=dict(checker_binary_sha256=pilot.AGDA_SHA, own_target_cold=True,
                              repeated_boolean_rows=200, new_distinct_game_rows=0))
            row_pool = assembly6.interfaces(row)
            seen_row = checked_modules((out/'records/canonical-rows34176.log').read_text())
            row_ok = bool(row_rec['accepted'] and len(row_pool) == 3 and set(seen_row) == {
                ROW_PREFIX+'.Family', ROW_PREFIX+'.BodyData34176', ROW_PREFIX+'.Part34176'})
            report.update(row_record=row_rec, row_source=row_source, row_accepted=row_ok,
                          row_checked_modules=seen_row, row_interface_pool_sha256=digest_entries(row_pool))
            atomic_json(out/'row-interface-map.json', row_pool)
            atomic_json(out/'report.json', report)
            require(row_ok, 'row phase did not pass; preserve artifacts and stop')
            report['status'] = 'checking-bridge'; atomic_json(out/'report.json', report)
            route_source = source_identity(routes)
            report['bridge_storage_admission'] = storage(current,64*2**20,floor=floor)
            atomic_json(out/'report.json',report)
            route_rec = run_job('canonical-bridge34176',
                _command(machine, BRIDGE_PREFIX+'.Root', routes, row=row, heap='-M10G'),
                out/'records', root=routes, expected_source_sha256=route_source['source_sha256'],
                timeout=400, cpu_limit=240, rss_limit_gib=11.5, log_limit_mib=4,
                metadata=dict(checker_binary_sha256=pilot.AGDA_SHA, own_target_cold=True,
                              new_boolean_rows=0, repeated_boolean_rows=0))
        seen_routes = checked_modules((out/'records/canonical-bridge34176.log').read_text())
        route_pool = assembly6.interfaces(routes)
        immutable = all(source_identity(p) == s and assembly6.interfaces(p) == cache
                        for p, (s, cache) in before.items())
        row_intact = source_identity(row) == row_source and assembly6.interfaces(row) == row_pool
        expected_routes = {BRIDGE_PREFIX+'.Root'} | {BRIDGE_PREFIX+'.Batch'+str(i) for i in range(16)}
        accepted = bool(route_rec['accepted'] and len(route_pool) == 17
                        and set(seen_routes) == expected_routes and immutable and row_intact)
        atomic_json(out/'bridge-interface-map.json', route_pool)
        report.update(accepted=accepted, status='complete' if accepted else 'not-accepted',
                      bridge_record=route_rec, bridge_source=route_source, bridge_checked_modules=seen_routes,
                      bridge_interface_pool_sha256=digest_entries(route_pool), row_interfaces=3,
                      bridge_interfaces=len(route_pool), all_four_donors_unchanged=immutable,
                      accepted_new_row_phase_unchanged=row_intact,
                      storage=storage(current,floor=floor), finished_utc=utc())
        atomic_json(out/'report.json', report)
        require(accepted, 'canonical bridge did not pass; originals retained, no automatic retry')
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('plan', 'approval', 'sample', 'output'):
        parser.add_argument('--'+arg, type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd().resolve(), args.output.absolute(), args.plan, args.approval, args.sample)
