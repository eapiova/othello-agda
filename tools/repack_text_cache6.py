"""Repack one full cache: source bytes and proof interfaces exact, table payloads exact."""
import contextlib,fcntl,hashlib,json,os,re,shutil,stat,struct,subprocess,sys,time,zipfile
from pathlib import Path
from compression import zstd
import assembly6
import citation_diagnostic6 as common
import completion_batch6 as batch
import big_rows_probe6 as previous
from provenance import source_identity,digest_entries
from run_job import atomic_json,build_lock,run_job,utc
from study6 import Ledger
from study_archive6 import verify_view

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
BOUND=sys.argv[1] if len(sys.argv)>1 and sys.argv[1] in ['upper','lower'] else 'upper'
OUT=BASE/('packed-'+BOUND+'-cache6-20261018');CHECK=OUT/'check';UNIT='othello6-'+OUT.name+'.service'
RESERVE=180;OUTER=150;ALLOWANCE=10
previous.OUT=OUT;common.OUT=OUT;common.HARD_GIB=6;common.RESERVATION_CPU=RESERVE


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    return h.hexdigest()


def pack(plan):
    cache=plan['caches'][BOUND];original=json.loads(Path(cache['manifest']).read_text())
    assert sha(cache['archive'])==cache['archive_sha256']
    archive=OUT/'cache.zip';entries={};interfaces={};lineage={}
    pattern=re.compile(r'_build/2[.]9[.]0/agda/src/Tests/Text'+BOUND.title()+r'Packed6/Group[0-9]+[.]agdai')
    with zipfile.ZipFile(cache['archive']) as old,zipfile.ZipFile(archive,'x') as new:
        assert set(old.namelist())==set(original['entries'])
        for name,e in original['entries'].items():
            raw=old.read(name);assert hashlib.sha256(raw).hexdigest()==e['sha256']
            if pattern.fullmatch(name):
                source=name.split('/agda/',1)[1][:-6]+'.agda';text=old.read(source)
                assert hashlib.sha256(text).hexdigest()==original['entries'][source]['sha256']
                assert b'table : T.Map' in text and all(t not in text for t in [b'Proven',b'Partial',b'Certified',b'postulate',b'abstract'])
                assert raw[24:28]==bytes.fromhex('28b52ffd')
                decoded=zstd.decompress(raw[24:]);assert len(decoded)<16*2**20
                encoded=raw[:24]+zstd.compress(decoded,level=19)
                assert encoded[:24]==raw[:24] and zstd.decompress(encoded[24:])==decoded
                lineage[name]=dict(old_sha256=e['sha256'],new_sha256=hashlib.sha256(encoded).hexdigest(),
                    decoded_payload_sha256=hashlib.sha256(decoded).hexdigest(),header_hex=raw[:24].hex(),
                    source_sha256=hashlib.sha256(text).hexdigest(),old_bytes=len(raw),new_bytes=len(encoded))
                raw=encoded
            info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=e['mode']<<16
            info.extra=struct.pack('<HHQ',0xa6da,8,e['mtime_ns'])
            method=zipfile.ZIP_STORED if name.endswith('.agdai') or stat.S_ISDIR(e['mode']) else zipfile.ZIP_ZSTANDARD
            new.writestr(info,raw,compress_type=method,compresslevel=19 if method==zipfile.ZIP_ZSTANDARD else None)
            entries[name]=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=e['mode'],mtime_ns=e['mtime_ns'])
            if name.endswith('.agdai'):interfaces[name]=entries[name]['sha256']
            common.storage(8*2**20)
    assert len(lineage)==(654 if BOUND=='upper' else 688)
    assert all(interfaces[n]==h for n,h in original['interfaces'].items() if n not in lineage)
    with archive.open('rb') as stream:os.fsync(stream.fileno())
    with zipfile.ZipFile(archive) as new:
        assert set(new.namelist())==set(entries)
        for name,e in entries.items():assert hashlib.sha256(new.read(name)).hexdigest()==e['sha256']
    manifest=dict(format='othello-full-cache-table-payload-preserving-repack-v1',created_utc=utc(),
        source=original['source'],source_identity=original['source_identity'],interfaces=interfaces,
        interface_pool_sha256=digest_entries(interfaces),entries=entries,raw_bytes=sum(e['size'] for e in entries.values()),
        archive=str(archive),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
        parent_archive=cache['archive'],parent_archive_sha256=cache['archive_sha256'],
        all_source_and_nonGroup_interface_bytes_exact=True,group_interface_decoded_payloads_exact=True,
        mathematical_objective_complete=False)
    atomic_json(OUT/'archive-manifest.json',manifest);atomic_json(OUT/'payload-lineage.json',lineage)
    for p in [OUT/'archive-manifest.json',OUT/'payload-lineage.json']:
        with p.open('rb') as stream:os.fsync(stream.fileno())
    fd=os.open(OUT,os.O_RDONLY);os.fsync(fd);os.close(fd)
    return manifest


