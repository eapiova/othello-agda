"""Bounded read-only search for the exact existing Agda frame encoder parameters."""
import hashlib,json,shutil,subprocess,sys,zipfile,zlib
from pathlib import Path
from compression import zstd
from provenance import source_identity
from run_job import atomic_json,run_job,utc
from study6 import Ledger
import assembly6
import completion_batch6 as batch
import citation_diagnostic6 as common
import big_rows_probe6 as previous

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/mnt/data/othello-agda-desktop-artifacts-20261018')
OUT=BASE/'interface-codec-parameters6-20261018';UNIT='othello6-'+OUT.name+'.service'
previous.OUT=OUT;common.OUT=OUT


def worker():
    import ctypes
    p=json.loads((OUT/'plan.json').read_text());assert common.sha(Path(__file__))==p['helper_sha256']
    library=Path('/nix/store/s7vmxmhkq439cjb7ag9w198p6dk7kl0w-zstd-1.5.7/lib/libzstd.so.1')
    assert common.sha(library)==p['agda_libzstd_sha256']
    lib=ctypes.CDLL(str(library));lib.ZSTD_versionString.restype=ctypes.c_char_p
    lib.ZSTD_compressBound.argtypes=[ctypes.c_size_t];lib.ZSTD_compressBound.restype=ctypes.c_size_t
    lib.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_int];lib.ZSTD_compress.restype=ctypes.c_size_t
    lib.ZSTD_findFrameCompressedSize.argtypes=[ctypes.c_char_p,ctypes.c_size_t];lib.ZSTD_findFrameCompressedSize.restype=ctypes.c_size_t
    lib.ZSTD_isError.argtypes=[ctypes.c_size_t];lib.ZSTD_isError.restype=ctypes.c_uint
    def encode(raw,level):
        cap=lib.ZSTD_compressBound(len(raw));buf=ctypes.create_string_buffer(cap)
        size=lib.ZSTD_compress(buf,cap,raw,len(raw),level);assert not lib.ZSTD_isError(size)
        return buf.raw[:size]
    cases=[];common_levels=None
    for label,cache in p['caches'].items():
        archive=Path(cache['archive']);assert common.sha(archive)==cache['archive_sha256']
        with zipfile.ZipFile(archive) as saved:
            prefix='_build/2.9.0/agda/src/Tests/Text'+label.title()+'Packed6/'
            group=652 if label=='upper' else 686
            for suffix in ['Body'+str(group),'Rows'+str(group),'Group'+str(group)]:
                name=prefix+suffix+'.agdai';raw=saved.read(name);assert len(raw)<4*2**20 and raw[24:28]==bytes.fromhex('28b52ffd')
                payload=zstd.decompress(raw[24:]);assert len(payload)<16*2**20
                candidates={};matches=[]
                for level in range(-10,23):
                    encoded=encode(payload,level)
                    candidates[str(level)]=dict(bytes=len(encoded),frame_prefix_hex=encoded[:12].hex())
                    if encoded==raw[24:]:matches.append(level)
                common_levels=set(matches) if common_levels is None else common_levels & set(matches)
                frame_size=lib.ZSTD_findFrameCompressedSize(raw[24:],len(raw)-24)
                assert not lib.ZSTD_isError(frame_size)
                cases.append(dict(label=label,name=name,original_bytes=len(raw),original_frame_prefix_hex=raw[24:36].hex(),
                    first_frame_compressed_bytes=frame_size,frame_bytes=len(raw)-24,
                    exact_reencoding_levels=matches,candidates=candidates))
    atomic_json(OUT/'report.json',dict(finished_utc=utc(),accepted=True,probe_only=True,cases=cases,
        library=str(library),library_sha256=common.sha(library),library_version=lib.ZSTD_versionString().decode(),
        common_exact_reencoding_levels=sorted(common_levels),original_inputs_unchanged=True,
        no_archives_replaced=True,no_proofs_or_cache_changes=True,full_corpus_codec_not_validated=True,
        mathematical_objective_complete=False))


