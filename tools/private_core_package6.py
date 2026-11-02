"""Prepare exact selected source dependencies for the private 6x6 package.

AI-assisted source packaging; neither generation nor readback proves Problem2.
Existing large immutable source archives are referenced, never duplicated.
"""
import contextlib,hashlib,json,os,re,shutil,stat,struct,subprocess,sys,zipfile
from compression import zstd
from pathlib import Path
import big_rows_probe6 as previous
import citation_diagnostic6 as common
import completion_batch6 as batch
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'private-core-package6-20261018';UNIT='othello6-'+OUT.name+'.service'
IMPORT=re.compile(r'^\s*(?:open\s+)?import\s+([A-Za-z0-9_.]+)',re.M)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda:stream.read(2**20),b''):h.update(b)
    return h.hexdigest()


def worker():
    plan=json.loads((OUT/'plan.json').read_text())
    assert sha(Path(__file__))==plan['helper_sha256']
    donors=[Path(p) for p in plan['donors']]
    selected={};core={};builtins=set();edges={};opened={};providers=[]
    with contextlib.ExitStack() as stack:
        for label,p in plan['packages'].items():
            assert sha(p['archive'])==p['archive_sha256']
            z=stack.enter_context(zipfile.ZipFile(p['archive']));opened[label]=z
            m=json.loads(Path(p['manifest']).read_text());providers.append((label,p,m,set(z.namelist())))
        def resolve(module):
            relative='src/'+module.replace('.','/')+'.agda'
            for donor in donors:
                file=donor/relative
                if file.is_file():
                    s=file.stat();raw=file.read_bytes()
                    return raw,dict(provider='core',source=str(file),entry=relative,sha256=hashlib.sha256(raw).hexdigest(),
                        size=len(raw),mode=s.st_mode,mtime_ns=s.st_mtime_ns)
            for label,p,m,names in providers:
                entry=relative
                if label.endswith('-sources'):
                    prefix=m['prefix']+'.'
                    if not module.startswith(prefix):continue
                    short=module[len(prefix):]
                    if '.' in short:continue
                    entry=short+'.agda'
                if entry not in names:continue
                raw=opened[label].read(entry);e=m['entries'][entry]
                assert hashlib.sha256(raw).hexdigest()==e['sha256']
                return raw,dict(provider=label,archive=p['archive'],archive_sha256=p['archive_sha256'],
                    entry=entry,sha256=e['sha256'],size=len(raw),mode=e['mode'],mtime_ns=e['mtime_ns'])
            raise ValueError('Unresolved source dependency: '+module)
        pending=['Tests.CompleteUpperRows6.Result']
        while pending:
            module=pending.pop()
            if module in selected or module in builtins:continue
            if module.startswith('Agda.'):
                builtins.add(module);continue
            raw,e=resolve(module);selected[module]=e
            text=raw.decode();imports=IMPORT.findall(text);edges[module]=imports
            if e['provider']=='core':core[e['entry']]=(raw,e)
            pending.extend(imports)
        assert len(selected)<6000 and len(core)<500
        lib=ROOT/'othello.agda-lib';s=lib.stat();core['othello.agda-lib']=(lib.read_bytes(),
            dict(source=str(lib),sha256=sha(lib),size=s.st_size,mode=s.st_mode,mtime_ns=s.st_mtime_ns))
        archive=OUT/'core-source.zip'
        with zipfile.ZipFile(archive,'x') as z:
            for name,(raw,e) in sorted(core.items()):
                info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=e['mode']<<16
                info.extra=struct.pack('<HHQ',0xa6da,8,e['mtime_ns'])
                z.writestr(info,raw,compress_type=zipfile.ZIP_ZSTANDARD,compresslevel=19)
        with archive.open('rb') as stream:os.fsync(stream.fileno())
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist())==set(core)
            for name,(raw,e) in core.items():
                info=z.getinfo(name)
                assert z.read(name)==raw and info.external_attr>>16==e['mode']
                assert info.extra==struct.pack('<HHQ',0xa6da,8,e['mtime_ns'])
        assert all(sha(Path(e['source']))==e['sha256'] for raw,e in core.values())
        assert all(sha(ROOT/n)==h for n,h in plan['p1_files'].items())
        graph_raw=json.dumps(dict(selected_modules=selected,dependency_edges=edges),
            sort_keys=True,separators=(',',':')).encode()
        graph=OUT/'source-graph.json.zst';graph.write_bytes(zstd.compress(graph_raw,level=19))
        assert zstd.decompress(graph.read_bytes())==graph_raw
        with graph.open('rb') as stream:os.fsync(stream.fileno())
        manifest=dict(format='othello-private-selected-source-package-v1',finished_utc=utc(),
            entrypoint='Tests.CompleteUpperRows6.Result.initial6x6 : Problem2',
            core_archive=str(archive),core_archive_sha256=sha(archive),core_archive_bytes=archive.stat().st_size,
            core_entries={n:e for n,(raw,e) in core.items()},selected_module_count=len(selected),
            source_graph=str(graph),source_graph_sha256=sha(graph),source_graph_decoded_sha256=hashlib.sha256(graph_raw).hexdigest(),
            builtin_modules_from_pinned_Agda=sorted(builtins),large_archive_references=plan['packages'],
            source_resolution_order_preserved=True,all_selected_source_bytes_modes_ns_mtimes_preserved=True,
            original_desktop_runs_and_NAMOR_untouched=True,p1_unchanged=True,
            package_source_integrity_verified=True,package_build_not_yet_checked=True,
            complete_initial_theorem_not_yet_checked=True,mathematical_objective_complete=False)
        atomic_json(OUT/'manifest.json',manifest)
        own=batch.allocated(OUT)
        assert own+65536<2*2**20 and plan['prior_allocated_study_bytes']+own<12*2**30
        assert shutil.disk_usage(ROOT).free-2**20>=80*2**30
        atomic_json(OUT/'report.json',dict(accepted=True,finished_utc=utc(),selected_modules=len(selected),
            core_source_files=len(core),core_archive_bytes=archive.stat().st_size,own_output_bytes=own,
            large_source_archives_reused=True,source_integrity_only=True,new_game_row_checks=0,
            p1_unchanged=True,mathematical_objective_complete=False))


