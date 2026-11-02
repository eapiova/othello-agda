"""Bounded append recovery of a closed interrupted untrusted source archive."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
BOUND='lower'
OLD=BASE/'complete-lower-row-sources6-20261018'
OUT=BASE/'complete-lower-row-sources-recovery6-20261018';UNIT='othello6-'+OUT.name+'.service'
RESERVE=500;OUTER=460;ALLOWANCE=10
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=3;common.RESERVATION_CPU=RESERVE


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    def storage(reserve=0):
        own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
        archive=Path(plan['resume_archive'])
        delta=archive.stat().st_blocks*512-plan['initial_archive_allocated_bytes']
        assert delta>=0 and own+delta+reserve<=48*2**20
        assert archive.stat().st_size+8*2**20<=128*2**20
        assert plan['prior_allocated_study_bytes']+own+delta+reserve<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(checked_utc=utc(),allocated_study_bytes=plan['prior_allocated_study_bytes']+own+delta,
            own_output_bytes=own,shared_archive_growth_bytes=delta,root_free_bytes=shutil.disk_usage(ROOT).free,
            virtual_view_not_double_counted=True,existing_archive_counted_once_in_prior_snapshot=True)
    common.storage=storage;process=None;cleanup=None;view=OUT/'view'
    with common.watched():
        sandbox=previous.sandbox()[:-1]+['--bind',str(OLD),str(OLD),'--']
        prepared=run_job('prepare',sandbox+['/usr/bin/python3','-B',str(ROOT/'tools/complete_row_sources_resume6.py'),str(OUT)],
            OUT/'records',root=OUT/'control',timeout=800,cpu_limit=OUTER-30,rss_limit_gib=2.6,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'],
            metadata=dict(untrusted_source_preparation_only=True,new_solver_runs=0,new_game_row_checks=0,
                mathematical_objective_complete=False))
        assert prepared['accepted'],'Complete certificate-source preparation incomplete'
        manifest=json.loads((OUT/'archive-manifest.json').read_text());assert manifest['bound']==BOUND
        assert sha(manifest['archive'])==manifest['archive_sha256'] and manifest['new_game_row_checks']==0
        try:
            fs=Path(plan['filesystem_binary']);assert sha(fs)==plan['filesystem_binary_sha256']
            view.mkdir();log=(OUT/'filesystem.log').open('wb')
            process=subprocess.Popen([str(fs),manifest['archive'],str(view)],stdout=log,stderr=subprocess.STDOUT)
            start=time.monotonic()
            while not os.path.ismount(view):
                assert process.poll() is None and time.monotonic()-start<10
                time.sleep(.05)
            verified=verify_view(view,OUT/'archive-manifest.json')
            atomic_json(OUT/'view-verification.json',verified)
        finally:
            if os.path.ismount(view):subprocess.run(['/usr/bin/fusermount3','-u',str(view)],capture_output=True,text=True,timeout=8)
            if process is not None:
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
                log.close()
            cleanup=dict(unmounted=not os.path.ismount(view),exit=None if process is None else process.returncode)
            atomic_json(OUT/'view-cleanup.json',cleanup)
        assert cleanup['unmounted'] and cleanup['exit']==0
        assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,prepared=prepared['accepted'],
            source_archive_sha256=manifest['archive_sha256'],source_archive_bytes=manifest['archive_bytes'],
            emitted_groups=manifest['emitted_new_group_fields'],emitted_owner_rows=manifest['emitted_owner_rows'],
            emitted_tokens=manifest['emitted_tokens'],view_verification=verified,cleanup=cleanup,
            reused_group_count=manifest['reused_group_count'],reused_source_bytes_preserved=True,
            preparation_cpu_seconds=prepared['cpu_seconds'],preparation_peak_rss_gib=prepared['peak_rss_gib'],
            p1_unchanged=True,new_native_solver_runs=0,new_game_row_checks=0,
            source_values_not_yet_Agda_checked=True,production_go=False,mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),BOUND,'worker'],OUT/'records',
        root=OUT/'control',timeout=1000,cpu_limit=OUTER,rss_limit_gib=2.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running','--type=service','--no-legend','--plain','othello*'],text=True).strip()
    priorpath=OLD/'closure.json'
    prior=json.loads(priorpath.read_text())
    assert prior['closed'] and not prior['accepted'] and prior['coordinator_interrupted_for_phase_envelope']
    assert prior['combined_scope_cpu_seconds']+RESERVE+ALLOWANCE<=6000
    cap=json.loads((ROOT/'results/full-source-layout-scope-extension6-20261018.json').read_text());assert cap['new_cumulative_cap_cpu_seconds']==6000
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*','citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+32*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    helpers=['complete_row_sources_recovery_job6.py','complete_row_sources_resume6.py','bench6.py','compact_shared6.py','directed_probe6.py',
        'native_layout_samples6.py','unicode_codec_probe6.py','packed_wire6.py','wire_part_samples6.py','ref.py',
        'study_archive6.py','run_job.py','provenance.py']
    fs=BASE/'global-archive-probe6-20261018/archive-fs'
    archive=OLD/'row-sources.zip'
    plan=dict(created_utc=utc(),bound=BOUND,control_source=source_identity(OUT/'control'),
        helper_sha256={n:sha(ROOT/'tools'/n) for n in helpers},p1_files=history['p1_files'],
        filesystem_binary=str(fs),filesystem_binary_sha256=sha(fs),prior_allocated_study_bytes=used,
        previous_combined_scope_cpu_seconds=prior['combined_scope_cpu_seconds'],scope_cpu_cap=6000,
        reservation=RESERVE,outer_cpu_cap=OUTER,new_controller_allowance_seconds=ALLOWANCE,
        resume_archive=str(archive),partial_archive_sha256=sha(archive),initial_archive_allocated_bytes=archive.stat().st_blocks*512,
        hard_memory_gib=3,swap_bytes=0,core_bytes=0,own_and_shared_archive_growth_cap_mib=48,
        original_archive_target_envelope_mib=128,retained_study_cap_gib=12,
        root_free_floor_gib=80,untrusted_source_preparation_only=True,existing_wire_read_only=True,
        new_solver_runs=0,new_game_row_checks=0,production_go=False,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    if BOUND=='upper':request=dict(bound=BOUND,wire=json.loads((ROOT/'results/upper-wire-current6-20261018.json').read_text()))
    else:
        from wire_part_samples6 import _fingerprint
        wire=Path('/home/eapiova/projects/othello-agda/runs/six-full-map-lower-native-20261016/results/full-map-pilot6/initial-lower.wire')
        request=dict(bound=BOUND,wire=str(wire),wire_sha256='d6b4786ebafc86c5f1513d8e300366b9baf3ff06879defa8e2cb19998dc3a762',wire_fingerprint=list(_fingerprint(wire.stat())))
    request.update(resume_archive=str(archive),partial_archive_sha256=plan['partial_archive_sha256'])
    atomic_json(OUT/'input-request.json',request)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Append only missing LOWER source groups to the closed verified partial ZIP;128MiB source target envelope, shared archive growth counted explicitly inside unchanged12GiB cap, all failed preparation CPU and inline6000 usage retained')
    reservation=ledger.reserve('assembly',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=3G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=64','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=1030','--property=WorkingDirectory='+str(OUT/'control'),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),BOUND,'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=prior['combined_scope_cpu_seconds']+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[1]=='lower' and sys.argv[2] in ['launch','worker','supervise']
    if sys.argv[2]=='launch':launch()
    elif sys.argv[2]=='worker':worker()
    else:raise SystemExit(supervise())
