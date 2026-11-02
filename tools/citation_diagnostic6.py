"""AI-assisted small safe diagnostic; no full-map import or new coverage."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading

import assembly6
import completion_batch6 as batch
import sparse_citation_pilot6 as sparse
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger

ROOT = batch.ROOT
LABEL = 'citation-diagnostic6-20261018'
OUT = ROOT/'results'/LABEL
CHECK = OUT/'check'
UNIT = 'othello6-'+LABEL+'.service'
PREFIX = 'Tests.CitationDiagnostic6'
DIRECT = False
TARGETS = ['Data','Implicit','Explicit']
PHASE_CPU = 15
PHASE_TIMEOUT = 50
HARD_GIB = 3
OUTER_CPU = 70
RESERVATION_CPU = 80
ALLOWANCE_CPU = 20
RECOVERY = False
FULL = False
INCREMENTAL = False
INDEXED = False
OPAQUE = False
PACKED = False
PACKED_SPLIT = False
FUSED = False
SPECIALIZED = False
DIRECTED = False
SYMMETRY = False
PROFILE_ONLY = False
PROFILE_FLAGS = []
DIRECTED_CODEC = False
SCALING = False
SCALING_FINAL = False
ROW_PACKED = False
PACKED_GAME = False
ARITHMETIC_GAME = False
ARITHMETIC_COLUMNS = False
ARITHMETIC_FINITE = False
ARITHMETIC_FINITE_FIXED = False
ARITHMETIC_STATE_ONLY = False
ARITHMETIC_EVAL = False
STRICT_STATE = False
LENGTH_RAYS = False
UNICODE_CODEC = False
INLINE_ENTRIES = False
ERASED_ARITHMETIC = False
CACHED_STATE = False
CACHED_RECOVERY = False
CACHED_SECOND = False
CONCRETE_LOWER = False
CONCRETE_RECOVERY = False
CONCRETE_BOOLEAN = False
ROW_CACHE = False
ROW_CACHE_RECOVERY = False
ACTION_SUFFIX = ''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def disjoint_checkers():
    """Permit the independently owned NAMOR project; never signal its jobs."""
    allowed=Path('/home/eapiova/projects/modal-positions')
    peers=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdecimal():continue
        try:
            if (proc/'comm').read_text().strip().lower()!='agda':continue
            raw=(proc/'cmdline').read_bytes()
            if not raw:continue
            argv=raw.decode().split('\0')[:-1]
            cwd=(proc/'cwd').resolve()
            executable=Path(argv[0]).absolute()
        except (FileNotFoundError,ProcessLookupError):continue
        assert cwd.is_relative_to(allowed) and executable.is_relative_to(allowed), 'Agda process may share Othello build state'
        assert not any(str(ROOT) in arg or str(batch.full_map.BASE) in arg for arg in argv), 'Othello dependency in peer command'
        peers.append(dict(pid=int(proc.name),cwd=str(cwd),executable=str(executable),project='independent NAMOR'))
    if peers:
        memory=dict((line.split()[0].rstrip(':'),int(line.split()[1])) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
        assert memory['MemAvailable']*1024>=(HARD_GIB+2)*2**30,'host memory headroom insufficient for disjoint checking'
    return peers


def storage(reserve=0):
    old=sparse.storage()
    own=batch.allocated(OUT)
    others=sum(batch.allocated(p) for p in (ROOT/'results').glob('direct-rows-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('full-resolver-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('incremental-rule-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('incremental-indexed-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('packed-nat-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('fused-row-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('specialized-rule-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('directed-move-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('direct-symmetry-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('checker-profile6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('directed-codec-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('directed-scaling6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('row-packed-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('packed-game-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('arithmetic-game-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('arithmetic-columns-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('arithmetic-evaluation-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('strict-state-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('length-rays-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('unicode-codec-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('inline-entries-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('erased-arithmetic-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('cached-game-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('stable-bound-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('memo-reuse-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('margin-policy-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('endgame-cost-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('tt-policy-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('endgame12-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('concrete-lower-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('row-cache-probe6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('endgame16-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('capped-cost-screen6-20261018*') if p!=OUT)
    others+=sum(batch.allocated(p) for p in (ROOT/'results').glob('bounded-layout6-20261018*') if p!=OUT)
    old['allocated_study_bytes']+=others
    assert old['allocated_study_bytes']+own+reserve<12*2**30
    assert own+reserve<=(64 if DIRECT or FULL or INCREMENTAL else 16)*2**20 and shutil.disk_usage(ROOT).free-reserve>=80*2**30
    return dict(allocated_study_bytes=old['allocated_study_bytes']+own,
                free_bytes=shutil.disk_usage(ROOT).free,new_artifact_bytes=own,
                reserved_bytes=reserve,checked_utc=utc())


@contextlib.contextmanager
def watched():
    group=Path('/sys/fs/cgroup')/next(x[3:] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::')).lstrip('/')
    assert (group/'memory.max').read_text().strip()==str(HARD_GIB*2**30)
    assert (group/'memory.swap.max').read_text().strip()=='0'
    stop=threading.Event();errors=[]
    def watch():
        while not stop.wait(3):
            try:
                atomic_json(OUT/'storage.json',storage(8*2**20))
                cpu=dict(x.split() for x in (group/'cpu.stat').read_text().splitlines())
                assert int(cpu['usage_usec'])/1e6<RESERVATION_CPU-20,'service CPU guard'
                available=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
                assert available>=2*2**30,'host memory headroom guard'
            except BaseException as error:
                errors.append(str(error));atomic_json(OUT/'resource-stop.json',dict(reason=str(error),finished_utc=utc()))
                os.kill(os.getpid(),signal.SIGTERM);return
    thread=threading.Thread(target=watch,daemon=True);thread.start()
    try:yield
    finally:stop.set();thread.join()
    assert not errors,'resource watcher interrupted probe'


def layout():
    if ROW_CACHE:
        from row_cache_probe6 import emit
        return emit(CHECK)
    if CONCRETE_BOOLEAN:
        from concrete_boolean_probe6 import emit
        return emit(CHECK)
    if CONCRETE_LOWER:
        from concrete_lower_probe6 import emit
        return emit(CHECK)
    if CACHED_STATE:
        from cached_game_probe6 import emit
        return emit(CHECK)
    if ERASED_ARITHMETIC:
        from erased_arithmetic_probe6 import emit
        return emit(CHECK)
    if INLINE_ENTRIES:
        from inline_probe6 import emit
        return emit(CHECK)
    if UNICODE_CODEC:
        from unicode_codec_probe6 import emit
        return emit(CHECK)
    if LENGTH_RAYS:
        from length_probe6 import emit
        return emit(CHECK)
    if STRICT_STATE:
        from strict_packed_probe6 import emit
        return emit(CHECK)
    if ARITHMETIC_GAME:
        from arithmetic_game_probe6 import emit
        return emit(CHECK,finite=ARITHMETIC_FINITE)
    if PACKED_GAME:
        from packed_game_probe6 import emit
        return emit(CHECK)
    if ROW_PACKED:
        from row_packed_probe6 import emit
        return emit(CHECK)
    if SCALING:
        from directed_scaling6 import emit
        return emit(CHECK,recovery=RECOVERY)
    if DIRECTED_CODEC:
        from directed_codec_probe6 import emit
        return emit(CHECK)
    if PROFILE_ONLY:
        from checker_profile6 import emit
        return emit(CHECK)
    if SYMMETRY:
        from symmetry_probe6 import emit
        return emit(CHECK)
    if DIRECTED:
        from directed_probe6 import emit
        return emit(CHECK)
    if SPECIALIZED:
        from specialized_probe6 import emit
        return emit(CHECK, PREFIX)
    if FUSED:
        from incremental_indexed_probe6 import emit
        return emit(CHECK,prefix='Tests.FusedRowFixed6' if RECOVERY else 'Tests.FusedRowProbe6',fused=True,skip_core=RECOVERY)
    if PACKED_SPLIT:
        from packed_split_probe6 import emit
        return emit(CHECK)
    if PACKED:
        from packed_nat_probe6 import emit
        return emit(CHECK)
    if INDEXED:
        from incremental_indexed_probe6 import emit
        return emit(CHECK,prefix='Tests.IncrementalOpaqueProbe6',split=True) if OPAQUE else emit(CHECK)
    if INCREMENTAL:
        from incremental_probe6 import emit
        return emit(CHECK)
    if FULL:
        from full_resolver_probe6 import emit
        return emit(CHECK,PREFIX)
    if DIRECT:
        from direct_rows_probe6 import emit
        return emit(CHECK,PREFIX)
    CHECK.mkdir(parents=True)
    folder=CHECK/'src/Tests/CitationDiagnostic6';folder.mkdir(parents=True)
    shared=sparse.COMMON+'''import Tests.CompletionBatchLowerA6.Rows342.Part342 as Original
'''
    data=shared+'''s : B.Vec (State six) 1
s = Lazy.states 1 "bQPEQ8QQQQQQQ"
abstract
  hit : M.lookup Original.demand 6752 ≡ just (B.lookupVec s B.fzero)
  hit = refl
'''
    for name,body in [('Data',data)]+[(name,shared+f'''open import {PREFIX}.Data
aligned : ∀ G → Laws.Aligned Original.demand G → Laws.Aligned (M.rows 6752 1 s) G
aligned G same B.fzero =
  Laws.aligned-compatible {{map = Original.demand}} {explicit} same 6752 _ hit
aligned G same (B.fsuc ())
''') for name,explicit in [('Implicit',''),('Explicit','{G = G}')]]:
        (folder/(name+'.agda')).write_text(sparse.HEADER+'-- AI-assisted safe diagnostic; no new row coverage.\nmodule '+PREFIX+'.'+name+' where\n\n'+body)
    (CHECK/'othello.agda-lib').write_bytes((ROOT/'othello.agda-lib').read_bytes())
    return source_identity(CHECK)


def worker():
    batch.authorized()
    plan=json.loads((OUT/'plan.json').read_text())
    assert all(sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items())
    expected={Path(p):tuple(pin) for p,pin in plan['donors'].items()}
    with contextlib.ExitStack() as stack:
        for path in sorted(expected):
            lock=stack.enter_context((path/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stack.enter_context(watched())
        before=batch.donor_snapshot(expected)
        stack.enter_context(build_lock(CHECK))
        assert source_identity(CHECK)==plan['source'] and not assembly6.interfaces(CHECK)
        results={}
        for target in TARGETS:
            storage(8*2**20)
            assert shutil.disk_usage(ROOT).free-8*2**20>=80*2**30
            argv=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(CHECK),str(CHECK),
                  '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--',
                  batch.full_map.AGDA,'--no-libraries','-i','src']
            for path in expected:argv+=['-i',str(path/'src')]
            argv+=(PROFILE_FLAGS if PROFILE_ONLY else ['--profile=modules'])+['--safe','--without-K','--cubical-compatible','--save-metas',
                   'src/'+(PREFIX.replace('.','/')+'/' if PREFIX else '')+target+'.agda','+RTS','-M1G' if OPAQUE or PACKED else ('-M2G' if INDEXED else ('-M10G' if FULL else ('-M4G' if DIRECT or INCREMENTAL else '-M2G'))),'-s','-RTS']
            record=run_job(target.replace('/','-').lower(),argv,OUT/'records',root=CHECK,timeout=PHASE_TIMEOUT,cpu_limit=PHASE_CPU,
                rss_limit_gib=HARD_GIB-.25,log_limit_mib=2,expected_source_sha256=plan['source']['source_sha256'],
                metadata=dict(checker_binary_sha256=batch.full_map.AGDA_SHA,diagnostic_only=True,
                              native_search_allowed=False,production_authorized=False))
            results[target]={k:record[k] for k in ['accepted','exit_code','cpu_seconds','wall_seconds','stop_reason','peak_rss_gib']}
            atomic_json(OUT/'phase-summary.json',results)
            if SCALING and record['accepted'] and (target.endswith('/Training') or target.endswith('/Holdout')):
                from directed_scaling6 import summarize
                summarize(OUT,'training' if target.endswith('Training') else 'holdout')
            # Failed parsing/state identity would invalidate both inference comparisons.
            if not record['accepted'] and (DIRECT or FULL or INCREMENTAL or target=='Data'):break
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        intact=batch.donor_snapshot(expected)==before
        p1=all(sha(ROOT/n)==h for n,h in history['p1_files'].items())
        assert intact and p1 and source_identity(CHECK)==plan['source']
        complete=all(t in results and results[t]['accepted'] for t in TARGETS)
        atomic_json(OUT/'report.json',dict(format='othello-packed-nat-probe6-v1' if PACKED else ('othello-incremental-indexed-probe6-v1' if INDEXED else ('othello-incremental-rule-probe6-v1' if INCREMENTAL else ('othello-full-resolver-probe6-v1' if FULL else ('othello-direct-row-probe6-v1' if DIRECT else 'othello-citation-diagnostic6-v1')))),phases=results,
            accepted_donors_unchanged=intact,p1_unchanged=p1,new_distinct_rows=0,
            all_phases_accepted=complete,conditional_partial_rows=200 if DIRECT and complete else 0,
            semantic_shared_map_rows=400 if FULL and complete else 0,
            arbitrary_board_rule_agreement_checked=INCREMENTAL and any(results.get(t,{}).get('accepted') for t in ['Othello/Incremental6','Othello/Specialized6']),
            original_conditional_partial_rows=200 if INDEXED and complete and not DIRECTED else 0,
            directed_conditional_tree_rows=(1600 if SCALING else 200) if DIRECTED and complete and not CONCRETE_BOOLEAN else 0,
            boolean_only_existing_rows=200 if CONCRETE_BOOLEAN and complete else 0,
            packed_conditional_partial_rows=200 if PACKED and complete else 0,
            storage=storage(),mathematical_objective_complete=False,finished_utc=utc()))
        if DIRECT or FULL or INCREMENTAL:assert complete,'probe failed; retain exact partial receipts'


def supervise():
    batch.authorized()
    job=json.loads((OUT/'job.json').read_text())
    assert not (OUT/'records'/(LABEL+'.json')).exists()
    r=run_job(LABEL,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker'+ACTION_SUFFIX if ACTION_SUFFIX else (('worker-fused-fixed' if RECOVERY else 'worker-fused') if FUSED else (('worker-packed-split' if PACKED_SPLIT else 'worker-packed') if PACKED else (('worker-incremental-indexed-opaque' if OPAQUE else ('worker-incremental-indexed-fixed' if RECOVERY else 'worker-incremental-indexed')) if INDEXED else ('worker-incremental' if INCREMENTAL else ('worker-full' if FULL else ('worker-direct-fixed' if RECOVERY else ('worker-direct' if DIRECT else 'worker')))))))],
        OUT/'records',root=OUT/'control',timeout=1700 if FULL else (800 if DIRECT or INCREMENTAL else 220),cpu_limit=OUTER_CPU,rss_limit_gib=HARD_GIB-.1,
        log_limit_mib=2,reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    return 0 if r['accepted'] else 1


def launch():
    batch.authorized()
    assert not OUT.exists() and sha(batch.full_map.AGDA)==batch.full_map.AGDA_SHA
    assert not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
           '--type=service','--no-legend','--plain','othello*'],text=True).strip()
    peers=disjoint_checkers()
    storage(16*2**20)
    expected=sparse.donors()
    if PACKED:
        for label in ['sparse-citation-pilot6-20261018-fixed','direct-rows-probe6-20261018-fixed']:
            previous=ROOT/'results'/label
            spec=json.loads((previous/'plan.json').read_text())
            if label.startswith('sparse-'):
                assert json.loads((previous/'semantic-scope-audit.json').read_text())['accepted']
                source_pin=spec['layout']['source']['source_sha256']
            else:
                assert json.loads((previous/'report.json').read_text())['all_phases_accepted']
                source_pin=spec['source']['source_sha256']
            expected[previous/'check']=(source_pin,batch.digest_entries(json.loads((previous/'interfaces.json').read_text())))
        if PACKED_SPLIT:
            previous=ROOT/'results/packed-nat-probe6-20261018'
            assert json.loads((previous/'report.json').read_text())['all_phases_accepted']
            expected[previous/'check']=(json.loads((previous/'plan.json').read_text())['source']['source_sha256'],
                batch.digest_entries(json.loads((previous/'interfaces.json').read_text())))
    if INDEXED:
        for label in ['sparse-citation-pilot6-20261018-fixed','full-resolver-probe6-20261018','incremental-rule-probe6-20261018']:
            previous=ROOT/'results'/label
            spec=json.loads((previous/'plan.json').read_text())
            if label.startswith('sparse-'):
                assert json.loads((previous/'semantic-scope-audit.json').read_text())['accepted']
                source_pin=spec['layout']['source']['source_sha256']
            else:
                assert json.loads((previous/'report.json').read_text())['all_phases_accepted']
                source_pin=spec['source']['source_sha256']
            expected[previous/'check']=(source_pin,batch.digest_entries(json.loads((previous/'interfaces.json').read_text())))
        if FUSED:
            for label in ['packed-nat-probe6-20261018','packed-nat-probe6-20261018-split']:
                previous=ROOT/'results'/label
                assert json.loads((previous/'report.json').read_text())['all_phases_accepted']
                expected[previous/'check']=(json.loads((previous/'plan.json').read_text())['source']['source_sha256'],
                    batch.digest_entries(json.loads((previous/'interfaces.json').read_text())))
            if RECOVERY or SPECIALIZED or DIRECTED:
                previous=ROOT/'results/fused-row-probe6-20261018'
                closure=json.loads((previous/'closure.json').read_text())
                assert closure['reusable_checked_core_modules']==['Game.IndexedTransfer','Othello.IncrementalIndexed6']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if DIRECTED:
                previous=ROOT/'results/specialized-rule-probe6-20261018-fixed'
                closure=json.loads((previous/'closure.json').read_text())
                assert closure['accepted'] and closure['arbitrary_board_rule_agreement_checked']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if SYMMETRY:
                previous=ROOT/'results/directed-move-probe6-20261018-fixed'
                closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if PROFILE_ONLY or DIRECTED_CODEC or ROW_PACKED:
                previous=ROOT/'results/direct-symmetry-probe6-20261018'
                closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if PACKED_GAME or LENGTH_RAYS:
                previous=ROOT/'results/row-packed-probe6-20261018-fixed'
                closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if UNICODE_CODEC or INLINE_ENTRIES:
                for label in ['length-rays-probe6-20261018','directed-codec-probe6-20261018-fixed']:
                    previous=ROOT/'results'/label
                    closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                    expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if INLINE_ENTRIES:
                previous=ROOT/'results/unicode-codec-probe6-20261018'
                closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if STRICT_STATE:
                previous=ROOT/'results/packed-game-probe6-20261018'
                closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if ERASED_ARITHMETIC or ROW_CACHE:
                previous=ROOT/'results/arithmetic-evaluation-probe6-20261018'
                closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if CACHED_STATE or CONCRETE_LOWER or ROW_CACHE:
                for label in ['inline-entries-probe6-20261018','erased-arithmetic-probe6-20261018']:
                    previous=ROOT/'results'/label
                    closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                    expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
            if SCALING:
                for label in ['direct-symmetry-probe6-20261018','directed-codec-probe6-20261018-fixed']:
                    previous=ROOT/'results'/label
                    closure=json.loads((previous/'closure.json').read_text());assert closure['accepted']
                    expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
                if RECOVERY:
                    previous=ROOT/'results/directed-scaling6-20261018'
                    closure=json.loads((previous/'closure.json').read_text())
                    assert not closure['accepted'] and closure['training_accepted'] and closure['reusable_interfaces']==22
                    expected[previous/'check']=(closure['source_sha256'],closure['interface_pool_sha256'])
    if DIRECT:
        from direct_rows_probe6 import FIXED
        donor=ROOT/FIXED/'check'
        assert json.loads((ROOT/FIXED/'semantic-scope-audit.json').read_text())['accepted']
        assert json.loads((ROOT/FIXED/'report.json').read_text())['record']['accepted']
        expected[donor]=(json.loads((ROOT/FIXED/'plan.json').read_text())['layout']['source']['source_sha256'],
                         batch.digest_entries(json.loads((ROOT/FIXED/'interfaces.json').read_text())))
    source=layout()
    helpers=sorted(set(batch.HELPERS+['sparse_citation_pilot6.py','citation_diagnostic6.py','full_map_pilot6.py']
                       +(['direct_rows_probe6.py','compact_shared6.py'] if DIRECT else [])
                       +(['full_resolver_probe6.py','full_map_alignment6.py'] if FULL else [])
                       +(['incremental_probe6.py','ref.py','bench6.py','compact_shared6.py'] if INCREMENTAL else [])))
    if INDEXED:helpers.append('incremental_indexed_probe6.py')
    if PACKED:helpers.append('packed_nat_probe6.py')
    if PACKED_SPLIT:helpers.append('packed_split_probe6.py')
    if SPECIALIZED:helpers+=['specialized_probe6.py','specialized_source6.py']
    if DIRECTED:helpers+=['directed_probe6.py','direct_moves_source6.py','direct_rows_probe6.py']
    if SYMMETRY:helpers+=['symmetry_probe6.py','symmetry_source6.py']
    if PROFILE_ONLY:helpers+=['checker_profile6.py']
    if DIRECTED_CODEC:helpers+=['directed_codec_probe6.py','directed_codec_source6.py']
    if SCALING:helpers+=['directed_scaling6.py']
    if ROW_PACKED:helpers+=['row_packed_probe6.py','row_packed_source6.py','encoded_resolver_source6.py']
    if PACKED_GAME:helpers+=['packed_game_probe6.py']
    if ARITHMETIC_GAME:helpers+=['arithmetic_game_probe6.py','row_arithmetic_source6.py']
    if ARITHMETIC_COLUMNS:helpers+=['row_arithmetic_column_source6.py']
    if ARITHMETIC_FINITE:helpers+=['row_arithmetic_finite_source6.py']
    if STRICT_STATE:helpers+=['strict_packed_probe6.py']
    if LENGTH_RAYS:helpers+=['length_probe6.py','length_rules_source6.py','length_rays_source6.py']
    if UNICODE_CODEC:helpers+=['unicode_codec_probe6.py','unicode_codec_source6.py']
    if INLINE_ENTRIES:helpers+=['inline_probe6.py','inline_entries_source6.py']
    if ERASED_ARITHMETIC:helpers+=['erased_arithmetic_probe6.py','erased_arithmetic_source6.py']
    if CACHED_STATE:helpers+=['cached_game_probe6.py','cached_game_source6.py']
    if CONCRETE_LOWER:helpers+=['concrete_lower_probe6.py','concrete_lower_source6.py']
    if CONCRETE_BOOLEAN:helpers+=['concrete_boolean_probe6.py']
    if ROW_CACHE:helpers+=['row_cache_probe6.py']
    atomic_json(OUT/'plan.json',dict(source=source,donors={str(p):pin for p,pin in expected.items()},
        helper_sha256={n:sha(ROOT/'tools'/n) for n in helpers},authorization_sha256=sha(batch.AUTH),
        kernel_reservation_seconds=RESERVATION_CPU,assembly_allowance_seconds=ALLOWANCE_CPU,
        scope_cpu_cap_seconds=RESERVATION_CPU+ALLOWANCE_CPU,
        hard_memory_gib=HARD_GIB,swap_bytes=0,free_disk_floor_gib=80,study_artifact_cap_gib=12,
        targets=TARGETS,phase_cpu_seconds=PHASE_CPU,phase_timeout_seconds=PHASE_TIMEOUT,
        disjoint_agda_at_launch=peers,shared_build_state_allowed=False,
        production_authorized=False,created_utc=utc()))
    control=OUT/'control';control.mkdir();shutil.copy2(Path(__file__),control/'worker.py')
    ledger=Ledger(ROOT/'results/study6-ledger.json')
    summary=Ledger.summary(json.loads(ledger.path.read_text()))
    assert not summary['outstanding']
    if RECOVERY:
        earlier=ROOT/'results'/('arithmetic-columns-probe6-20261018' if ARITHMETIC_FINITE else ('arithmetic-game-probe6-20261018' if ARITHMETIC_GAME else ('row-packed-probe6-20261018' if ROW_PACKED else ('directed-scaling6-20261018' if SCALING else ('directed-codec-probe6-20261018' if DIRECTED_CODEC else ('checker-profile6-20261018' if PROFILE_ONLY else ('directed-move-probe6-20261018' if DIRECTED else ('specialized-rule-probe6-20261018' if SPECIALIZED else ('fused-row-probe6-20261018' if FUSED else ('incremental-indexed-probe6-20261018' if INDEXED else 'direct-rows-probe6-20261018'))))))))))
        if CACHED_RECOVERY:earlier=ROOT/'results/cached-game-probe6-20261018'
        if CONCRETE_RECOVERY:earlier=ROOT/'results/concrete-lower-probe6-20261018'
        if ROW_CACHE_RECOVERY:earlier=ROOT/'results/row-cache-probe6-20261018'
        previous=json.loads((earlier/'closure.json').read_text())
        if ARITHMETIC_FINITE_FIXED:
            extra=json.loads((ROOT/'results/arithmetic-columns-probe6-20261018-finite/closure.json').read_text())
            additional=(json.loads((ROOT/'results/arithmetic-columns-probe6-20261018-finite-fixed/closure.json').read_text())['charged_cpu_seconds'] if ARITHMETIC_STATE_ONLY else 0)
            assert previous['charged_cpu_seconds']+extra['charged_cpu_seconds']+additional+RESERVATION_CPU+20<=200
        scope_cap=200 if ARITHMETIC_FINITE else (100 if PROFILE_ONLY else (320 if SPECIALIZED or DIRECTED else 220))
        if CACHED_RECOVERY or ROW_CACHE_RECOVERY:scope_cap=200
        if CONCRETE_RECOVERY:scope_cap=140
        if CONCRETE_BOOLEAN:
            failed=json.loads((ROOT/'results/concrete-lower-probe6-20261018-fixed/closure.json').read_text())
            assert not failed['accepted']
            assert previous['charged_cpu_seconds']+failed['charged_cpu_seconds']+RESERVATION_CPU+20<=scope_cap
        if CACHED_SECOND:
            others=[json.loads((ROOT/'results'/('cached-game-probe6-20261018-fixed'+(str(n) if n>1 else ''))/'closure.json').read_text()) for n in range(1,CACHED_SECOND)]
            assert all(not p['accepted'] for p in others)
            assert previous['charged_cpu_seconds']+sum(p['charged_cpu_seconds'] for p in others)+RESERVATION_CPU+20<=scope_cap
        assert not previous['accepted'] and previous['charged_cpu_seconds']+RESERVATION_CPU+20<=scope_cap
        if SCALING_FINAL:
            second=json.loads((ROOT/'results/directed-scaling6-20261018-fixed/closure.json').read_text())
            assert not second['accepted'] and not second['heldout_checked']
            assert previous['charged_cpu_seconds']+second['charged_cpu_seconds']+RESERVATION_CPU+20<=scope_cap
        allowance=dict(reused_from=str(earlier/'job.json'),original=json.loads((earlier/'job.json').read_text())['control_allowance'],
                       additional_withholding_seconds=0,combined_scope_cpu_cap_seconds=scope_cap)
    else:
        allowance=ledger.withhold('assembly',ALLOWANCE_CPU,'Continuing completion6: conservative preparation/audit/supervision allowance for '+LABEL+'; no additional budget.')
    reservation=ledger.reserve('kernel',RESERVATION_CPU,LABEL)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=source_identity(control),unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax='+str(HARD_GIB)+'G',
        '--property=MemorySwapMax=0','--property=LimitCORE=0','--property=CPUQuota=100%','--property=TasksMax=128',
        '--property=KillMode=control-group','--property=RuntimeMaxSec='+str(1800 if FULL else (840 if DIRECT or INCREMENTAL else 240)),'--property=TimeoutStopSec=10',
        '--property=WorkingDirectory='+str(control),'--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise'+ACTION_SUFFIX if ACTION_SUFFIX else (('supervise-fused-fixed' if RECOVERY else 'supervise-fused') if FUSED else (('supervise-packed-split' if PACKED_SPLIT else 'supervise-packed') if PACKED else (('supervise-incremental-indexed-opaque' if OPAQUE else ('supervise-incremental-indexed-fixed' if RECOVERY else 'supervise-incremental-indexed')) if INDEXED else ('supervise-incremental' if INCREMENTAL else ('supervise-full' if FULL else ('supervise-direct-fixed' if RECOVERY else ('supervise-direct' if DIRECT else 'supervise')))))))]
    response=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=response.returncode,stdout=response.stdout,
        stderr=response.stderr,submitted_utc=utc()))
    assert response.returncode==0
    print(json.dumps(dict(unit=UNIT,reservation=reservation)))


if __name__=='__main__':
    os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['GIT_OPTIONAL_LOCKS']='0'
    assert len(sys.argv)==2 and sys.argv[1] in ('launch-row-cache-fixed','worker-row-cache-fixed','supervise-row-cache-fixed','launch-row-cache','worker-row-cache','supervise-row-cache')+('launch-concrete-boolean','worker-concrete-boolean','supervise-concrete-boolean','launch-concrete-fixed','worker-concrete-fixed','supervise-concrete-fixed','launch-concrete','worker-concrete','supervise-concrete')+tuple(a+'-cached-fixed'+str(n) for a in ['launch','worker','supervise'] for n in range(3,7))+('launch-cached-fixed2','worker-cached-fixed2','supervise-cached-fixed2','launch-cached-fixed','worker-cached-fixed','supervise-cached-fixed','launch-cached','worker-cached','supervise-cached','launch-erased','worker-erased','supervise-erased','launch-inline','worker-inline','supervise-inline','launch-unicode','worker-unicode','supervise-unicode','launch-length','worker-length','supervise-length','launch-strict','worker-strict','supervise-strict','launch-arithmetic-eval','worker-arithmetic-eval','supervise-arithmetic-eval','launch-arithmetic-state','worker-arithmetic-state','supervise-arithmetic-state','launch-arithmetic-finite-fixed','worker-arithmetic-finite-fixed','supervise-arithmetic-finite-fixed','launch-arithmetic-finite','worker-arithmetic-finite','supervise-arithmetic-finite','launch-arithmetic-columns','worker-arithmetic-columns','supervise-arithmetic-columns','launch-arithmetic-game-fixed','worker-arithmetic-game-fixed','supervise-arithmetic-game-fixed','launch-arithmetic-game','worker-arithmetic-game','supervise-arithmetic-game','launch-packed-game','worker-packed-game','supervise-packed-game','launch-row-packed-fixed','worker-row-packed-fixed','supervise-row-packed-fixed','launch-row-packed','worker-row-packed','supervise-row-packed','launch-scaling-final','worker-scaling-final','supervise-scaling-final','launch-scaling-fixed','worker-scaling-fixed','supervise-scaling-fixed','launch-scaling','worker-scaling','supervise-scaling','launch-codec','worker-codec','supervise-codec','launch-codec-fixed','worker-codec-fixed','supervise-codec-fixed','launch-profile-fixed','worker-profile-fixed','supervise-profile-fixed','launch-profile','worker-profile','supervise-profile','launch-symmetry','worker-symmetry','supervise-symmetry','launch-directed','worker-directed','supervise-directed','launch-directed-fixed','worker-directed-fixed','supervise-directed-fixed','launch-specialized-fixed','supervise-specialized-fixed','worker-specialized-fixed','launch-specialized','supervise-specialized','worker-specialized','launch','supervise','worker','launch-direct','supervise-direct','worker-direct','launch-direct-fixed','supervise-direct-fixed','worker-direct-fixed','launch-full','supervise-full','worker-full','launch-incremental','supervise-incremental','worker-incremental','launch-incremental-indexed','supervise-incremental-indexed','worker-incremental-indexed','launch-incremental-indexed-fixed','supervise-incremental-indexed-fixed','worker-incremental-indexed-fixed','launch-incremental-indexed-opaque','supervise-incremental-indexed-opaque','worker-incremental-indexed-opaque','launch-packed','supervise-packed','worker-packed','launch-packed-split','supervise-packed-split','worker-packed-split','launch-fused','supervise-fused','worker-fused','launch-fused-fixed','supervise-fused-fixed','worker-fused-fixed')
    action=sys.argv[1]
    if action.endswith('-row-cache-fixed'):
        ROW_CACHE_RECOVERY=RECOVERY=True
        action=action[:-6]
    if action.endswith('-row-cache'):
        ROW_CACHE=INLINE_ENTRIES=LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-row-cache'
        LABEL='row-cache-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/CachedRow6','Othello/RowCacheState6','Othello/RowCacheGame6','Othello/RowCacheRows6','Tests/RowCacheProbe6/Baseline','Tests/RowCacheProbe6/Variant','Tests/RowCacheProbe6/Compact']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=160
        RESERVATION_CPU=180
        ALLOWANCE_CPU=20
        if ROW_CACHE_RECOVERY:
            ACTION_SUFFIX='-row-cache-fixed'
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            RESERVATION_CPU=165
            OUTER_CPU=140
        action=action[:-10]
    if action.endswith('-arithmetic-eval'):
        ARITHMETIC_EVAL=ARITHMETIC_FINITE=True
        action=action[:-16]+'-arithmetic-game'
    if action.endswith('-arithmetic-state'):
        ARITHMETIC_STATE_ONLY=True
        action=action[:-17]+'-arithmetic-finite-fixed'
    if action.endswith('-arithmetic-finite-fixed'):
        ARITHMETIC_FINITE_FIXED=True
        action=action[:-6]
    if action.endswith('-arithmetic-finite'):
        ARITHMETIC_FINITE=ARITHMETIC_COLUMNS=RECOVERY=True
        action=action[:-18]+'-arithmetic-game'
    if action.endswith('-arithmetic-columns'):
        ARITHMETIC_COLUMNS=True
        action=action[:-19]+'-arithmetic-game'
    if action.endswith('-arithmetic-game-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-row-packed-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-scaling-final'):
        RECOVERY=True
        SCALING_FINAL=True
        action=action[:-6]
    if action.endswith('-scaling-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-codec-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-profile-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-directed-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-specialized-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-specialized'):
        SPECIALIZED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-specialized'
        LABEL='specialized-rule-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/CellRays6','Othello/Specialized6','Othello/AgreedIndexed6','Tests/SpecializedProbe6/Baseline','Tests/SpecializedProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=300
        ALLOWANCE_CPU=20
        if RECOVERY:
            ACTION_SUFFIX='-specialized-fixed'
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            RESERVATION_CPU=280
        action=action[:-12]
    if action.endswith('-directed'):
        DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-directed-fixed' if RECOVERY else '-directed'
        LABEL='directed-move-probe6-20261018'+('-fixed' if RECOVERY else '')
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Game/DirectedIndexed','Othello/DirectMoves6','Othello/DirectedRows6','Tests/DirectedProbe6/Data','Tests/DirectedProbe6/Baseline','Tests/DirectedProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=280 if RECOVERY else 300
        ALLOWANCE_CPU=20
        action=action[:-9]
    if action.endswith('-symmetry'):
        SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-symmetry'
        LABEL='direct-symmetry-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/DirectSymmetry6','Tests/DirectSymmetryProbe6/Baseline','Tests/DirectSymmetryProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=160
        RESERVATION_CPU=200
        ALLOWANCE_CPU=20
        action=action[:-9]
    if action.endswith('-profile'):
        PROFILE_ONLY=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        PROFILE_FLAGS=['--profile=internal']
        ACTION_SUFFIX='-profile-fixed' if RECOVERY else '-profile'
        LABEL='checker-profile6-20261018'+('-fixed' if RECOVERY else '')
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Tests/CheckerProfile6/Root']
        PHASE_CPU=35
        PHASE_TIMEOUT=90
        HARD_GIB=4
        OUTER_CPU=60
        RESERVATION_CPU=70 if RECOVERY else 80
        ALLOWANCE_CPU=20
        action=action[:-8]
    if action.endswith('-codec'):
        DIRECTED_CODEC=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-codec-fixed' if RECOVERY else '-codec'
        LABEL='directed-codec-probe6-20261018'+('-fixed' if RECOVERY else '')
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/DirectedCompact6','Tests/DirectedCodecProbe6/Data','Tests/DirectedCodecProbe6/Baseline','Tests/DirectedCodecProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=280 if RECOVERY else 300
        ALLOWANCE_CPU=20
        action=action[:-6]
    if action.endswith('-scaling'):
        SCALING=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-scaling-final' if SCALING_FINAL else ('-scaling-fixed' if RECOVERY else '-scaling')
        LABEL='directed-scaling6-20261018'+('-final' if SCALING_FINAL else ('-fixed' if RECOVERY else ''))
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Tests/DirectedScalingFixed6/Holdout'] if RECOVERY else ['Othello/DirectedParts6','Tests/DirectedScaling6/Training','Tests/DirectedScaling6/Holdout']
        PHASE_CPU=100
        PHASE_TIMEOUT=280
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=250 if RECOVERY else 300
        ALLOWANCE_CPU=20
        action=action[:-8]
    if action.endswith('-arithmetic-game'):
        ARITHMETIC_GAME=PACKED_GAME=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-arithmetic-game-fixed' if RECOVERY else '-arithmetic-game'
        LABEL='arithmetic-game-probe6-20261018'+('-fixed' if RECOVERY else '')
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Game/BooleanUIP','Othello/ArithmeticState6','Othello/ArithmeticGame6','Othello/ArithmeticRows6','Tests/ArithmeticGameProbe6/RefData','Tests/ArithmeticGameProbe6/Baseline','Tests/ArithmeticGameProbe6/Variant']
        PHASE_CPU=180
        PHASE_TIMEOUT=360
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=300
        ALLOWANCE_CPU=20
        if RECOVERY:RESERVATION_CPU=280
        if ARITHMETIC_COLUMNS:
            ACTION_SUFFIX='-arithmetic-columns'
            LABEL='arithmetic-columns-probe6-20261018'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            PHASE_CPU=90
            PHASE_TIMEOUT=200
            OUTER_CPU=160
            RESERVATION_CPU=180
        if ARITHMETIC_FINITE:
            ACTION_SUFFIX='-arithmetic-finite'
            LABEL='arithmetic-columns-probe6-20261018-finite'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            TARGETS=['Game/BooleanUIP','Othello/ArithmeticState6']
            PHASE_CPU=12
            PHASE_TIMEOUT=40
            OUTER_CPU=22
            RESERVATION_CPU=40
            if ARITHMETIC_FINITE_FIXED:
                ACTION_SUFFIX='-arithmetic-finite-fixed'
                LABEL+='-fixed'
                OUT=ROOT/'results'/LABEL
                CHECK=OUT/'check'
                UNIT='othello6-'+LABEL+'.service'
                TARGETS=['Game/BooleanUIP','Othello/ArithmeticState6','Othello/ArithmeticGame6','Othello/ArithmeticRows6','Tests/ArithmeticGameProbe6/RefData']
            if ARITHMETIC_STATE_ONLY:
                ACTION_SUFFIX='-arithmetic-state'
                LABEL='arithmetic-columns-probe6-20261018-state'
                OUT=ROOT/'results'/LABEL
                CHECK=OUT/'check'
                UNIT='othello6-'+LABEL+'.service'
                TARGETS=['Game/BooleanUIP','Othello/ArithmeticState6']
                OUTER_CPU=16
                RESERVATION_CPU=32
        if ARITHMETIC_EVAL:
            ACTION_SUFFIX='-arithmetic-eval'
            LABEL='arithmetic-evaluation-probe6-20261018'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            TARGETS=['Game/BooleanUIP','Othello/ArithmeticState6','Othello/ArithmeticGame6','Othello/ArithmeticRows6','Tests/ArithmeticGameProbe6/RefData','Tests/ArithmeticGameProbe6/Baseline','Tests/ArithmeticGameProbe6/Variant']
            PHASE_CPU=35
            PHASE_TIMEOUT=120
            OUTER_CPU=160
            RESERVATION_CPU=180
        action=action[:-16]
    if action.endswith('-concrete-boolean'):
        CONCRETE_BOOLEAN=CONCRETE_RECOVERY=RECOVERY=True
        action=action[:-8]+'-fixed'
    if action.endswith('-concrete-fixed'):
        CONCRETE_RECOVERY=RECOVERY=True
        action=action[:-6]
    if action.endswith('-concrete'):
        CONCRETE_LOWER=INLINE_ENTRIES=LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-concrete'
        LABEL='concrete-lower-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/ConcreteLowerChecker6','Othello/ConcreteLowerRows6','Tests/ConcreteLowerProbe6/Baseline','Tests/ConcreteLowerProbe6/Variant','Tests/ConcreteLowerProbe6/Compact']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=100
        RESERVATION_CPU=120
        ALLOWANCE_CPU=20
        if CONCRETE_RECOVERY:
            ACTION_SUFFIX='-concrete-fixed'
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            TARGETS=TARGETS[:-1]
            PHASE_CPU=15
            OUTER_CPU=48
            RESERVATION_CPU=68
            if CONCRETE_BOOLEAN:
                ACTION_SUFFIX='-concrete-boolean'
                LABEL='concrete-lower-probe6-20261018-boolean'
                OUT=ROOT/'results'/LABEL
                CHECK=OUT/'check'
                UNIT='othello6-'+LABEL+'.service'
                TARGETS=['Tests/ConcreteBooleanProbe6/Compare']
                PHASE_CPU=15
                OUTER_CPU=24
                RESERVATION_CPU=44
        action=action[:-9]
    if '-cached-fixed' in action and action.rsplit('-cached-fixed',1)[1].isdigit():
        CACHED_SECOND=int(action.rsplit('-cached-fixed',1)[1])
        action=action.rsplit('-cached-fixed',1)[0]+'-cached-fixed'
    if action.endswith('-cached-fixed2'):
        CACHED_SECOND=True
        action=action[:-1]
    if action.endswith('-cached-fixed'):
        CACHED_RECOVERY=RECOVERY=True
        action=action[:-6]
    if action.endswith('-cached'):
        CACHED_STATE=INLINE_ENTRIES=LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-cached'
        LABEL='cached-game-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/EmptyCache6','Othello/CachedGame6','Othello/CachedRows6','Tests/CachedGameProbe6/Baseline','Tests/CachedGameProbe6/Variant','Tests/CachedGameProbe6/Compact']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=160
        RESERVATION_CPU=180
        ALLOWANCE_CPU=20
        if CACHED_RECOVERY:
            ACTION_SUFFIX='-cached-fixed'
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            OUTER_CPU=140
            RESERVATION_CPU=150
            if CACHED_SECOND:
                ACTION_SUFFIX='-cached-fixed'+str(CACHED_SECOND)
                LABEL+=str(CACHED_SECOND)
                OUT=ROOT/'results'/LABEL
                CHECK=OUT/'check'
                UNIT='othello6-'+LABEL+'.service'
                earlier=[ROOT/'results/cached-game-probe6-20261018']+[ROOT/'results'/('cached-game-probe6-20261018-fixed'+(str(n) if n>1 else '')) for n in range(1,CACHED_SECOND)]
                consumed=sum(json.loads((p/'closure.json').read_text())['charged_cpu_seconds'] for p in earlier)
                RESERVATION_CPU=int(200-20-consumed-1)
                OUTER_CPU=RESERVATION_CPU-25
                assert RESERVATION_CPU>=80
        action=action[:-7]
    if action.endswith('-erased'):
        ERASED_ARITHMETIC=LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-erased'
        LABEL='erased-arithmetic-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Game/BooleanRecompute','Othello/ErasedArithmeticState6','Othello/ErasedArithmeticGame6','Othello/ErasedArithmeticRows6','Tests/ErasedArithmeticProbe6/RefData','Tests/ErasedArithmeticProbe6/Baseline','Tests/ErasedArithmeticProbe6/Variant']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=160
        RESERVATION_CPU=180
        ALLOWANCE_CPU=20
        action=action[:-7]
    if action.endswith('-inline'):
        INLINE_ENTRIES=LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-inline'
        LABEL='inline-entries-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/InlineEntries6','Othello/InlineRows6','Tests/InlineProbe6/Baseline','Tests/InlineProbe6/Variant','Tests/InlineProbe6/Compact']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=160
        RESERVATION_CPU=180
        ALLOWANCE_CPU=20
        action=action[:-7]
    if action.endswith('-unicode'):
        UNICODE_CODEC=LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-unicode'
        LABEL='unicode-codec-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/UnicodeCompact6','Tests/UnicodeCodecProbe6/Data','Tests/UnicodeCodecProbe6/Baseline','Tests/UnicodeCodecProbe6/Variant']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=80
        RESERVATION_CPU=100
        ALLOWANCE_CPU=20
        action=action[:-8]
    if action.endswith('-length'):
        LENGTH_RAYS=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-length'
        LABEL='length-rays-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/LengthRays6','Othello/LengthRules6','Othello/LengthMoves6','Othello/LengthRows6','Tests/LengthProbe6/Baseline','Tests/LengthProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=300
        ALLOWANCE_CPU=20
        action=action[:-7]
    if action.endswith('-strict'):
        STRICT_STATE=PACKED_GAME=ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-strict'
        LABEL='strict-state-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/StrictPacked6','Othello/StrictPackedGame6','Othello/StrictPackedRows6','Othello/StrictBoard6','Othello/StrictBoardRows6','Tests/StrictPackedProbe6/Hybrid','Tests/StrictPackedProbe6/Baseline','Tests/StrictPackedProbe6/Variant','Tests/StrictPackedProbe6/BoardVariant']
        PHASE_CPU=35
        PHASE_TIMEOUT=120
        HARD_GIB=4
        OUTER_CPU=160
        RESERVATION_CPU=180
        ALLOWANCE_CPU=20
        action=action[:-7]
    if action.endswith('-packed-game'):
        PACKED_GAME=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ROW_PACKED=True
        ACTION_SUFFIX='-packed-game'
        LABEL='packed-game-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/PackedGame6','Othello/PackedRows6','Tests/PackedGameProbe6/Baseline','Tests/PackedGameProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=300
        ALLOWANCE_CPU=20
        action=action[:-12]
    if action.endswith('-row-packed'):
        ROW_PACKED=SYMMETRY=DIRECTED=FUSED=INDEXED=INCREMENTAL=True
        ACTION_SUFFIX='-row-packed-fixed' if RECOVERY else '-row-packed'
        LABEL='row-packed-probe6-20261018'+('-fixed' if RECOVERY else '')
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Game/MappedTransfer','Othello/RowPacked6','Game/EncodedResolver','Othello/RowPackedIndexed6','Tests/RowPackedProbe6/RefData','Tests/RowPackedProbe6/Baseline','Tests/RowPackedProbe6/Variant']
        PHASE_CPU=90
        PHASE_TIMEOUT=240
        HARD_GIB=4
        OUTER_CPU=260
        RESERVATION_CPU=300
        ALLOWANCE_CPU=20
        if RECOVERY:RESERVATION_CPU=280
        action=action[:-11]
    if action.endswith('-packed-split'):
        PACKED_SPLIT=True
        action=action[:-6]
    if action.endswith('-opaque'):
        OPAQUE=True
        action=action[:-7]
    if action.endswith('-fixed'):
        RECOVERY=True
        action=action[:-6]
    if action.endswith('-direct'):
        DIRECT=True
        LABEL='direct-rows-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX='Tests.DirectRowsProbe6'
        TARGETS=['Link','States','Bodies','Baseline','Rows']
        PHASE_CPU=50
        PHASE_TIMEOUT=140
        HARD_GIB=6
        OUTER_CPU=180
        RESERVATION_CPU=200
        if RECOVERY:
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            PREFIX='Tests.DirectRowsProbeFixed6'
            RESERVATION_CPU=190
        action=action[:-7]
    if action.endswith('-full'):
        FULL=True
        LABEL='full-resolver-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX='Tests.FullResolverProbe6'
        TARGETS=['Combined/Root']
        PHASE_CPU=420
        PHASE_TIMEOUT=1400
        HARD_GIB=12
        OUTER_CPU=500
        RESERVATION_CPU=600
        ALLOWANCE_CPU=50
        action=action[:-5]
    if action.endswith('-incremental'):
        INCREMENTAL=True
        LABEL='incremental-rule-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/Incremental6','Tests/IncrementalProbe6/Fixture','Tests/IncrementalProbe6/Baseline','Tests/IncrementalProbe6/Variant']
        PHASE_CPU=50
        PHASE_TIMEOUT=140
        HARD_GIB=6
        OUTER_CPU=180
        RESERVATION_CPU=200
        ALLOWANCE_CPU=20
        action=action[:-12]
    if action.endswith('-incremental-indexed'):
        INDEXED=True
        INCREMENTAL=True
        LABEL='incremental-indexed-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Game/IndexedTransfer','Othello/IncrementalIndexed6','Tests/IncrementalIndexedProbe6/Baseline','Tests/IncrementalIndexedProbe6/Variant']
        PHASE_CPU=50
        PHASE_TIMEOUT=140
        HARD_GIB=4
        OUTER_CPU=180
        RESERVATION_CPU=200
        ALLOWANCE_CPU=20
        if RECOVERY:
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            RESERVATION_CPU=190
        if OPAQUE:
            LABEL+='-opaque'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            HARD_GIB=2
            TARGETS=['Game/IndexedTransfer','Othello/IncrementalIndexed6','Tests/IncrementalOpaqueProbe6/Baseline','Tests/IncrementalOpaqueProbe6/Fast','Tests/IncrementalOpaqueProbe6/Transported']
        action=action[:-20]
    if action.endswith('-packed'):
        PACKED=True
        INCREMENTAL=True
        LABEL='packed-nat-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Othello/PackedNat6','Tests/PackedNatProbe6/Data','Tests/PackedNatProbe6/Baseline','Tests/PackedNatProbe6/Variant']
        PHASE_CPU=50
        PHASE_TIMEOUT=140
        HARD_GIB=2
        OUTER_CPU=180
        RESERVATION_CPU=200
        ALLOWANCE_CPU=20
        if PACKED_SPLIT:
            LABEL+='-split'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            TARGETS=['Othello/CompatibleRows6','Tests/PackedNatSplitProbe6/Left','Tests/PackedNatSplitProbe6/Right','Tests/PackedNatSplitProbe6/Aligned','Tests/PackedNatSplitProbe6/Compatible']
        action=action[:-7]
    if action.endswith('-fused'):
        FUSED=True
        INDEXED=True
        INCREMENTAL=True
        LABEL='fused-row-probe6-20261018'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX=''
        TARGETS=['Tests/FusedRowProbe6/Root']
        PHASE_CPU=120
        PHASE_TIMEOUT=400
        HARD_GIB=4
        OUTER_CPU=180
        RESERVATION_CPU=200
        ALLOWANCE_CPU=20
        if RECOVERY:
            LABEL+='-fixed'
            OUT=ROOT/'results'/LABEL
            CHECK=OUT/'check'
            UNIT='othello6-'+LABEL+'.service'
            TARGETS=['Tests/FusedRowFixed6/Root']
            OUTER_CPU=160
            RESERVATION_CPU=180
        action=action[:-6]
    if action=='launch':launch()
    elif action=='supervise':raise SystemExit(supervise())
    else:worker()