def supervise():
    job=json.loads((OUT/'job.json').read_text())
    result=run_job(OUT.name,previous.sandbox()+['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'],
        OUT/'records',root=OUT/'control',timeout=100,cpu_limit=30,rss_limit_gib=.8,log_limit_mib=1,
        reservation_id=job['reservation']['reservation_id'],expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if result['accepted'] else 1


def launch():
    batch.authorized();assert not OUT.exists() and not common.disjoint_checkers()
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
        '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    prior=json.loads((BASE/'interface-codec-probe6-20261018/closure.json').read_text())['combined_scope_cpu_seconds']
    assert prior+45<=2000
    legacy=common.storage(0)
    patterns=previous.EXTRA_PATTERNS+['global-upper-layout6-20261018*','step-existing-partial6-20261018*',
        'citation-diagnostic6-20261018*','shared-inline-scaling6-20261018*','text-map-scaling6-20261018*']
    extras={p for pattern in patterns for p in (ROOT/'results').glob(pattern)}
    registry=json.loads((ROOT/'results/study6-external-artifacts-20261018.json').read_text())
    paths=extras|{Path(x['path']) for x in registry['roots'] if Path(x['path'])!=OUT}
    used=legacy['allocated_study_bytes']+sum(batch.allocated(p) for p in paths)
    assert used+8*2**20<12*2**30 and shutil.disk_usage(ROOT).free-2**20>=80*2**30
    caches={n:json.loads((ROOT/f'results/text-{n}-cache-current6-20261018.json').read_text()) for n in ['upper','lower']}
    assert all(c.get('archive_view_replay_accepted',c.get('read_only_view_replay_accepted',False)) for c in caches.values())
    OUT.mkdir();(OUT/'control').mkdir();shutil.copy2(Path(__file__),OUT/'control/worker.py')
    p=dict(created_utc=utc(),control_source=source_identity(OUT/'control'),helper_sha256=common.sha(Path(__file__)),
        caches=caches,prior_allocated_study_bytes=used,previous_combined_scope_cpu_seconds=prior,
        scope_cpu_cap=2000,reservation_cpu_seconds=40,controller_allowance_cpu_seconds=5,
        hard_memory_gib=1,swap_bytes=0,core_bytes=0,own_output_cap_mib=8,retained_study_cap_gib=12,
        root_free_floor_gib=80,python_binary_sha256=common.sha('/usr/bin/python3'),
        agda_libzstd_sha256=common.sha('/nix/store/s7vmxmhkq439cjb7ag9w198p6dk7kl0w-zstd-1.5.7/lib/libzstd.so.1'),
        original_inputs_read_only=True,no_proof_or_cache_changes=True)
    atomic_json(OUT/'plan.json',p)
    ledger=Ledger(ROOT/'results/study6-ledger.json');assert not Ledger.summary(json.loads(ledger.path.read_text()))['outstanding']
    allowance=ledger.withhold('assembly',5,'Bounded exact original Agda frame parameter search using the pinned Agda Nix libzstd; all source/cache bytes remain untouched and all inline2000 consumption is retained')
    reservation=ledger.reserve('assembly',40,OUT.name)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,control_source=p['control_source'],unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=1G','--property=MemorySwapMax=0',
        '--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=64','--property=KillMode=control-group',
        '--property=RuntimeMaxSec=120','--property=WorkingDirectory='+str(OUT/'control'),
        '--property=StandardOutput=append:'+str(OUT/'service.log'),'--property=StandardError=append:'+str(OUT/'service.log'),
        '/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise']
    done=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr));assert done.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation,combined_reserved_scope_cpu_seconds=prior+45)))


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['launch','worker','supervise']
    if sys.argv[1]=='launch':launch()
    elif sys.argv[1]=='worker':worker()
    else:raise SystemExit(supervise())
