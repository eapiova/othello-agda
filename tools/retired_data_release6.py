"""Retire only unused vector-table data caches; preserve exact sources and all other interfaces."""
import hashlib,json,os,re,shutil,stat,struct,subprocess,sys,time,zipfile
from pathlib import Path
import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity,digest_entries
from run_job import atomic_json,run_job,utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'retired-data-release6-20261018';UNIT='othello6-'+OUT.name+'.service'
OLD=BASE/'retired-vector-archive6-20261018'
RESERVE=100;OUTER=75;ALLOWANCE=10
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=2;common.RESERVATION_CPU=RESERVE


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()


def worker():
    plan=json.loads((OUT/'plan.json').read_text());assert sha(Path(__file__))==plan['helper_sha256']
    original=Path(plan['original_archive']);assert sha(original)==plan['original_archive_sha256']
    old=json.loads((OLD/'journal.json').read_text());assert old['complete']
    omit={n for n in old['entries'] if re.fullmatch(r'_build/2[.]9[.]0/agda/src/Tests/FullUpperPacked6/Group[0-9]+[.]agdai',n)}
    assert len(omit)==654
    entries={};pool={};dropped={};archive=OUT/'sources-and-proof-cache.zip'
    def storage(reserve=0):
        own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
        assert own+reserve<64*2**20 and plan['prior_allocated_study_bytes']+own+reserve<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(checked_utc=utc(),allocated_study_bytes=plan['prior_allocated_study_bytes']+own,
            own_output_bytes=own,root_free_bytes=shutil.disk_usage(ROOT).free)
    common.storage=storage
    process=None;view=OUT/'view';cleanup=None
    with common.watched():
        with zipfile.ZipFile(original) as source,zipfile.ZipFile(archive,'x') as target:
            assert set(source.namelist())==set(old['entries'])
            for name,e in old['entries'].items():
                if name in omit:
                    relative=name.split('/agda/',1)[1][:-6]+'.agda'
                    raw_source=source.read(relative)
                    assert hashlib.sha256(raw_source).hexdigest()==old['entries'][relative]['sha256']
                    assert b'table : M.Map Packed.PackedState' in raw_source
                    assert all(token not in raw_source for token in [b'Proven',b'Partial',b'Certified',b'postulate',b'abstract'])
                    dropped[name]=dict(old_sha256=e['sha256'],source=relative,source_sha256=hashlib.sha256(raw_source).hexdigest(),
                        kind='regenerable table-data interface; no proof declaration')
                    continue
                raw=source.read(name);assert hashlib.sha256(raw).hexdigest()==e['sha256']
                info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=e['mode']<<16
                info.extra=struct.pack('<HHQ',0xa6da,8,e['mtime_ns'])
                method=zipfile.ZIP_ZSTANDARD if name.endswith('.agda') else zipfile.ZIP_STORED
                target.writestr(info,raw,compress_type=method,compresslevel=19 if method==zipfile.ZIP_ZSTANDARD else None)
                entries[name]={k:e[k] for k in ['size','sha256','mode','mtime_ns']}
                if name.endswith('.agdai'):pool[name]=e['sha256']
                storage(8*2**20)
        assert len(pool)==2 and all(not n.endswith('.agdai') or n in omit or n in pool for n in old['entries'])
        with archive.open('rb') as stream:os.fsync(stream.fileno())
        with zipfile.ZipFile(archive) as saved:
            assert set(saved.namelist())==set(entries)
            for name,e in entries.items():assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
        manifest=dict(format='othello-retired-vector-source-proof-cache-v1',created_utc=utc(),
            source=old['source'],source_identity=plan['source_identity'],interfaces=pool,
            interface_pool_sha256=digest_entries(pool),entries=entries,raw_bytes=sum(e['size'] for e in entries.values()),
            archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
            omitted_regenerable_data_interfaces=dropped,all_source_and_retained_interface_bytes_exact=True,
            original_container_retirement_pending=True,mathematical_objective_complete=False)
        atomic_json(OUT/'archive-manifest.json',manifest)
        with (OUT/'archive-manifest.json').open('rb') as stream:os.fsync(stream.fileno())
        fd=os.open(OUT,os.O_RDONLY);os.fsync(fd);os.close(fd)
        try:
            view.mkdir();log=(OUT/'filesystem.log').open('wb')
            fs=Path(plan['filesystem_binary']);assert sha(fs)==plan['filesystem_binary_sha256']
            process=subprocess.Popen([str(fs),str(archive),str(view)],stdout=log,stderr=subprocess.STDOUT)
            start=time.monotonic()
            while not os.path.ismount(view):
                assert process.poll() is None and time.monotonic()-start<10
                time.sleep(.05)
            verified=verify_view(view,OUT/'archive-manifest.json')
            atomic_json(OUT/'view-verification.json',verified)
        finally:
            unmount=None
            if os.path.ismount(view):unmount=subprocess.run(['/usr/bin/fusermount3','-u',str(view)],capture_output=True,text=True,timeout=8)
            if process is not None:
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
                log.close()
            cleanup=dict(unmounted=not os.path.ismount(view),exit=None if process is None else process.returncode)
            atomic_json(OUT/'view-cleanup.json',cleanup)
        assert cleanup['unmounted'] and cleanup['exit']==0
        assert sha(original)==plan['original_archive_sha256'] and original.stat().st_nlink==1
        assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        # The source and every non-Group interface are durable and independently read back.
        # The old container is replaced; only its regenerable Group data caches are discarded.
        original.unlink()
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,retained_entries=len(entries),
            omitted_data_interfaces=len(dropped),retained_interfaces=len(pool),original_container_removed=True,
            all_source_bytes_metadata_and_nonGroup_interfaces_preserved=True,view_verified=verified,
            new_archive_bytes=archive.stat().st_size,new_archive_sha256=manifest['archive_sha256'],
            old_desktop_runs_and_NAMOR_untouched=True,p1_unchanged=True,zip93_view_verified=True,
            mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    # Orchestration mounts a read-only view; only the two explicitly owned archive paths are mutated.
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=180,cpu_limit=OUTER,rss_limit_gib=1.8,log_limit_mib=1,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((BASE/'data-cache-transcode6-20261018/closure.json').read_text())['combined_scope_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=6000
    extension=json.loads((ROOT/'results/full-source-layout-scope-extension6-20261018.json').read_text());assert extension['new_cumulative_cap_cpu_seconds']==6000
    old=json.loads((OLD/'closure.json').read_text());assert old['accepted']
    original=Path(old['archive']);assert original.is_file() and original.stat().st_nlink==1
    for bound in ['upper','lower']:
        assert str(original)!=json.loads((ROOT/f'results/text-{bound}-cache-current6-20261018.json').read_text())['archive']
    donor=json.loads((BASE/'text-upper-holdout6-20261018/plan.json').read_text())['donors']
    assert str(BASE/'full-upper-probe6-20261018/check') not in donor
    source=json.loads((BASE/'full-upper-probe6-20261018/emission.json').read_text())['source'];assert source['source_sha256']==old['archived_source_sha256']
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*','citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+64*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    fs=BASE/'global-archive-probe6-20261018/archive-fs'
    p=dict(created_utc=utc(),control_source=source_identity(OUT/'control'),helper_sha256=sha(Path(__file__)),
        source_identity=source,p1_files=history['p1_files'],original_archive=str(original),original_archive_sha256=old['archive_sha256'],
        filesystem_binary=str(fs),filesystem_binary_sha256=sha(fs),prior_allocated_study_bytes=used,
        previous_combined_scope_cpu_seconds=prior,scope_cpu_cap=6000,reservation=RESERVE,outer_cpu_cap=OUTER,
        new_controller_allowance_seconds=ALLOWANCE,hard_memory_gib=2,swap_bytes=0,core_bytes=0,
        retained_study_cap_gib=12,root_free_floor_gib=80,own_output_cap_mib=64,
        authorization='User-authorized cleanup and necessary proof storage; exact sources and every non-Group interface retained, only unused generated table-data caches retired')
    atomic_json(OUT/'plan.json',p)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Retire unused generated vector-table caches only, preserve all source and other interfaces exactly, verify complete ZIP93 source view before old container removal; all prior inline6000 charges preserved')
    reservation=ledger.reserve('assembly',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=p['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=2G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=64','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=210','--property=WorkingDirectory='+str(OUT/'control'),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
