"""Durable file-by-file archive of the accepted full LOWER text cache.

Delete a file only after its exact bytes are durably stored and independently
verified. Receipts outside check/ and all protected original runs stay read-only.
"""
import hashlib,json,os,shutil,stat,struct,subprocess,sys,zipfile
from pathlib import Path
import assembly6
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity,digest_entries
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
SOURCE=BASE/'text-lower-probe6-20261018/check'
OUT=BASE/'lower-cache-archive6-20261018';UNIT='othello6-'+OUT.name+'.service'
RESERVE=150;OUTER=125;ALLOWANCE=10;CAP=160*2**20
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=4;common.RESERVATION_CPU=RESERVE


def durable(path,data):
    atomic_json(path,data)
    with path.open('rb') as f:os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()


def archive_worker():
    plan=json.loads((OUT/'plan.json').read_text());frozen=json.loads((OUT/'storage-freeze.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256']
    assert source_identity(SOURCE)['source_sha256']==plan['source_sha256']
    assert digest_entries(assembly6.interfaces(SOURCE))==plan['interface_pool_sha256']
    entries={};total=0
    for p in sorted(SOURCE.rglob('*')):
        s=p.lstat();assert not p.is_symlink() and (p.is_file() or p.is_dir()) and s.st_nlink>=1
        name=p.relative_to(SOURCE).as_posix()+('/' if p.is_dir() else '')
        assert len(name)<4094 and len(entries)<5000
        if p.is_file():assert s.st_nlink==1 and s.st_size<=16*2**20
        total+=s.st_size if p.is_file() else 0;assert total<=200*2**20
        entries[name]=dict(size=s.st_size if p.is_file() else 0,mode=s.st_mode,mtime_ns=s.st_mtime_ns,
            inode=s.st_ino,ctime_ns=s.st_ctime_ns,allocated_bytes=s.st_blocks*512,
            sha256=sha(p) if p.is_file() else hashlib.sha256(b'').hexdigest())
    journal=dict(created_utc=utc(),source=str(SOURCE),source_sha256=plan['source_sha256'],
        interface_pool_sha256=plan['interface_pool_sha256'],entries=entries,verified_and_removed=[],complete=False)
    durable(OUT/'journal.json',journal);released=0
    def storage(reserve=0):
        remaining=max(frozen['initial_source_allocated_bytes']-released,batch.allocated(SOURCE))
        own=batch.allocated(OUT);used=frozen['prior_without_source_allocated_bytes']+remaining+own
        assert own+reserve<=CAP and used+reserve<12*2**30
        free=shutil.disk_usage(ROOT).free;assert free-2**20>=80*2**30
        assert shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(allocated_study_bytes=used,own_output_bytes=own,conservative_source_remaining_bytes=remaining,
            root_free_bytes=free,reserved_bytes=reserve,checked_utc=utc())
    common.storage=storage;archive=OUT/'lower-text-cache.zip'
    with common.watched():
        for name,e in entries.items():
            p=SOURCE/name;s=p.stat();assert s.st_ino==e['inode'] and s.st_mtime_ns==e['mtime_ns']
            raw=p.read_bytes() if p.is_file() else b'';assert len(raw)==e['size'] and hashlib.sha256(raw).hexdigest()==e['sha256']
            info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=e['mode']<<16
            info.extra=struct.pack('<HHQ',0xa6da,8,e['mtime_ns']);info.compress_type=zipfile.ZIP_DEFLATED
            with zipfile.ZipFile(archive,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as saved:saved.writestr(info,raw)
            with archive.open('rb') as f:os.fsync(f.fileno())
            with zipfile.ZipFile(archive) as saved:
                assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
                zi=saved.getinfo(name);assert zi.external_attr>>16==e['mode'] and zi.extra==info.extra
            journal['verified_and_removed'].append(name);durable(OUT/'journal.json',journal)
            if stat.S_ISREG(e['mode']):
                now=p.stat();assert (now.st_ino,now.st_size,now.st_mtime_ns,now.st_ctime_ns)==(e['inode'],e['size'],e['mtime_ns'],e['ctime_ns'])
                p.unlink();released+=e['allocated_bytes']
            storage(8*2**20)
        assert not any(p.is_file() or p.is_symlink() for p in SOURCE.rglob('*'))
        with zipfile.ZipFile(archive) as saved:
            assert set(saved.namelist())==set(entries)
            for name,e in entries.items():assert hashlib.sha256(saved.read(name)).hexdigest()==e['sha256']
        for p in sorted(SOURCE.rglob('*'),key=lambda p:len(p.parts),reverse=True):p.rmdir()
        assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        journal.update(complete=True,finished_utc=utc(),archive=str(archive),archive_sha256=sha(archive))
        durable(OUT/'journal.json',journal)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,entries=len(entries),raw_bytes=total,
            archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
            every_file_verified_before_removal=True,all_entries_reverified=True,all_original_metadata_preserved=True,
            empty_source_directory_remaining=True,p1_unchanged=True,old_desktop_runs_and_NAMOR_untouched=True,
            native_solver_runs=0,agda_checks=0,mathematical_objective_complete=False))