def supervise():
    j=json.loads((OUT/'job.json').read_text())
    sandbox=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(OUT),str(OUT),
        '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--']
    r=run_job(OUT.name,sandbox+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=500,cpu_limit=80,rss_limit_gib=2.6,log_limit_mib=2,
        reservation_id=j['reservation']['reservation_id'],expected_source_sha256=j['control_source']['source_sha256'])
    return 0 if r['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((BASE/'completion-log-archive6-20261018/closure.json').read_text())
    assert prior['accepted'] and prior['combined_scope_cpu_seconds']+110<6000
    common.OUT=ROOT/'results/audit-no-output6-20261018';legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}|{Path(e['path']) for e in registry['roots'] if Path(e['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+2*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    donors=json.loads((BASE/'packed-lower-cache6-20261018/plan.json').read_text())['donors']
    packages={}
    for side in ['upper','lower']:
        packages[side+'-cache']=json.loads((ROOT/('results/text-'+side+'-cache-current6-20261018.json')).read_text())
        packages[side+'-sources']=json.loads((ROOT/('results/complete-'+side+'-row-sources-index6-20261018.json')).read_text())
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
    plan=dict(created_utc=utc(),helper_sha256=sha(Path(__file__)),control_source=source_identity(OUT/'control'),
        donors=donors,packages=packages,p1_files=history['p1_files'],prior_allocated_study_bytes=used,
        previous_combined_scope_cpu_seconds=prior['combined_scope_cpu_seconds'],new_controller_allowance_seconds=10,
        scope_cpu_cap=6000,own_output_cap_mib=2,root_free_floor_gib=80,retained_study_cap_gib=12,
        hard_memory_gib=3,swap_bytes=0,core_bytes=0,new_game_row_checks=0,mathematical_objective_complete=False)
    atomic_json(OUT/'plan.json',plan)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',10,'Prepare exact private selected-source package, reuse existing large archives, preserve resolution order and P1; source integrity only, all inline6000 charges preserved')
    reservation=ledger.reserve('assembly',100,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=plan['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=3G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%',
        '--property=TasksMax=64','--property=KillMode=control-group','--property=RuntimeMaxSec=530',
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