def worker():
    batch.authorized();plan=json.loads((OUT/'plan.json').read_text())
    assert all(sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    def storage(reserve=0):
        own=int(subprocess.check_output(['du','-s','-x','-B1',str(OUT)],text=True).split()[0])
        assert own+reserve<=112*2**20 and plan['prior_allocated_study_bytes']+own+reserve<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30 and shutil.disk_usage(OUT).free-reserve>=80*2**30
        return dict(checked_utc=utc(),allocated_study_bytes=plan['prior_allocated_study_bytes']+own,
            own_output_bytes=own,root_free_bytes=shutil.disk_usage(ROOT).free,virtual_views_not_double_counted=True)
    common.storage=storage;expected={Path(k):tuple(v) for k,v in plan['donors'].items()}
    processes=[];views={};phase=None;failure=None;cleanup=[];manifest=None
    with contextlib.ExitStack() as stack:
        for donor in expected:
            lock=stack.enter_context((donor/'_build/.study6.lock').open('rb'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=batch.donor_snapshot(expected);stack.enter_context(common.watched())
        manifest=pack(plan)
        fs=Path(plan['filesystem_binary']);assert sha(fs)==plan['filesystem_binary_sha256']
        (CHECK/'src/Tests').mkdir(parents=True)
        (CHECK/'src/Tests/RepackedTextReplay6.agda').write_text('''{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}
-- AI-assisted: replay unchanged mathematical proof interfaces with identical data payloads.
module Tests.RepackedTextReplay6 where
import Tests.TextLowerPacked6.Joint
import Tests.TextUpperHoldout6.Rows500
''')
        shutil.copy2(ROOT/'othello.agda-lib',CHECK/'othello.agda-lib')
        identity=source_identity(CHECK);atomic_json(OUT/'emission.json',dict(created_utc=utc(),source=identity))
        stack.enter_context(build_lock(CHECK))
        try:
            actual=dict(expected)
            for label,cache in plan['caches'].items():
                archive=Path(manifest['archive']) if label==BOUND else Path(cache['archive'])
                meta=OUT/'archive-manifest.json' if label==BOUND else Path(cache['manifest'])
                assert sha(archive)==(manifest['archive_sha256'] if label==BOUND else cache['archive_sha256'])
                view=OUT/(label+'-view');view.mkdir();log=stack.enter_context((OUT/(label+'-filesystem.log')).open('wb'))
                process=subprocess.Popen([str(fs),str(archive),str(view)],stdout=log,stderr=subprocess.STDOUT)
                processes.append((view,process));start=time.monotonic()
                while not os.path.ismount(view):
                    assert process.poll() is None and time.monotonic()-start<10
                    time.sleep(.05)
                views[label]=verify_view(view,meta)
                actual[view]=(cache['source_sha256'],manifest['interface_pool_sha256'] if label==BOUND else cache['interface_pool_sha256'])
            args=previous.sandbox()[:-1]
            for view,_ in processes:args+=['--ro-bind',str(view),str(view)]
            args+=['--',batch.full_map.AGDA,'--no-libraries','-i','src']
            for donor in actual:args+=['-i',str(donor/'src')]
            args+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules','--no-write-interfaces',
                'src/Tests/RepackedTextReplay6.agda','+RTS','-M4500M','-s','-RTS']
            result=run_job('cache-replay',args,OUT/'records',root=CHECK,timeout=140,cpu_limit=45,rss_limit_gib=5.6,
                log_limit_mib=2,expected_source_sha256=identity['source_sha256'],
                metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,table_payload_recompression=True,
                    proof_interface_bytes_unchanged=True,all_source_bytes_unchanged=True,additional_game_row_checks=0,
                    mathematical_objective_complete=False))
            phase={k:result[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']}
            assert result['accepted'],'Repacked cache replay incomplete'
            log=(OUT/'records/cache-replay.log').read_text()
            for name in ['Tests.TextUpperHoldout6.Rows500','Tests.TextLowerPacked6.Joint']:
                assert 'Checking '+name not in log,'A mathematical proof was rechecked: '+name
            assert not assembly6.interfaces(CHECK)
            for label,cache in plan['caches'].items():
                meta=OUT/'archive-manifest.json' if label==BOUND else Path(cache['manifest'])
                assert verify_view(OUT/(label+'-view'),meta)==views[label]
        except BaseException as error:failure=repr(error)
        finally:
            for view,process in reversed(processes):
                if os.path.ismount(view):subprocess.run(['/usr/bin/fusermount3','-u',str(view)],capture_output=True,text=True,timeout=8)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
                cleanup.append(dict(view=str(view),unmounted=not os.path.ismount(view),exit=process.returncode))
            atomic_json(OUT/'view-cleanup.json',cleanup)
        intact=batch.donor_snapshot(expected)==before
        p1=all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        complete=failure is None and phase is not None and phase['accepted'] and all(v['unmounted'] for v in cleanup)
        ref=dict(plan['caches'][BOUND]);ref.update(archive=manifest['archive'],archive_sha256=manifest['archive_sha256'],
            manifest=str(OUT/'archive-manifest.json'),interface_pool_sha256=manifest['interface_pool_sha256'],
            parent_cache_manifest=plan['caches'][BOUND]['manifest'],payload_lineage=str(OUT/'payload-lineage.json'),
            archive_view_replay_accepted=complete,proof_interfaces_byte_exact=True,source_bytes_byte_exact=True,
            table_interface_payloads_byte_exact=True,original_compressed_table_frames_not_claimed_identical=True)
        atomic_json(OUT/'new-cache-reference.json',ref)
        atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=complete,failure=failure,phase=phase,views=views,
            cleanup=cleanup,accepted_donors_unchanged=intact,p1_unchanged=p1,source_unchanged=source_identity(CHECK)==identity,
            all_source_bytes_and_nonGroup_interfaces_preserved=True,all_table_payloads_preserved=True,
            proof_reused_without_boolean_rerun=complete,original_archive_not_removed_by_worker=True,
            new_archive_bytes=manifest['archive_bytes'],new_archive_sha256=manifest['archive_sha256'],
            additional_game_row_checks=0,mathematical_objective_complete=False))
        assert complete and intact and p1 and source_identity(CHECK)==identity,'Repack incomplete; original cache retained'


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,['/usr/bin/python3','-B',str(Path(__file__).resolve()),BOUND,'worker'],OUT/'records',
        root=OUT/'control',timeout=600,cpu_limit=OUTER,rss_limit_gib=5.8,log_limit_mib=2,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running','--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior_path=BASE/('retired-data-release6-20261018' if BOUND=='upper' else 'packed-upper-cache6-20261018')/'closure.json'
    closed=json.loads(prior_path.read_text());assert closed['accepted']
    prior=closed['combined_scope_cpu_seconds'];assert prior+RESERVE+ALLOWANCE<=6000
    extension=json.loads((ROOT/'results/full-source-layout-scope-extension6-20261018.json').read_text());assert extension['new_cumulative_cap_cpu_seconds']==6000
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*','citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+112*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    caches={label:json.loads((ROOT/f'results/text-{label}-cache-current6-20261018.json').read_text()) for label in ['upper','lower']}
    assert all(c['archive_view_replay_accepted'] for c in caches.values())
    oldplan=json.loads((BASE/'data-cache-transcode6-20261018/plan.json').read_text());donors=oldplan['donors']
    held=BASE/'text-upper-holdout6-20261018';held_closed=json.loads((held/'closure.json').read_text())
    donors[str(held/'check')]=[held_closed['source_sha256'],held_closed['interface_pool_sha256']]
    assert all(c['original_source'] not in donors for c in caches.values())
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    helpers=set(['repack_text_cache6.py','study_archive6.py']+list(oldplan['helper_sha256']))
    plan=dict(created_utc=utc(),control_source=source_identity(OUT/'control'),helper_sha256={n:sha(ROOT/'tools'/n) for n in helpers},
        bound=BOUND,caches=caches,donors=donors,p1_files=history['p1_files'],prior_allocated_study_bytes=used,
        filesystem_binary=caches['upper']['filesystem_binary'],filesystem_binary_sha256=sha(caches['upper']['filesystem_binary']),
        previous_combined_scope_cpu_seconds=prior,scope_cpu_cap=6000,reservation=RESERVE,outer_cpu_cap=OUTER,
        new_controller_allowance_seconds=ALLOWANCE,hard_memory_gib=6,swap_bytes=0,core_bytes=0,
        retained_study_cap_gib=12,root_free_floor_gib=80,own_output_cap_mib=112,
        all_source_and_nonGroup_interface_bytes_preserved=True,group_interface_payloads_preserved=True,
        original_archive_removed_only_after_accepted_terminal_replay=True)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',ALLOWANCE,'Full '+BOUND+' data-cache repack with unchanged sources/proof bytes and identical decoded table payloads; dual-cache proof replay before replacement, all inline6000 charges retained')
    reservation=ledger.reserve('kernel',RESERVE,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=6G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=630','--property=WorkingDirectory='+str(OUT/'control'),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),BOUND,'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=prior+RESERVE+ALLOWANCE)))


if __name__=='__main__':
    assert len(sys.argv)==3 and sys.argv[1] in ['upper','lower'] and sys.argv[2] in ['launch','worker','supervise']
    if sys.argv[2]=='launch':launch()
    elif sys.argv[2]=='worker':worker()
    else:raise SystemExit(supervise())