def worker():
    import contextlib,fcntl,time
    from run_job import build_lock
    from study_archive6 import verify_view
    plan=json.loads((OUT/'plan.json').read_text())
    assert all(sha(ROOT/'tools'/n)==h for n,h in plan['other_helper_sha256'].items())
    cache=plan['upper_cache'];fs=Path(cache['filesystem_binary'])
    assert sha(fs)==plan['filesystem_binary_sha256'] and sha(Path(cache['archive']))==cache['archive_sha256']
    frozen=json.loads((OUT/'storage-freeze.json').read_text())
    upper_view=OUT/'upper-view';lower_view=OUT/'lower-view';check=OUT/'check'
    expected={Path(k):tuple(v) for k,v in plan['donors'].items() if k not in [str(SOURCE),cache['original_source']]}
    def physical_storage(reserve=0):
        own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
        used=frozen['prior_without_source_allocated_bytes']+own
        assert own+reserve<=CAP and used+reserve<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(checked_utc=utc(),allocated_study_bytes=used,own_output_bytes=own,
            root_free_bytes=shutil.disk_usage(ROOT).free,virtual_views_excluded_from_physical_allocation=True)
    processes=[];failure=None;phase=None;view_results={};cleanup=[]
    with contextlib.ExitStack() as stack:
        for donor in expected:
            lock=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=batch.donor_snapshot(expected)
        archive_sandbox=previous.sandbox()[:-1]+['--bind',str(SOURCE),str(SOURCE),'--']
        sealed=run_job('archive-seal',archive_sandbox+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'archive-only'],
            OUT/'records',root=OUT/'control',timeout=260,cpu_limit=70,rss_limit_gib=1.8,log_limit_mib=2,
            expected_source_sha256=plan['control_source']['source_sha256'])
        assert sealed['accepted'],'Durable LOWER cache sealing incomplete'
        SOURCE.rmdir()
        journal=json.loads((OUT/'journal.json').read_text());assert journal['complete']
        manifest=dict(format='othello-sealed-full-lower-cache-v1',created_utc=utc(),source=str(SOURCE),
            source_identity=plan['source_identity'],interfaces=plan['interfaces'],
            interface_pool_sha256=plan['interface_pool_sha256'],entries=journal['entries'],
            raw_bytes=sum(e['size'] for e in journal['entries'].values()),archive=journal['archive'],
            archive_sha256=journal['archive_sha256'],original_source_removed=True,
            mathematical_objective_complete=False)
        atomic_json(OUT/'archive-manifest.json',manifest)
        (check/'src/Tests').mkdir(parents=True)
        (check/'src/Tests/SealedLowerReplay6.agda').write_text('''{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted cache portability replay; no additional game rows are checked.
module Tests.SealedLowerReplay6 where
import Tests.TextLowerPacked6.Joint
import Tests.TextLowerPacked6.Rows686
''')
        shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
        identity=source_identity(check);atomic_json(OUT/'emission.json',dict(created_utc=utc(),source=identity))
        stack.enter_context(build_lock(check));common.storage=physical_storage
        try:
            for label,archive,view,metadata in [('upper',Path(cache['archive']),upper_view,Path(cache['manifest'])),
                ('lower',Path(manifest['archive']),lower_view,OUT/'archive-manifest.json')]:
                view.mkdir();log=stack.enter_context((OUT/(label+'-filesystem.log')).open('wb'))
                process=subprocess.Popen([str(fs),str(archive),str(view)],stdout=log,stderr=subprocess.STDOUT)
                processes.append((view,process));start=time.monotonic()
                while not os.path.ismount(view):
                    assert process.poll() is None and time.monotonic()-start<10
                    time.sleep(.05)
                view_results[label]=verify_view(view,metadata)
            actual=dict(expected)
            actual[upper_view]=(cache['source_sha256'],cache['interface_pool_sha256'])
            actual[lower_view]=(plan['source_sha256'],plan['interface_pool_sha256'])
            args=previous.sandbox()[:-1]
            for view,_ in processes:args+=['--ro-bind',str(view),str(view)]
            args+=['--',batch.full_map.AGDA,'--no-libraries','-i','src']
            for donor in actual:args+=['-i',str(donor/'src')]
            args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                'src/Tests/SealedLowerReplay6.agda','+RTS','-M2800M','-s','-RTS']
            with common.watched():
                result=run_job('archive-cache-replay',args,OUT/'records',root=check,timeout=100,cpu_limit=35,
                    rss_limit_gib=3.6,log_limit_mib=2,expected_source_sha256=identity['source_sha256'],
                    metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,both_archive_views_read_only=True,
                        additional_game_rows=0,mathematical_objective_complete=False))
                phase={k:result[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']}
                assert result['accepted'],'Lower archive replay incomplete'
                assert verify_view(upper_view,cache['manifest'])==view_results['upper']
                assert verify_view(lower_view,OUT/'archive-manifest.json')==view_results['lower']
        except BaseException as error:failure=repr(error)
        finally:
            for view,process in reversed(processes):
                unmount=None
                if os.path.ismount(view):unmount=subprocess.run(['/usr/bin/fusermount3','-u',str(view)],capture_output=True,text=True,timeout=8)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
                cleanup.append(dict(view=str(view),unmounted=not os.path.ismount(view),fuse_exit=process.returncode,
                    unmount_exit=None if unmount is None else unmount.returncode))
            atomic_json(OUT/'view-cleanup.json',cleanup)
        intact=batch.donor_snapshot(expected)==before
        p1=all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        accepted=failure is None and phase is not None and phase['accepted'] and all(x['unmounted'] for x in cleanup)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=accepted,failure=failure,phase=phase,
            views=view_results,cleanup=cleanup,source_entries_exact=True,plain_source_removed=True,
            archive=str(OUT/'lower-text-cache.zip'),archive_sha256=journal['archive_sha256'],
            archive_bytes=(OUT/'lower-text-cache.zip').stat().st_size,entries=len(journal['entries']),
            accepted_donors_unchanged=intact,p1_unchanged=p1,old_desktop_runs_and_NAMOR_untouched=True,
            additional_game_row_checks=0,mathematical_objective_complete=False))
        assert accepted and intact and p1 and source_identity(check)==identity,'Archive/replay incomplete; exact recoverable bytes retained'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],OUT/'records',
        root=OUT/'control',timeout=400,cpu_limit=OUTER,rss_limit_gib=3.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and SOURCE.is_dir() and not SOURCE.is_symlink()
    assert not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    closed=json.loads((SOURCE.parent/'closure.json').read_text());assert closed['accepted']
    prior=closed['combined_scope_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=2000
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+16*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    source=source_identity(SOURCE);pool=assembly6.interfaces(SOURCE)
    assert source['source_sha256']==closed['source_sha256'] and digest_entries(pool)==closed['interface_pool_sha256']
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    atomic_json(OUT/'storage-freeze.json',dict(created_utc=utc(),prior_allocated_study_bytes=used,
        initial_source_allocated_bytes=batch.allocated(SOURCE),prior_without_source_allocated_bytes=used-batch.allocated(SOURCE),
        own_output_cap_bytes=CAP,retained_study_cap_gib=12,root_free_floor_gib=80,
        rolling_archive_counts_source_and_archive_physical_bytes=True))
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    oldplan=json.loads((SOURCE.parent/'plan.json').read_text());expected=oldplan['donors']
    expected[str(SOURCE)]=[closed['source_sha256'],closed['interface_pool_sha256']]
    cache=json.loads((ROOT/'results/text-upper-cache-current6-20261018.json').read_text())
    plan=dict(created_utc=utc(),control_source=source_identity(OUT/'control'),helper_sha256=sha(Path(__file__)),
        other_helper_sha256={n:sha(ROOT/'tools'/n) for n in ['study_archive6.py','study_archive_fs6.c']+list(oldplan['helper_sha256'])},
        filesystem_binary_sha256=sha(Path(cache['filesystem_binary'])),upper_cache=cache,donors=expected,
        source_identity=source,interfaces=pool,source_sha256=closed['source_sha256'],
        interface_pool_sha256=closed['interface_pool_sha256'],p1_files=history['p1_files'],
        previous_combined_scope_cpu_seconds=prior,scope_cpu_cap=2000,reservation=RESERVE,outer_cpu_cap=OUTER,
        new_controller_allowance_seconds=ALLOWANCE,hard_memory_gib=4,swap_bytes=0,core_bytes=0,
        archive_entry_verified_before_any_source_unlink=True,check_both_full_archive_views_after_sealing=True,
        mutation_scope=str(SOURCE),mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Durable bounded full LOWER cache archive, verify every entry before unlink and replay dense/joint accepted interfaces through both read-only archive views; inline2000 actuals retained')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=4G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=430','--property=WorkingDirectory='+str(OUT/'control'),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','supervise','worker','archive-only']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    elif sys.argv[1]=='archive-only':archive_worker()
    else:raise SystemExit(supervise())

