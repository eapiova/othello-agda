"""Resumable single-checker production for all remaining prepared 6x6 rows.

AI-assisted controller.  This checks only the frozen remaining Rows modules;
it does not import AllParts or Result and therefore does not claim Problem2.
Production must be launched under an explicit post-transfer authorization file.
The outer study6 reservation is intentionally left for manual reconciliation
from its terminal run_job record.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import zipfile

from compression import zstd

import assembly6
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
import full_row_records6 as records
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT = BASE/'full-row-production6-20261018'
CONTROL = OUT/'control'
UNIT = 'othello6-'+OUT.name+'.service'
FORECAST_FILE = ROOT/'results/complete-remaining-row-forecast6-20261018.json'
CONTINUATION_FILE = ROOT/'results/full-text-maps-continuation6-20261018.json'
REGISTRY_FILE = ROOT/'results/study6-external-artifacts-20261018.json'
LEDGER_FILE = ROOT/'results/study6-ledger.json'
HANDOFF = ROOT/'results/migration-handoff6-20261018-021658/handoff.json'
PRIVATE_CORE = BASE/'private-core-package6-20261018'
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
SIDES = ('upper', 'lower')
PREFIX = {'upper': 'Tests.CompleteUpperRows6', 'lower': 'Tests.CompleteLowerRows6'}
PROOF = {side: OUT/(side+'-proof') for side in SIDES}
ROW_ZIP = {side: OUT/(side+'-row-interfaces.zip') for side in SIDES}
LINEAGE = OUT/'row-interface-payload-lineage.json.zst'
RECORD_ZIP = OUT/'closed-child-records.zip'
PROGRESS = OUT/'progress.json'
TRANSACTION = OUT/'active-batch.json'
CHILD_CPU = 160
CHILD_WALL = 400
INITIAL_RESERVATION = 50000
INITIAL_OUTER_CPU = 49500
RUNTIME_MAX = 65000
GIB = 2**30
MIB = 2**20
EXPECTED_COUNTS = {'upper': 649, 'lower': 684}
OWNED = {'upper': {6, 100, 300, 500, 652}, 'lower': {6, 100, 300, 686}}
EXTRA_PATTERNS = previous.EXTRA_PATTERNS + [
    'global-upper-layout6-20261018*', 'step-existing-partial6-20261018*',
    'citation-diagnostic6-20261018*', 'shared-inline-scaling6-20261018*',
    'text-map-scaling6-20261018*']
HELPERS = ['full_row_production6.py', 'full_row_records6.py', 'assembly6.py',
           'big_rows_probe6.py', 'citation_diagnostic6.py', 'completion_batch6.py',
           'run_job.py', 'provenance.py', 'study6.py', 'study_archive6.py']

previous.OUT = OUT
common.OUT, common.HARD_GIB, common.RESERVATION_CPU = OUT, 12, INITIAL_RESERVATION


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def allocated(path):
    path = Path(path)
    return 0 if not path.exists() else int(subprocess.check_output(
        ['du', '-s', '-x', '-B1', str(path)], text=True).split()[0])


def read_json(path):
    return json.loads(Path(path).read_text())


def durable_json(path, data):
    records.atomic_bytes(Path(path), (json.dumps(data, indent=2)+'\n').encode(), mode=0o600)


def authorization(path, action):
    path = Path(path).resolve(strict=True)
    raw = read_json(path)
    require(raw.get('approved') is True and raw.get('category_transfer_applied') is True,
            'explicit applied-cap authorization is required')
    require(raw.get('output') == str(OUT) and raw.get('total_cpu_seconds') == 172800,
            'authorization output or unchanged total differs')
    require(raw.get('child_cpu_limit_seconds') == CHILD_CPU
            and raw.get('child_wall_limit_seconds') == CHILD_WALL,
            'child caps differ from the frozen production caps')
    require(raw.get('runtime_max_seconds') == RUNTIME_MAX,
            'service wall cap differs from the frozen production cap')
    applied = raw.get('applied_unused_category_reallocation', {})
    require(applied == {'compiled_to_kernel_cpu_seconds': 8000,
                        'native_to_kernel_cpu_seconds': 5000},
            'the exact approved unused-category transfer must be recorded as applied')
    require(raw.get('ledger_sha256_after_transfer') == sha(LEDGER_FILE),
            'ledger differs from the post-transfer authorization pin')
    reserve = raw.get('reservation_cpu_seconds')
    outer = raw.get('outer_cpu_cap_seconds')
    require(isinstance(reserve, (int, float)) and isinstance(outer, (int, float))
            and 400 <= outer and outer+100 <= reserve <= INITIAL_RESERVATION,
            'finite reservation and outer caps are required')
    if action == 'launch':
        require(reserve == INITIAL_RESERVATION and outer == INITIAL_OUTER_CPU,
                'initial production requires the frozen 50000/49500 CPU caps')
    else:
        require(raw.get('resume') is True, 'resume requires a new explicit resume authorization')
    return path, raw


def census_prior():
    require(not OUT.exists(), 'initial census requires the registered output to be absent')
    common.OUT = OUT
    legacy = common.storage(0)
    paths = {p for pattern in EXTRA_PATTERNS for p in (ROOT/'results').glob(pattern)}
    registry = read_json(REGISTRY_FILE)
    registered = {Path(entry['path']) for entry in registry['roots']}
    require(OUT in registered, 'parent must register the production output before launch')
    if PRIVATE_CORE.exists():
        require(PRIVATE_CORE in registered, 'closed private core package must be registered')
    paths |= {p for p in registered if p != OUT}
    return legacy['allocated_study_bytes'] + sum(allocated(path) for path in paths), paths


def component_storage(plan, remaining=None, reserve=0):
    forecast = plan['forecast']['storage']
    row_allocated = sum(allocated(path) for path in ROW_ZIP.values())
    row_bytes = 0
    for path in ROW_ZIP.values():
        if path.exists():
            with zipfile.ZipFile(path) as archive:
                row_bytes += sum(info.file_size for info in archive.infolist())
    cache_meta_paths = [LINEAGE, OUT/'complete-row-cache-manifest.json']
    cache_meta_bytes = sum(allocated(path) for path in cache_meta_paths) + row_allocated-row_bytes
    record_bytes = allocated(RECORD_ZIP)
    own = allocated(OUT)
    scratch = max(0, own-row_allocated-sum(allocated(path) for path in cache_meta_paths)-record_bytes)
    require(row_bytes <= forecast['projected_row_cache_bytes'], 'row-frame cache cap reached')
    require(cache_meta_bytes <= forecast['cache_container_and_lineage_overhead_bytes'],
            'cache lineage/container cap reached')
    require(record_bytes <= forecast['future_closed_record_archive_cap_bytes'],
            'closed child-record archive cap reached')
    require(scratch <= forecast['batch_scratch_cap_bytes'], 'batch scratch cap reached')
    projected = (plan['prior_allocated_study_bytes'] +
                 forecast['projected_row_cache_bytes'] +
                 forecast['cache_container_and_lineage_overhead_bytes'] +
                 forecast['future_closed_record_archive_cap_bytes'] +
                 forecast['batch_scratch_cap_bytes'] +
                 forecast['final_assembly_interface_cap_bytes'] +
                 plan['private_core_remaining_allowance_bytes'] +
                 forecast['stop_reserve_bytes'])
    require(projected < 12*GIB, 'frozen completed-production projection exceeds retained cap')
    require(plan['prior_allocated_study_bytes']+own+reserve < 12*GIB,
            'physical retained study cap reached')
    root_free = shutil.disk_usage(ROOT).free
    data_free = shutil.disk_usage(OUT).free
    require(root_free-reserve >= 80*GIB and data_free-reserve >= 80*GIB,
            'ordinary free-disk floor reached')
    result = dict(checked_utc=utc(), prior_allocated_study_bytes=plan['prior_allocated_study_bytes'],
        own_output_bytes=own, row_payload_bytes=row_bytes, row_container_allocated_bytes=row_allocated,
        cache_metadata_and_container_bytes=cache_meta_bytes,
        closed_record_archive_bytes=record_bytes, scratch_bytes=scratch,
        frozen_completed_projection_bytes=projected, root_free_bytes=root_free,
        data_free_bytes=data_free, reserved_bytes=reserve,
        virtual_readonly_fuse_bytes_excluded=True)
    if remaining is not None:
        result['remaining_groups'] = remaining
    atomic_json(OUT/'storage.json', result)
    return result


def resources(plan):
    groups = [line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
              if line.startswith('0::')]
    require(len(groups) == 1, 'one unified cgroup required')
    group = Path('/sys/fs/cgroup')/groups[0].lstrip('/')
    require((group/'memory.max').read_text().strip() == str(12*GIB)
            and (group/'memory.swap.max').read_text().strip() == '0',
            'hard 12GiB/no-swap cgroup required')
    return group


def cgroup_cpu(group):
    values = dict(line.split() for line in (group/'cpu.stat').read_text().splitlines())
    return int(values['usage_usec'])/1e6


@contextlib.contextmanager
def watched(plan, group):
    stop = threading.Event()
    failures = []
    cutoff = plan['run']['outer_cpu_cap_seconds']-200

    def watch():
        while not stop.wait(3):
            try:
                require(cgroup_cpu(group) < cutoff, 'service CPU cleanup guard reached')
                component_storage(plan, reserve=4*MIB)
                available = next(int(line.split()[1])*1024 for line in
                    Path('/proc/meminfo').read_text().splitlines()
                    if line.startswith('MemAvailable:'))
                require(available >= 2*GIB, 'host memory headroom guard reached')
            except BaseException as error:
                failures.append(repr(error))
                atomic_json(OUT/'resource-stop.json', dict(reason=repr(error), finished_utc=utc(),
                    accepted_progress=progress_summary(plan)))
                os.kill(os.getpid(), signal.SIGTERM)
                return
    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set(); thread.join()
    require(not failures, 'resource watcher stopped production')


def load_lineage():
    return {} if not LINEAGE.exists() else json.loads(zstd.decompress(LINEAGE.read_bytes()))


def write_lineage(lineage):
    raw = (json.dumps(lineage, sort_keys=True, separators=(',', ':'))+'\n').encode()
    records.atomic_bytes(LINEAGE, zstd.compress(raw, level=19), mode=0o600)


def recover_append_journals():
    lineage = load_lineage()
    outcomes = {}
    row_journals = {side: records.read_append_journal(ROW_ZIP[side]) for side in SIDES}
    for side in SIDES:
        def row_committed(journal, side=side):
            match = re.fullmatch(r'Rows(\d+)\.agdai', journal['member'])
            if match is None:
                return False
            entry = lineage.get(side+'/'+journal['member'])
            return entry is not None and entry['new_sha256'] == journal['member_sha256']
        outcomes[side] = records.recover_append(ROW_ZIP[side], row_committed)
    progress = read_json(PROGRESS) if PROGRESS.exists() else {'record_cohorts': []}
    cohorts = {entry['member']: entry['sha256'] for entry in progress.get('record_cohorts', [])}
    outcomes['records'] = records.recover_append(RECORD_ZIP,
        lambda journal: cohorts.get(journal['member']) == journal['member_sha256'])
    for side in SIDES:
        if outcomes[side] == 'committed' and row_journals[side] is not None:
            match = re.fullmatch(r'Rows(\d+)\.agdai', row_journals[side]['member'])
            require(match is not None, 'committed row journal member is invalid')
            loose = row_interface(side, int(match.group(1)))
            if loose.exists():
                require(sha(loose) == lineage[side+'/'+row_journals[side]['member']]['new_sha256'],
                        'loose committed row differs from archive lineage')
                loose.unlink()
                records.fsync_directory(loose.parent)
    indexed = progress.get('record_cohorts', [])
    if indexed:
        require(RECORD_ZIP.is_file(), 'indexed record archive is missing')
        with zipfile.ZipFile(RECORD_ZIP) as archive:
            require(set(archive.namelist()) == {entry['member'] for entry in indexed},
                    'record archive inventory differs from its durable index')
            for entry in indexed:
                blob = archive.read(entry['member'])
                require(hashlib.sha256(blob).hexdigest() == entry['sha256'],
                        'record cohort hash differs from its durable index')
                records.verify_cohort_blob(blob)
        for entry in indexed:
            for item in entry['batch_records']:
                for relative in item['evidence_files']:
                    path = OUT/relative
                    if path.exists():
                        path.unlink()
                root = OUT/item['wrapper_root']
                if root.exists():
                    shutil.rmtree(root)
        records.fsync_directory(OUT)
    atomic_json(OUT/'append-journal-recovery.json', {'checked_utc': utc(), 'outcomes': outcomes})
    return outcomes


def zip_inventory(side):
    if not ROW_ZIP[side].exists():
        return {}
    with zipfile.ZipFile(ROW_ZIP[side]) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())),
                'duplicate row-cache members are forbidden')
        return {name: hashlib.sha256(archive.read(name)).hexdigest()
                for name in archive.namelist()}


def archived_groups(side):
    if not ROW_ZIP[side].exists():
        return set()
    with zipfile.ZipFile(ROW_ZIP[side]) as archive:
        names = archive.namelist()
    require(len(names) == len(set(names)), 'duplicate row-cache members are forbidden')
    found = set()
    for name in names:
        match = re.fullmatch(r'Rows(\d+)\.agdai', name)
        require(match is not None, 'row cache must remain flat and Rows-only')
        found.add(int(match.group(1)))
    return found


def verify_archived_rows(plan):
    lineage = load_lineage()
    found = {side: set() for side in SIDES}
    for side in SIDES:
        inventory = zip_inventory(side)
        with zipfile.ZipFile(ROW_ZIP[side]) if ROW_ZIP[side].exists() else contextlib.nullcontext() as archive:
            for name, pin in inventory.items():
                match = re.fullmatch(r'Rows(\d+)\.agdai', name)
                require(match is not None, 'row cache must remain flat and Rows-only')
                group = int(match.group(1)); key = side+'/'+name
                require(key in lineage and lineage[key]['new_sha256'] == pin,
                        'row archive lacks matching payload lineage')
                raw = archive.read(name)
                require(raw[:24].hex() == lineage[key]['header_hex']
                        and raw[24:28] == bytes.fromhex('28b52ffd'), 'row interface header differs')
                payload = zstd.decompress(raw[24:])
                require(hashlib.sha256(payload).hexdigest() == lineage[key]['decoded_payload_sha256'],
                        'row interface decoded payload differs')
                found[side].add(group)
    schedule = schedule_groups(plan)
    for side in SIDES:
        require(found[side] <= schedule[side] | {100, 300}, 'unexpected archived group')
    return found


def schedule_groups(plan):
    return {side: {group for entry in plan['forecast']['side'][side]['batches']
                   for group in entry['groups']} for side in SIDES}


def progress_summary(plan):
    try:
        found = {side: archived_groups(side) for side in SIDES}
    except BaseException as error:
        return {'verification_error': repr(error)}
    schedule = schedule_groups(plan)
    return {side: {'accepted_scheduled_groups': len(found[side] & schedule[side]),
                   'remaining_scheduled_groups': len(schedule[side]-found[side]),
                   'accepted_groups': sorted(found[side])} for side in SIDES}


def source_evidence(side, group, manifest, source_view):
    evidence = {}
    for stem in ('Rows', 'Body'):
        name = stem+str(group)+'.agda'
        entry = manifest['entries'][name]
        path = source_view/name
        require(path.is_file() and sha(path) == entry['sha256'], 'prepared source entry changed')
        evidence[name] = dict(entry)
    text = (source_view/('Rows'+str(group)+'.agda')).read_text()
    require(re.search(r'^module '+re.escape(PREFIX[side])+r'\.Rows'+str(group)+r' where$', text, re.M)
            and ('Global.G' in text)
            and not re.search(r'^import '+re.escape(PREFIX[side])+r'\.Rows\d+', text, re.M),
            'Rows source filename/module/G independence invariant differs')
    lines = [line.strip() for line in text.splitlines()
             if ('Global.G' in line or '{G =' in line or 'upperGoal' in line or 'lowerGoal' in line)]
    case = manifest['cases'][str(group)]
    return {'entries': evidence, 'case': case, 'G_parameter_lines': lines}


def body_interface(side, group):
    return PROOF[side]/'_build/2.9.0/agda/src'/Path(*PREFIX[side].split('.'))/('Body'+str(group)+'.agdai')


def row_interface(side, group):
    return PROOF[side]/'_build/2.9.0/agda/src'/Path(*PREFIX[side].split('.'))/('Rows'+str(group)+'.agdai')


def evict_body(side, group, source_view, manifest):
    file = body_interface(side, group)
    source = source_view/('Body'+str(group)+'.agda')
    require(file.is_file() and file.stat().st_nlink == 1, 'completed Body interface missing or linked')
    require(sha(source) == manifest['entries'][source.name]['sha256'], 'Body source hash changed')
    text = source.read_text()
    require(re.search(r'^module '+re.escape(PREFIX[side])+r'\.Body'+str(group)+r' where$', text, re.M)
            and re.search(r'^text : String$', text, re.M)
            and all(word not in text for word in ('Partial', 'Certified', 'Proven', 'postulate')),
            'Body source is not classified data-only')
    result = {'path': str(file), 'old_sha256': sha(file), 'bytes': file.stat().st_size,
              'source_sha256': sha(source), 'regenerable_string_data_only': True}
    file.unlink()
    require(not file.exists(), 'Body interface eviction failed')
    return result


def pack_row(side, group, source_evidence_record, *, seed=None):
    file = row_interface(side, group)
    require(file.is_file() and file.stat().st_nlink == 1, 'completed Rows interface missing or linked')
    old_stat = file.stat(); raw = file.read_bytes()
    require(len(raw) > 28 and raw[24:28] == bytes.fromhex('28b52ffd'), 'unexpected Agda frame')
    payload = zstd.decompress(raw[24:])
    packed = raw if seed is not None else raw[:24]+zstd.compress(payload, level=19)
    require(packed[:24] == raw[:24] and zstd.decompress(packed[24:]) == payload,
            'row payload-preserving compaction failed')
    if seed is None:
        records.atomic_bytes(file, packed, mode=old_stat.st_mode & 0o7777,
            atime_ns=old_stat.st_atime_ns, mtime_ns=old_stat.st_mtime_ns)
    append = records.append_stored(ROW_ZIP[side], 'Rows'+str(group)+'.agdai', packed)
    with zipfile.ZipFile(ROW_ZIP[side]) as archive:
        reread = archive.read('Rows'+str(group)+'.agdai')
    require(reread[:24] == raw[:24] and zstd.decompress(reread[24:]) == payload,
            'archived row payload differs')
    lineage = load_lineage(); key = side+'/Rows'+str(group)+'.agdai'
    entry = {'side': side, 'group': group, 'old_sha256': hashlib.sha256(raw).hexdigest(),
        'new_sha256': hashlib.sha256(packed).hexdigest(), 'old_bytes': len(raw),
        'new_bytes': len(packed), 'header_hex': raw[:24].hex(),
        'decoded_payload_sha256': hashlib.sha256(payload).hexdigest(),
        'mode': old_stat.st_mode & 0o7777, 'atime_ns': old_stat.st_atime_ns,
        'mtime_ns': old_stat.st_mtime_ns,
        'archive_member': append['member'], 'seeded_accepted_pilot': seed is not None}
    if seed is not None:
        require(seed['new_sha256'] == entry['new_sha256']
                and seed['decoded_payload_sha256'] == entry['decoded_payload_sha256']
                and seed['header_hex'] == entry['header_hex'], 'pilot payload lineage differs')
        entry['pilot_lineage'] = seed
    if key in lineage:
        require(lineage[key] == entry, 'row lineage collision')
    else:
        lineage[key] = entry
        write_lineage(lineage)
    records.commit_append(ROW_ZIP[side])
    file.unlink()
    require(not file.exists(), 'loose row frame deletion failed')
    return entry


def seed_pilots(plan, views):
    found = {side: archived_groups(side) for side in SIDES}
    for side in SIDES:
        pilot = plan['pilots'][side]
        manifest = read_json(plan['packages'][side+'-sources']['manifest'])
        for group in (100, 300):
            if group in found[side]:
                continue
            relative = f'_build/2.9.0/agda/src/{PREFIX[side].replace(".", "/")}/Rows{group}.agdai'
            source = Path(pilot['proof_root'])/relative
            require(source.is_file() and sha(source) == pilot['retained_row_interfaces'][relative],
                    'accepted pilot row interface changed')
            destination = row_interface(side, group)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            evidence = source_evidence(side, group, manifest, views[side+'-sources'])
            pack_row(side, group, evidence, seed=pilot['lineage'][relative])
    require(all({100, 300} <= archived_groups(side) for side in SIDES),
            'accepted pilot interfaces were not seeded')


def wrapper(run_id, ordinal, side, groups):
    root = OUT/'scratch'/run_id/(f'{ordinal:04d}-{side}')
    require(not root.exists(), 'wrapper root already exists without a recoverable transaction')
    path = root/'src/Tests/FullRowProduction6'/('Batch'+str(ordinal)+'.agda')
    path.parent.mkdir(parents=True)
    shutil.copy2(ROOT/'othello.agda-lib', root/'othello.agda-lib')
    module = 'Tests.FullRowProduction6.Batch'+str(ordinal)
    imports = ''.join('import '+PREFIX[side]+'.Rows'+str(group)+'\n' for group in groups)
    path.write_text(HEADER+'-- AI-assisted production wrapper; Result is not imported.\n'
                    +'module '+module+' where\n'+imports)
    records.fsync_file(path); records.fsync_file(root/'othello.agda-lib')
    records.fsync_directory(path.parent); records.fsync_directory(root)
    identity = source_identity(root)
    return root, path.relative_to(root).as_posix(), identity


def loose_evidence_paths(wrapper_root, label):
    return [(wrapper_root/'othello.agda-lib'),
            *sorted((wrapper_root/'src').rglob('*.agda')),
            OUT/'records'/(label+'.json'), OUT/'records'/(label+'.log')]


def relative_evidence(path):
    return Path(path).relative_to(OUT).as_posix()


def flush_cohort(plan, force=False):
    progress = read_json(PROGRESS)
    pending = progress.get('pending_record_batches', [])
    if not pending or (len(pending) < 2 and not force):
        return
    require(len(pending) <= 2, 'record cohort exceeded two batches')
    relatives = []
    for item in pending:
        relatives.extend(item['evidence_files'])
    cohort = len(progress.get('record_cohorts', []))
    member = f'cohort-{cohort:04d}.tar.zst'
    result = records.archive_cohort(RECORD_ZIP, member, OUT, relatives,
        {'batches': pending, 'cohort': cohort})
    require(allocated(RECORD_ZIP) <= plan['forecast']['storage']['future_closed_record_archive_cap_bytes'],
            'closed child records exceeded their frozen envelope')
    progress['record_cohorts'].append({'member': member, 'sha256': result['sha256'],
        'bytes': result['bytes'], 'decoded_tar_sha256': result['decoded_tar_sha256'],
        'batches': [item['label'] for item in pending], 'batch_records': pending})
    progress['pending_record_batches'] = []
    durable_json(PROGRESS, progress)
    records.commit_append(RECORD_ZIP)
    for relative in relatives:
        path = OUT/relative
        if path.exists():
            path.unlink()
    for item in pending:
        root = OUT/item['wrapper_root']
        if root.exists():
            shutil.rmtree(root)
    records.fsync_directory(OUT/'records')
    records.fsync_directory(OUT)
    component_storage(plan, reserve=4*MIB)


def archive_batch_evidence(plan, transaction, result):
    progress = read_json(PROGRESS)
    files = [relative_evidence(path) for path in loose_evidence_paths(
        OUT/transaction['wrapper_root'], transaction['label'])]
    require(all((OUT/path).is_file() for path in files), 'complete child evidence is required')
    if not any(item['label'] == transaction['label'] for item in progress['pending_record_batches']):
        progress['pending_record_batches'].append({'label': transaction['label'],
            'accepted': result['accepted'], 'side': transaction['side'],
            'groups': transaction['groups'], 'wrapper_root': transaction['wrapper_root'],
            'evidence_files': files})
    durable_json(PROGRESS, progress)
    if not result['accepted']:
        flush_cohort(plan, force=True)


def commit_accepted_batch(plan, transaction, views, manifests, result):
    side = transaction['side']; groups = transaction['groups']
    evicted, rows = [], []
    found = archived_groups(side)
    for group in groups:
        evidence = source_evidence(side, group, manifests[side], views[side+'-sources'])
        body = body_interface(side, group)
        if body.exists():
            evicted.append(evict_body(side, group, views[side+'-sources'], manifests[side]))
        if group not in found:
            rows.append(pack_row(side, group, evidence))
        else:
            rows.append(load_lineage()[side+'/Rows'+str(group)+'.agdai'])
    found = archived_groups(side)
    require(all(group in found for group in groups), 'accepted batch did not commit every row')
    progress = read_json(PROGRESS)
    if not any(item['label'] == transaction['label'] for item in progress['accepted_batches']):
        archive_batch_evidence(plan, transaction, result)
        progress = read_json(PROGRESS)
        progress['accepted_batches'].append({'label': transaction['label'], 'side': side,
            'groups': groups, 'tokens': transaction['tokens'],
            'record': {key: result[key] for key in ('accepted', 'exit_code', 'cpu_seconds',
                'wall_seconds', 'stop_reason', 'peak_rss_gib')},
            'data_only_interfaces_evicted': evicted,
            'row_interface_payload_lineage': [row['new_sha256'] for row in rows],
            'committed_utc': utc()})
    progress['last_committed_batch'] = transaction['label']
    progress['coverage'] = progress_summary(plan)
    durable_json(PROGRESS, progress)
    if TRANSACTION.exists():
        TRANSACTION.unlink()
        records.fsync_directory(TRANSACTION.parent)
    flush_cohort(plan)
    component_storage(plan, progress['coverage'], 4*MIB)


def recover_transaction(plan, views, manifests):
    if not TRANSACTION.exists():
        return
    transaction = read_json(TRANSACTION)
    record_path = OUT/'records'/(transaction['label']+'.json')
    require(record_path.is_file(), 'active batch has no terminal child record; preserve it and stop')
    result = read_json(record_path)
    if not result.get('accepted'):
        archive_batch_evidence(plan, transaction, result)
        raise ValueError('previous child batch failed; evidence retained and no retry authorized')
    # An accepted child may have been interrupted during post-check compaction.
    # Rows already present are verified; missing members must still have their
    # loose terminal interfaces, so no mathematical check is repeated.
    side = transaction['side']; found = archived_groups(side)
    for group in transaction['groups']:
        if group in found:
            body = body_interface(side, group)
            if body.exists():
                evict_body(side, group, views[side+'-sources'], manifests[side])
            continue
        require(row_interface(side, group).is_file(),
                'accepted child row is neither archived nor available loose')
    commit_accepted_batch(plan, transaction, views, manifests, result)


def sandbox(views):
    argv = ['/usr/bin/bwrap', '--ro-bind', '/', '/', '--bind', str(OUT), str(OUT),
        '--proc', '/proc', '--dev-bind', '/dev', '/dev', '--tmpfs', '/tmp', '--die-with-parent']
    for view in views.values():
        argv += ['--ro-bind', str(view), str(view)]
    return argv+['--']


def run_batch(plan, run_id, ordinal, side, entry, views, donors, manifests):
    groups = entry['groups']
    root, target, identity = wrapper(run_id, ordinal, side, groups)
    label = f'{run_id}-{ordinal:04d}-{side}-'+'-'.join(map(str, groups))
    source_records = {str(group): source_evidence(side, group, manifests[side],
        views[side+'-sources']) for group in groups}
    transaction = {'format': 'othello-full-row-active-batch-v1', 'created_utc': utc(),
        'run_id': run_id, 'ordinal': ordinal, 'label': label, 'side': side,
        'groups': groups, 'tokens': entry['tokens'],
        'wrapper_root': root.relative_to(OUT).as_posix(), 'target': target,
        'wrapper_source_identity': identity, 'source_records': source_records}
    durable_json(TRANSACTION, transaction)
    component_storage(plan, reserve=4*MIB)
    argv = sandbox(views)+[batch.full_map.AGDA, '--no-libraries', '-i', 'src']
    for donor in donors:
        argv += ['-i', str(donor/'src')]
    for name in ('upper-sources', 'lower-sources', 'upper-cache', 'lower-cache'):
        if name.endswith('-sources'):
            argv += ['-i', str(PROOF[name.split('-')[0]]/'src')]
        else:
            argv += ['-i', str(views[name]/'src')]
    argv += ['--safe', '--without-K', '--cubical-compatible', '--save-metas',
        '--profile=modules', target, '+RTS', '-M4500M', '-s', '-RTS']
    before = {side0: assembly6.interfaces(PROOF[side0]) for side0 in SIDES}
    result = run_job(label, argv, OUT/'records', root=root, timeout=CHILD_WALL,
        cpu_limit=CHILD_CPU, rss_limit_gib=11.4, log_limit_mib=.5,
        expected_source_sha256=identity['source_sha256'],
        metadata={'checker_binary_sha256': batch.full_map.AGDA_SHA,
            'frozen_archive_hashes': {name: package['archive_sha256']
                for name, package in plan['packages'].items()},
            'frozen_source_entry_hashes': source_records,
            'proof_root_build_locks': [str(PROOF[s]/'_build/.study6.lock') for s in SIDES],
            'proof_cache_before': before, 'same_existing_G': True,
            'new_owner_rows': sum(manifests[side]['cases'][str(g)]['rows'] for g in groups),
            'result_or_allparts_imported': False, 'mathematical_objective_complete': False})
    records.fsync_directory(OUT/'records')
    transaction['terminal_record_sha256'] = sha(OUT/'records'/(label+'.json'))
    durable_json(TRANSACTION, transaction)
    if not result['accepted']:
        archive_batch_evidence(plan, transaction, result)
        raise ValueError('child batch was not accepted; no automatic retry')
    log = (OUT/'records'/(label+'.log')).read_text(errors='replace')
    for group in groups:
        require('Checking '+PREFIX[side]+'.Rows'+str(group) in log,
                'accepted record lacks the requested Rows check')
    commit_accepted_batch(plan, transaction, views, manifests, result)


def validate_plan(plan):
    require(sha(FORECAST_FILE) == plan['forecast_sha256']
            and sha(CONTINUATION_FILE) == plan['continuation_sha256']
            and sha(HANDOFF) == plan['handoff_sha256'], 'frozen continuation evidence changed')
    require(all(sha(ROOT/'tools'/name) == pin for name, pin in plan['helper_sha256'].items()),
            'production helper changed after launch')
    require(sha(batch.full_map.AGDA) == batch.full_map.AGDA_SHA
            and batch.full_map.AGDA_SHA == plan['agda_sha256'], 'pinned checker changed')
    require(len(plan['p1_files']) == 23
            and all(sha(ROOT/name) == pin for name, pin in plan['p1_files'].items()), 'tagged P1 changed')
    forecast = plan['forecast']
    require(forecast['predicted_remaining_checker_cpu_seconds'] == 44504.60606535086,
            'frozen checker forecast changed')
    groups = schedule_groups(plan)
    require({side: len(groups[side]) for side in SIDES} == EXPECTED_COUNTS,
            'remaining group schedule differs')
    for side in SIDES:
        batches = forecast['side'][side]['batches']
        flat = [group for entry in batches for group in entry['groups']]
        manifest = read_json(plan['packages'][side+'-sources']['manifest'])
        cases = {int(group): case for group, case in manifest['cases'].items()}
        require(len(batches) == forecast['side'][side]['batch_count']
                and all(0 < len(entry['groups']) <= 2 and entry['tokens'] <= 450000 for entry in batches)
                and len(flat) == EXPECTED_COUNTS[side] == len(set(flat))
                and groups[side] == set(cases)-{100, 300}
                and groups[side].isdisjoint(OWNED[side])
                and all(entry['tokens'] == sum(cases[group]['tokens'] for group in entry['groups'])
                        for entry in batches)
                and forecast['side'][side]['remaining_tokens'] == sum(cases[group]['tokens'] for group in flat)
                and forecast['side'][side]['remaining_owner_rows'] == sum(cases[group]['rows'] for group in flat),
                'invalid, duplicated, or source-inconsistent frozen batch schedule')
    require(plan['authorization_sha256'] == sha(plan['authorization_path']),
            'applied cap authorization changed')


def complete_manifest(plan, beginning, ending):
    found = verify_archived_rows(plan); schedule = schedule_groups(plan)
    require(all(found[side] == schedule[side] | {100, 300} for side in SIDES),
            'full remaining row coverage is incomplete')
    lineage = load_lineage()
    require(len(lineage) == sum(EXPECTED_COUNTS.values())+4, 'row lineage cardinality differs')
    progress = read_json(PROGRESS)
    accepted = progress['accepted_batches']
    recorded = [item for cohort in progress['record_cohorts'] for item in cohort['batch_records']]
    require(not progress['pending_record_batches']
            and len(accepted) == 667 == len(recorded)
            and len({item['label'] for item in accepted}) == 667
            and {item['label'] for item in accepted} == {item['label'] for item in recorded},
            'complete row coverage lacks one-to-one terminal child evidence')
    with zipfile.ZipFile(RECORD_ZIP) as archive:
        require(set(archive.namelist()) == {entry['member'] for entry in progress['record_cohorts']},
                'terminal child record archive inventory differs')
        for entry in progress['record_cohorts']:
            blob = archive.read(entry['member'])
            require(hashlib.sha256(blob).hexdigest() == entry['sha256'],
                    'terminal child record cohort hash differs')
            records.verify_cohort_blob(blob)
    require(all(not records.journal_path(path).exists()
                for path in [*ROW_ZIP.values(), RECORD_ZIP]), 'unresolved ZIP append journal remains')
    manifest = {'format': 'othello-full-row-production-cache-v1', 'finished_utc': utc(),
        'remaining_rows_sources_safely_checked': True,
        'checked_remaining_groups': {side: sorted(schedule[side]) for side in SIDES},
        'seeded_accepted_pilot_groups': {side: [100, 300] for side in SIDES},
        'row_archives': {side: {'path': str(ROW_ZIP[side]), 'sha256': sha(ROW_ZIP[side]),
            'bytes': ROW_ZIP[side].stat().st_size, 'member_count': len(zip_inventory(side)),
            'member_inventory_sha256': hashlib.sha256(json.dumps(zip_inventory(side),
                sort_keys=True, separators=(',', ':')).encode()).hexdigest()} for side in SIDES},
        'lineage_path': str(LINEAGE), 'lineage_sha256': sha(LINEAGE),
        'source_and_cache_views_beginning': beginning,
        'source_and_cache_views_end': ending,
        'p1_files': plan['p1_files'], 'donor_beginning': plan['donor_beginning'],
        'result_or_allparts_checked': False, 'Problem2_checked': False,
        'mathematical_objective_complete': False,
        'next_required_stage': 'final checker must mount the closed row archives and check Result.initial6x6 separately'}
    atomic_json(OUT/'complete-row-cache-manifest.json', manifest)
    component_storage(plan, reserve=4*MIB)
    return manifest


def worker(run_id):
    previous_term = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt()))
    plan = read_json(OUT/'plan.json'); validate_plan(plan)
    require(run_id == plan['run']['run_id'], 'worker run id differs from active run')
    group = resources(plan)
    donors = {Path(path): tuple(pins) for path, pins in plan['donors'].items()}
    packages = plan['packages']; manifests = {side: read_json(packages[side+'-sources']['manifest']) for side in SIDES}
    processes, views, beginning, cleanup = [], {}, {}, []
    failure = None; ending = None; complete = None
    with contextlib.ExitStack() as stack:
        for donor in donors:
            lock = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        donor_beginning = batch.donor_snapshot(donors)
        require(donor_beginning == plan['donor_beginning'], 'donor snapshot changed before production')
        for side in SIDES:
            PROOF[side].mkdir(parents=True, exist_ok=True)
            if not (PROOF[side]/'othello.agda-lib').exists():
                shutil.copy2(ROOT/'othello.agda-lib', PROOF[side]/'othello.agda-lib')
            require(sha(PROOF[side]/'othello.agda-lib') == plan['agda_lib_sha256'],
                    'proof-root Agda library file changed')
            stack.enter_context(build_lock(PROOF[side]))
        try:
            fs = Path(plan['filesystem_binary'])
            require(sha(fs) == plan['filesystem_binary_sha256'], 'archive filesystem helper changed')
            for name, package in packages.items():
                archive = Path(package['archive'])
                require(sha(archive) == package['archive_sha256']
                        and sha(package['manifest']) == package['manifest_sha256'],
                        'immutable package changed')
                lock = stack.enter_context(archive.open('rb'))
                fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                if name.endswith('-sources'):
                    side = name.split('-')[0]
                    view = PROOF[side]/'src'/Path(*PREFIX[side].split('.'))
                else:
                    view = OUT/name
                view.mkdir(parents=True, exist_ok=True)
                log = stack.enter_context((OUT/(name+'-filesystem.log')).open('wb'))
                process = subprocess.Popen([str(fs), str(archive), str(view)], stdout=log,
                    stderr=subprocess.STDOUT)
                processes.append((view, process))
                started = time.monotonic()
                while not os.path.ismount(view):
                    require(process.poll() is None and time.monotonic()-started < 10,
                            'archive view did not mount')
                    time.sleep(.05)
                beginning[name] = {**verify_view(view, package['manifest']),
                    'archive_sha256': package['archive_sha256'],
                    'manifest_sha256': package['manifest_sha256'],
                    'source_sha256': package.get('source_sha256'),
                    'interface_pool_sha256': package.get('interface_pool_sha256')}
                views[name] = view
            atomic_json(OUT/('input-snapshots-'+run_id+'-begin.json'), beginning)
            recover_append_journals()
            seed_pilots(plan, views)
            recover_transaction(plan, views, manifests)
            flush_cohort(plan)
            with watched(plan, group):
                ordinal = 0
                found = verify_archived_rows(plan)
                for side in SIDES:
                    for entry in plan['forecast']['side'][side]['batches']:
                        ordinal += 1
                        remaining = [g for g in entry['groups'] if g not in found[side]]
                        if not remaining:
                            continue
                        require(remaining == entry['groups'],
                                'partially committed frozen batch requires transaction recovery, not resubmission')
                        run_batch(plan, run_id, ordinal, side, entry, views, donors, manifests)
                        found[side].update(entry['groups'])
            flush_cohort(plan, force=True)
            ending = {name: {**verify_view(views[name], package['manifest']),
                'archive_sha256': package['archive_sha256'],
                'manifest_sha256': package['manifest_sha256'],
                'source_sha256': package.get('source_sha256'),
                'interface_pool_sha256': package.get('interface_pool_sha256')}
                      for name, package in packages.items()}
            require(ending == beginning, 'source or dataset view changed')
            require(batch.donor_snapshot(donors) == donor_beginning, 'donor changed during production')
            require(all(sha(ROOT/name) == pin for name, pin in plan['p1_files'].items()),
                    'tagged P1 changed during production')
            complete = complete_manifest(plan, beginning, ending)
        except BaseException as error:
            failure = repr(error)
            try:
                flush_cohort(plan, force=True)
            except BaseException as archive_error:
                failure += '; evidence archive error='+repr(archive_error)
        finally:
            for view, process in reversed(processes):
                if os.path.ismount(view):
                    subprocess.run(['/usr/bin/fusermount3', '-u', str(view)], capture_output=True, timeout=8)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate(); process.wait(timeout=5)
                cleanup.append({'view': str(view), 'unmounted': not os.path.ismount(view),
                                'exit_code': process.returncode})
            atomic_json(OUT/('view-cleanup-'+run_id+'.json'), cleanup)
    accepted = failure is None and complete is not None and all(
        item['unmounted'] and item['exit_code'] == 0 for item in cleanup)
    report = {'format': 'othello-full-row-production-run-v1', 'run_id': run_id,
        'finished_utc': utc(), 'accepted': accepted, 'failure': failure,
        'coverage': progress_summary(plan), 'view_cleanup': cleanup,
        'complete_row_cache_manifest': None if complete is None else str(OUT/'complete-row-cache-manifest.json'),
        'full_remaining_row_coverage_checked': complete is not None,
        'result_or_allparts_checked': False, 'Problem2_checked': False,
        'mathematical_objective_complete': False,
        'manual_ledger_finish_required_from_outer_record': True}
    atomic_json(OUT/('report-'+run_id+'.json'), report)
    atomic_json(OUT/'report.json', report)
    signal.signal(signal.SIGTERM, previous_term)
    require(accepted, 'production stopped; preserve accepted progress and terminal evidence')


def supervise(run_id):
    job = read_json(OUT/('job-'+run_id+'.json'))
    result = run_job(run_id, ['/usr/bin/python3', '-B', str(Path(__file__).resolve()),
        'worker', run_id], OUT/'outer-records', root=CONTROL,
        timeout=job['outer_wall_limit_seconds'], cpu_limit=job['outer_cpu_cap_seconds'],
        rss_limit_gib=11.7, log_limit_mib=.5,
        reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'],
        metadata={'manual_ledger_finish_required': True,
                  'full_row_production_run_id': run_id})
    return 0 if result['accepted'] else 1


def new_progress():
    return {'format': 'othello-full-row-production-progress-v1', 'created_utc': utc(),
        'accepted_batches': [], 'pending_record_batches': [], 'record_cohorts': [],
        'last_committed_batch': None, 'coverage': {}}


def freeze_plan(auth_path, auth):
    forecast = read_json(FORECAST_FILE); continuation = read_json(CONTINUATION_FILE)
    require(not forecast['production_go'] and not continuation['production_go']
            and not forecast['mathematical_objective_complete'], 'forecast state differs')
    prior, census_paths = census_prior()
    private_bytes = allocated(PRIVATE_CORE)
    storage = forecast['storage']
    require(prior == storage['allocated_study_bytes'],
            'fresh physical census differs from the refreshed frozen baseline')
    require(storage['private_core_package_in_baseline'] is True
            and private_bytes == storage['private_core_realized_bytes']
            and storage['private_core_original_allowance_bytes']-private_bytes
                == storage['private_core_source_package_allowance_bytes'],
            'private core realized/remaining baseline accounting differs')
    packages = {}
    for side in SIDES:
        cache = read_json(ROOT/('results/text-'+side+'-cache-current6-20261018.json'))
        source = read_json(ROOT/('results/complete-'+side+'-row-sources-index6-20261018.json'))
        require(source['accepted'], 'prepared source package is not accepted')
        packages[side+'-cache'] = {'archive': cache['archive'],
            'archive_sha256': cache['archive_sha256'], 'manifest': cache['manifest'],
            'manifest_sha256': sha(cache['manifest']), 'source_sha256': cache['source_sha256'],
            'interface_pool_sha256': cache['interface_pool_sha256']}
        packages[side+'-sources'] = {'archive': source['archive'],
            'archive_sha256': source['archive_sha256'], 'manifest': source['manifest'],
            'manifest_sha256': sha(source['manifest'])}
    fs = Path(packages['upper-cache']['archive']).parent/'archive-fs'
    if not fs.exists():
        fs = Path(read_json(ROOT/'results/text-upper-cache-current6-20261018.json')['filesystem_binary'])
    require(fs == Path(read_json(ROOT/'results/text-lower-cache-current6-20261018.json')['filesystem_binary']),
            'cache packages require distinct filesystem helpers')
    donors = read_json(BASE/'packed-lower-cache6-20261018/plan.json')['donors']
    donor_paths = {Path(path): tuple(pins) for path, pins in donors.items()}
    require(len(donor_paths) == 68, 'expected 68 core donor roots')
    donor_beginning = batch.donor_snapshot(donor_paths)
    handoff = read_json(HANDOFF)
    require(len(handoff['p1_files']) == 23, 'canonical handoff must pin 23 P1 files')
    pilots = {}
    for side, root in continuation['accepted_new_row_proof_roots'].items():
        closure = read_json(Path(root).parent/'closure.json')
        require(closure['accepted'] and closure['row_interface_recompression_replay_accepted']
                and sorted(closure['retained_row_interfaces']) == sorted(
                    f'_build/2.9.0/agda/src/{PREFIX[side].replace(".", "/")}/Rows{group}.agdai'
                    for group in (100, 300)), 'accepted pilot closure differs')
        lineage_path = Path(closure['row_interface_payload_lineage'])
        pilots[side] = {'proof_root': root, 'closure': str(Path(root).parent/'closure.json'),
            'closure_sha256': sha(Path(root).parent/'closure.json'),
            'retained_row_interfaces': closure['retained_row_interfaces'],
            'lineage_path': str(lineage_path), 'lineage_sha256': sha(lineage_path),
            'lineage': read_json(lineage_path)}
    run_id = 'production-0001'
    plan = {'format': 'othello-full-row-production-plan-v1', 'created_utc': utc(),
        'forecast': forecast, 'forecast_sha256': sha(FORECAST_FILE),
        'continuation_sha256': sha(CONTINUATION_FILE), 'handoff_sha256': sha(HANDOFF),
        'authorization_path': str(auth_path), 'authorization_sha256': sha(auth_path),
        'authorization': auth, 'packages': packages, 'pilots': pilots,
        'filesystem_binary': str(fs), 'filesystem_binary_sha256': sha(fs),
        'donors': donors, 'donor_beginning': donor_beginning, 'p1_files': handoff['p1_files'],
        'agda': batch.full_map.AGDA, 'agda_sha256': batch.full_map.AGDA_SHA,
        'agda_lib_sha256': sha(ROOT/'othello.agda-lib'),
        'helper_sha256': {name: sha(ROOT/'tools'/name) for name in HELPERS},
        'prior_allocated_study_bytes': prior,
        'forecast_prior_allocated_study_bytes': forecast['storage']['allocated_study_bytes'],
        'realized_private_core_package_bytes': private_bytes,
        'private_core_remaining_allowance_bytes': storage['private_core_source_package_allowance_bytes'],
        'census_paths': [str(path) for path in sorted(census_paths)],
        'run': {'run_id': run_id, 'reservation_cpu_seconds': auth['reservation_cpu_seconds'],
            'outer_cpu_cap_seconds': auth['outer_cpu_cap_seconds']}}
    return plan


def dispatch(action, auth_path):
    auth_path, auth = authorization(auth_path, action)
    batch.authorized()
    require(not common.disjoint_checkers(), 'another Othello checker is active')
    require(not subprocess.check_output(['systemctl', '--user', 'list-units',
        '--state=activating,running', '--type=service', '--no-legend', '--plain',
        'othello*'], text=True).strip(), 'an Othello service is already active')
    ledger = Ledger(LEDGER_FILE)
    state = read_json(LEDGER_FILE); summary = Ledger.summary(state)
    require(summary['total_cpu_seconds'] == 172800 and not summary['outstanding'],
            'ledger total or outstanding reservation differs')
    require(summary['categories']['kernel']['available_cpu_seconds'] >= auth['reservation_cpu_seconds'],
            'kernel category cannot cover the authorized reservation')
    if action == 'launch':
        require(not OUT.exists(), 'production output already exists; use resume with a new authorization')
        plan = freeze_plan(auth_path, auth)
        OUT.mkdir(); CONTROL.mkdir(); (OUT/'records').mkdir(); (OUT/'outer-records').mkdir()
        shutil.copy2(Path(__file__), CONTROL/'worker.py')
        durable_json(OUT/'plan.json', plan); durable_json(PROGRESS, new_progress())
    else:
        require(OUT.is_dir(), 'production output is absent')
        plan = read_json(OUT/'plan.json'); validate_plan(plan)
        require(not read_json(OUT/'report.json').get('accepted', False),
                'production is already complete') if (OUT/'report.json').exists() else None
        require(not TRANSACTION.exists() or (OUT/'records'/(read_json(TRANSACTION)['label']+'.json')).exists(),
                'incomplete active child has no terminal record; manual diagnosis required')
        run_number = 1+max([int(path.stem.split('-')[-1]) for path in OUT.glob('job-production-*.json')] or [0])
        run_id = f'production-{run_number:04d}'
        plan['authorization_path'] = str(auth_path); plan['authorization_sha256'] = sha(auth_path)
        plan['authorization'] = auth
        plan['run'] = {'run_id': run_id, 'reservation_cpu_seconds': auth['reservation_cpu_seconds'],
            'outer_cpu_cap_seconds': auth['outer_cpu_cap_seconds']}
        durable_json(OUT/'plan.json', plan)
    run_id = plan['run']['run_id']
    control_source = source_identity(CONTROL)
    reservation = ledger.reserve('kernel', auth['reservation_cpu_seconds'], run_id)
    unit = 'othello6-'+OUT.name+'-'+run_id+'.service'
    job = {'format': 'othello-full-row-production-job-v1', 'created_utc': utc(),
        'action': action, 'run_id': run_id, 'reservation': reservation,
        'outer_cpu_cap_seconds': auth['outer_cpu_cap_seconds'],
        'outer_wall_limit_seconds': RUNTIME_MAX-30, 'control_source': control_source,
        'unit': unit, 'manual_ledger_finish_required': True}
    durable_json(OUT/('job-'+run_id+'.json'), job)
    args = ['systemd-run', '--user', '--no-block', '--unit='+unit,
        '--property=MemoryMax=12G', '--property=MemorySwapMax=0', '--property=LimitCORE=0',
        '--property=CPUQuota=100%', '--property=TasksMax=128', '--property=KillMode=control-group',
        '--property=RuntimeMaxSec='+str(RUNTIME_MAX), '--property=WorkingDirectory='+str(CONTROL),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'supervise', run_id]
    done = subprocess.run(args, capture_output=True, text=True)
    atomic_json(OUT/('dispatch-'+run_id+'.json'), {'argv': args, 'exit_code': done.returncode,
        'stdout': done.stdout, 'stderr': done.stderr})
    require(done.returncode == 0, 'systemd dispatch failed; reservation remains outstanding')
    print(json.dumps({'unit': unit, 'run_id': run_id, 'reservation': reservation,
        'manual_finish_record': str(OUT/'outer-records'/(run_id+'.json'))}, indent=2))


def main():
    require(len(sys.argv) >= 2, 'action required')
    action = sys.argv[1]
    if action in ('launch', 'resume'):
        require(len(sys.argv) == 3, action+' requires AUTHORIZATION.json')
        dispatch(action, Path(sys.argv[2]))
        return 0
    if action in ('worker', 'supervise'):
        require(len(sys.argv) == 3, action+' requires RUN_ID')
        if action == 'worker':
            worker(sys.argv[2]); return 0
        return supervise(sys.argv[2])
    raise ValueError('action must be launch, resume, worker, or supervise')


if __name__ == '__main__':
    raise SystemExit(main())
