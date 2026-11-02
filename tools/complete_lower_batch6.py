"""Fresh two-group LOWER batch for cost and retained-interface-size validation.

AI-assisted harness. Certificate sources remain untrusted until their own safe
Agda checks succeed. Loading all Body modules proves no additional game rows.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile
from compression import zstd

import assembly6
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT = BASE/'complete-lower-batch6-20261018'
CHECK = OUT/'check'
UNIT = 'othello6-'+OUT.name+'.service'
RESERVE, OUTER, ALLOWANCE = 300, 270, 10
CAP = 16*2**20
GROUPS = (100, 300)
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
previous.OUT = OUT
common.OUT, common.HARD_GIB, common.RESERVATION_CPU = OUT, 6, RESERVE


def sha(path):
    return common.sha(Path(path))


def storage(plan, reserve=0):
    own = int(subprocess.check_output(['du', '-s', '-x', '-B1', str(OUT)], text=True).split()[0])
    used = plan['prior_allocated_study_bytes']+own
    assert own+reserve <= CAP and used+reserve < 12*2**30
    free = shutil.disk_usage(ROOT).free
    assert free-2**20 >= 80*2**30 and shutil.disk_usage(OUT).free-reserve >= 80*2**30
    return dict(checked_utc=utc(), allocated_study_bytes=used, own_output_bytes=own,
                root_free_bytes=free, virtual_source_and_cache_views_excluded=True)


def wrapper(name, imports):
    path = CHECK/'src/Tests'/('CompleteLowerBatch'+name+'6.agda')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER+'-- AI-assisted bounded validation; no full theorem claimed.\n'
                    +'module Tests.CompleteLowerBatch'+name+'6 where\n'+imports)
    return path.relative_to(CHECK).as_posix()


def worker():
    batch.authorized()
    plan = json.loads((OUT/'plan.json').read_text())
    assert all(sha(ROOT/'tools'/name) == pin for name, pin in plan['helper_sha256'].items())
    assert sha(batch.full_map.AGDA) == batch.full_map.AGDA_SHA
    common.storage = lambda reserve=0: storage(plan, reserve)
    expected = {Path(k): tuple(v) for k, v in plan['donors'].items()}
    processes, views, before_views, phases = [], {}, {}, {}
    failure = None
    proof_before = proof_after = None
    removed = []
    with contextlib.ExitStack() as stack:
        for donor in expected:
            lock = stack.enter_context((donor/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before_donors = batch.donor_snapshot(expected)
        stack.enter_context(common.watched())
        try:
            fs = Path(plan['filesystem_binary'])
            assert sha(fs) == plan['filesystem_binary_sha256']
            for name, package in plan['packages'].items():
                archive = Path(package['archive'])
                assert sha(archive) == package['archive_sha256']
                lock = stack.enter_context(archive.open('rb'))
                fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
                if name.endswith('-sources'):
                    side = name.split('-')[0].title()
                    proof = OUT/(name.split('-')[0]+'-proof')
                    proof.mkdir()
                    shutil.copy2(ROOT/'othello.agda-lib', proof/'othello.agda-lib')
                    stack.enter_context(build_lock(proof))
                    view = proof/'src/Tests'/('Complete'+side+'Rows6')
                else:
                    view = OUT/name
                view.mkdir(parents=True)
                log = stack.enter_context((OUT/(name+'-filesystem.log')).open('wb'))
                process = subprocess.Popen([str(fs), str(archive), str(view)], stdout=log, stderr=subprocess.STDOUT)
                processes.append((view, process))
                start = time.monotonic()
                while not os.path.ismount(view):
                    assert process.poll() is None and time.monotonic()-start < 10
                    time.sleep(.05)
                before_views[name] = verify_view(view, package['manifest'])
                views[name] = view
            atomic_json(OUT/'views-before.json', before_views)
            CHECK.mkdir(parents=True)
            shutil.copy2(ROOT/'othello.agda-lib', CHECK/'othello.agda-lib')
            targets = {}
            targets['batch'] = wrapper('Batch', ''.join(
                'import Tests.CompleteLowerRows6.Rows'+str(g)+'\n' for g in GROUPS))
            targets['replay'] = wrapper('Replay', ''.join(
                'import Tests.CompleteLowerRows6.Rows'+str(g)+'\n' for g in GROUPS))
            targets['packed-replay'] = wrapper('PackedReplay', ''.join(
                'import Tests.CompleteLowerRows6.Rows'+str(g)+'\n' for g in GROUPS))
            identity = source_identity(CHECK)
            atomic_json(OUT/'emission.json', dict(source=identity, targets=targets))
            stack.enter_context(build_lock(CHECK))
            args = previous.sandbox()[:-1]
            for view, _ in processes:
                args += ['--ro-bind', str(view), str(view)]
            args += ['--', batch.full_map.AGDA, '--no-libraries', '-i', 'src']
            for donor in expected:
                args += ['-i', str(donor/'src')]
            for side in ['upper', 'lower']:
                args += ['-i', str(views[side+'-cache']/'src'), '-i', str(OUT/(side+'-proof')/'src')]
            flags = ['--safe', '--without-K', '--cubical-compatible', '--save-metas', '--profile=modules']
            fields = ['accepted', 'exit_code', 'cpu_seconds', 'wall_seconds', 'stop_reason', 'peak_rss_gib']
            proof = OUT/'lower-proof'
            assert not assembly6.interfaces(proof)
            forecast = plan['forecast']
            atomic_json(OUT/'forecast-freeze-pin.json', dict(created_utc=utc(), plan_sha256=sha(OUT/'plan.json')))
            for label, cap, wall in [('batch', 160, 400), ('replay', 45, 150),
                                     ('packed-replay', 45, 150)]:
                if label == 'replay':
                    proof_before = assembly6.interfaces(proof)
                    for g in GROUPS:
                        relative = '_build/2.9.0/agda/src/Tests/CompleteLowerRows6/Body'+str(g)+'.agdai'
                        file = proof/relative
                        source = views['lower-sources']/('Body'+str(g)+'.agda')
                        manifest = json.loads(Path(plan['packages']['lower-sources']['manifest']).read_text())
                        assert sha(source) == manifest['entries'][source.name]['sha256']
                        text = source.read_text()
                        assert 'text : String' in text and all(word not in text for word in ['Partial', 'Certified', 'Proven', 'postulate'])
                        assert file.is_file() and file.stat().st_nlink == 1
                        removed.append(dict(path=str(file), sha256=sha(file), bytes=file.stat().st_size,
                                            regenerable_string_data_only=True, source_sha256=sha(source)))
                        file.unlink()
                    atomic_json(OUT/'evicted-data-interfaces.json', removed)
                    proof_after = assembly6.interfaces(proof)
                    assert len(proof_after) == len(GROUPS)
                    assert all(proof_before[name] == pin for name, pin in proof_after.items())
                    atomic_json(OUT/'retained-row-interfaces.json', proof_after)
                elif label == 'packed-replay':
                    lineage = {}
                    with zipfile.ZipFile(OUT/'original-row-interface-frames.zip','x') as saved:
                        for name, pin in proof_after.items():
                            file = proof/name
                            raw = file.read_bytes()
                            assert hashlib.sha256(raw).hexdigest() == pin
                            saved.writestr(name,raw,compress_type=zipfile.ZIP_STORED)
                            assert raw[24:28] == bytes.fromhex('28b52ffd')
                            payload = zstd.decompress(raw[24:])
                            packed = raw[:24]+zstd.compress(payload,level=19)
                            assert packed[:24] == raw[:24] and zstd.decompress(packed[24:]) == payload
                            old_stat = file.stat()
                            temporary = file.with_suffix('.repacked')
                            temporary.write_bytes(packed)
                            os.chmod(temporary,old_stat.st_mode & 0o7777)
                            os.utime(temporary,ns=(old_stat.st_atime_ns,old_stat.st_mtime_ns))
                            os.replace(temporary,file)
                            lineage[name] = dict(old_sha256=pin,new_sha256=sha(file),
                                decoded_payload_sha256=hashlib.sha256(payload).hexdigest(),
                                header_hex=raw[:24].hex(),old_bytes=len(raw),new_bytes=len(packed))
                    with (OUT/'original-row-interface-frames.zip').open('rb') as stream:
                        os.fsync(stream.fileno())
                    with zipfile.ZipFile(OUT/'original-row-interface-frames.zip') as saved:
                        assert all(hashlib.sha256(saved.read(name)).hexdigest()==e['old_sha256']
                                   for name,e in lineage.items())
                    atomic_json(OUT/'row-interface-payload-lineage.json',lineage)
                    proof_after = assembly6.interfaces(proof)
                    assert proof_after == {name:e['new_sha256'] for name,e in lineage.items()}
                    atomic_json(OUT/'retained-row-interfaces.json',proof_after)
                common.storage(8*2**20)
                invocation = args+flags+([] if label == 'batch' else ['--no-write-interfaces'])
                heap = '-M4500M'
                result = run_job(label, invocation+[targets[label], '+RTS', heap, '-s', '-RTS'],
                    OUT/'records', root=CHECK, timeout=wall, cpu_limit=cap, rss_limit_gib=5.6,
                    log_limit_mib=3, expected_source_sha256=identity['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,
                        frozen_package_archive_hashes={k:p['archive_sha256'] for k,p in plan['packages'].items()},
                        lower_same_existing_G=True, new_owner_rows=20000 if label=='batch' else 0,
                        source_layout_only=label=='layout', proof_root_build_lock=str(proof/'_build/.study6.lock'),
                        mathematical_objective_complete=False))
                phases[label] = {key:result[key] for key in fields}
                atomic_json(OUT/'phase-summary.json', phases)
                assert result['accepted'], 'Preflight incomplete: '+label
                if label == 'batch':
                    actual = result['cpu_seconds']
                    error = 100*abs(forecast['predicted_batch_cpu_seconds']-actual)/actual
                    atomic_json(OUT/'forecast-validation.json', dict(actual_cpu_seconds=actual,
                        relative_error_percent=error, component_gate_passed=error<=30,
                        threshold_percent=30, production_go=False))
                    assert error <= 30, 'Frozen batched forecast gate failed'
                elif label in ['replay','packed-replay']:
                    log = (OUT/('records/'+label+'.log')).read_text()
                    assert all('Checking Tests.CompleteLowerRows6.Rows'+str(g) not in log for g in GROUPS)
                    assert assembly6.interfaces(proof) == proof_after
            assert source_identity(CHECK) == identity
            assert all(verify_view(views[name], p['manifest']) == before_views[name]
                       for name, p in plan['packages'].items())
        except BaseException as error:
            failure = repr(error)
        finally:
            cleanup = []
            for view, process in reversed(processes):
                if os.path.ismount(view):
                    subprocess.run(['/usr/bin/fusermount3', '-u', str(view)], capture_output=True, timeout=8)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
                cleanup.append(dict(view=str(view), unmounted=not os.path.ismount(view), exit=process.returncode))
            atomic_json(OUT/'view-cleanup.json', cleanup)
        intact = batch.donor_snapshot(expected) == before_donors
        p1 = all(sha(ROOT/name) == pin for name, pin in plan['p1_files'].items())
        accepted = failure is None and len(phases)==3 and all(p['accepted'] for p in phases.values())
        accepted = accepted and intact and p1 and all(c['unmounted'] and c['exit']==0 for c in cleanup)
        atomic_json(OUT/'report.json', dict(finished_utc=utc(), accepted=accepted, failure=failure,
            phases=phases, donor_sources_and_interfaces_unchanged=intact, p1_unchanged=p1,
            lower_new_owned_groups=list(GROUPS) if phases.get('batch',{}).get('accepted') else [],
            new_lower_owner_rows=20000 if phases.get('batch',{}).get('accepted') else 0,
            retained_row_interfaces=proof_after, data_only_interfaces_evicted=removed,
            row_interface_recompression_replay_accepted=phases.get('packed-replay',{}).get('accepted',False),
            full_body_layout_previously_validated_in=str(BASE/'complete-row-preflight6-20261018/closure.json'),
            full_row_coverage_proved=False, production_go=False, mathematical_objective_complete=False))
        assert accepted, 'Preflight incomplete; preserve all receipts and successful row proofs'


def supervise():
    job = json.loads((OUT/'job.json').read_text())
    result = run_job(OUT.name, ['/usr/bin/python3', '-B', str(Path(__file__).resolve()), 'worker'],
        OUT/'records', root=OUT/'control', timeout=900, cpu_limit=OUTER, rss_limit_gib=5.8,
        log_limit_mib=3, reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized()
    assert not OUT.exists() and not common.disjoint_checkers()
    assert sha(batch.full_map.AGDA) == batch.full_map.AGDA_SHA
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior = json.loads((BASE/'archived-cache-duplicates6-20261018/closure.json').read_text())
    assert prior['accepted'] and prior['combined_scope_cpu_seconds']+RESERVE+ALLOWANCE <= 6000
    legacy = common.storage(0)
    patterns = previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    paths = {p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry = json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths |= {Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used = legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+CAP < 12*2**30 and shutil.disk_usage(ROOT).free-2**20 >= 80*2**30
    donors = json.loads((BASE/'packed-lower-cache6-20261018/plan.json').read_text())['donors']
    packages = {}
    for side in ['upper', 'lower']:
        packages[side+'-cache'] = json.loads((ROOT/('results/text-'+side+'-cache-current6-20261018.json')).read_text())
        closed = json.loads((ROOT/('results/complete-'+side+'-row-sources-index6-20261018.json')).read_text())
        assert closed['accepted']
        packages[side+'-sources'] = dict(archive=closed['archive'],archive_sha256=closed['archive_sha256'],manifest=closed['manifest'])
    meta = json.loads(Path(packages['lower-sources']['manifest']).read_text())
    old = json.loads((BASE/'text-upper-holdout6-20261018/forecast-freeze.json').read_text())
    warm = 8.5838
    lower_offset=24.232649-old['cpu_per_token']*54145
    predicted = warm+len(GROUPS)*(lower_offset-warm)+old['cpu_per_token']*sum(meta['cases'][str(g)]['tokens'] for g in GROUPS)
    forecast = dict(created_utc=utc(), model='previous independently validated LOWER token slope/offset, shared measured warm import8.5838CPU',
        cpu_per_token=old['cpu_per_token'],lower_offset_cpu_seconds=lower_offset,
        selected_untouched_groups=list(GROUPS), predicted_batch_cpu_seconds=predicted,
        accepted_relative_error_percent=30, full_scope_cpu_budget_unchanged=True)
    OUT.mkdir(); (OUT/'control').mkdir()
    shutil.copy2(Path(__file__), OUT/'control/worker.py')
    history = json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    fs = Path(packages['upper-cache']['filesystem_binary'])
    helpers = ['complete_lower_batch6.py','assembly6.py','big_rows_probe6.py','citation_diagnostic6.py',
        'completion_batch6.py','run_job.py','provenance.py','study6.py','study_archive6.py']
    plan = dict(created_utc=utc(), control_source=source_identity(OUT/'control'), donors=donors,
        packages=packages, filesystem_binary=str(fs), filesystem_binary_sha256=sha(fs),
        helper_sha256={name:sha(ROOT/'tools'/name) for name in helpers},p1_files=history['p1_files'],
        prior_allocated_study_bytes=used, previous_combined_scope_cpu_seconds=prior['combined_scope_cpu_seconds'],
        new_controller_allowance_seconds=ALLOWANCE, scope_cpu_cap=6000, reservation=RESERVE,
        outer_cpu_cap=OUTER, hard_memory_gib=6, swap_bytes=0, core_bytes=0, phase_caps=[160,45,45],
        own_output_cap_bytes=CAP, retained_study_cap_gib=12, root_free_floor_gib=80,
        forecast=forecast, no_native_solver_runs=True, production_go=False, mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger = Ledger(ROOT/'results/study6-ledger.json')
    assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance = ledger.withhold('assembly',ALLOWANCE,'Fresh LOWER two-group cost/interface-size validation on prepared full sources, preserving all prior inline6000 charges, existing full-body memory measurement and unchanged safeguards')
    reservation = ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args = ['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=6G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=128','--property=KillMode=control-group','--property=RuntimeMaxSec=930',
        '--property=WorkingDirectory='+str(OUT/'control'),'--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done = subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr))
    assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,forecast=forecast,
        combined_reserved_scope_cpu_seconds=prior['combined_scope_cpu_seconds']+RESERVE+ALLOWANCE)))


if __name__ == '__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch': launch()
    elif sys.argv[1]=='worker': worker()
    else: raise SystemExit(supervise())
