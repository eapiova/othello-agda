"""AI-assisted bounded measurement of exact singleton citation resolvers.

Every singleton is linked to the accepted resolver by a safe closed equality.
The game checker, states, bodies, and semantic coverage are unchanged.
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

import assembly6
import completion_batch6 as prior
import full_map_pilot6 as full
from canonical_join6 import emit_join
from provenance import source_identity
from run_job import atomic_json, build_lock, run_job, utc
from study6 import Ledger

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'sparse-citation-pilot6-20261018'
OUT = ROOT/'results'/LABEL
CHECK = OUT/'check'
UNIT = 'othello6-'+LABEL+'.service'
PREFIX = 'Tests.SparseCitationPilot6'
PARTS = [342, 33154]
FIXED = False
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON = '''open import Prelude
open import Agda.Builtin.Nat using (_+_)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy
open import Othello.Board using (State; six)
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(items, leaf, combine):
    require(bool(items), 'nonempty tree required')
    if len(items) == 1:
        return leaf(items[0])
    middle = len(items)//2
    return combine(items[middle], tree(items[:middle], leaf, combine),
                   tree(items[middle:], leaf, combine))


def emit():
    sample = json.loads((prior.OUT/'sample.json').read_text())
    manifest = json.loads((prior.bridge.FULL/'results/full-state-map6.json').read_text())
    chunks = {x['part']: x for x in manifest['chunks']}
    sources = {}

    def add(module, body):
        name = 'src/'+module.replace('.', '/')+'.agda'
        require(name not in sources, 'duplicate module')
        sources[name] = (HEADER+'-- AI-assisted; all generated assertions require safe checking.\nmodule '
                         +module+' where\n\n'+body).encode()

    units = []
    for part in PARTS:
        case = next(x for x in sample['cases'] if x['part'] == part)
        references = sorted(set(case['references']))
        old_prefix = 'Tests.CompletionBatchLowerA6.Rows'+str(part)
        prefix = PREFIX+'.Rows'+str(part)
        groups = [references[i:i+32] for i in range(0, len(references), 32)]
        group_ids = list(range(len(groups)))
        for group_id, keys in enumerate(groups):
            body = COMMON+f'import {old_prefix}.Part{part} as Original\n'
            for key in keys:
                chunk = sample['states'][str(key//200)]
                literal = chunk['text'][13*(key%200):13*(key%200+1)]
                require(len(literal) == 13, 'complete singleton state required')
                body += f'''s{key} : B.Vec (State six) 1
s{key} = Lazy.states 1 "{literal}"
abstract
  hit{key} : M.lookup Original.demand {key} ≡ just (B.lookupVec s{key} B.fzero)
  hit{key} = refl
aligned{key} : ∀ G → Laws.Aligned Original.demand G →
  Laws.Aligned (M.rows {key} 1 s{key}) G
aligned{key} G same B.fzero =
  Laws.aligned-compatible {{map = Original.demand}} {'{G = G}' if FIXED else ''} same {key} _ hit{key}
aligned{key} G same (B.fsuc ())
'''
            expression = tree(keys, lambda k:f'(M.rows {k} 1 s{k})',
                              lambda pivot,l,r:f'(M.branch {pivot} {l} {r})')
            proof = tree(keys, lambda k:f'(aligned{k} G same)',
                         lambda _,l,r:f'({l} , {r})')
            body += f'''demand : M.Map (State six)
demand = {expression}
aligned : ∀ G → Laws.Aligned Original.demand G → Laws.Aligned demand G
aligned G same = {proof}
'''
            add(prefix+'.Citations'+str(group_id), body)
        own_module = chunks[part]['module']
        body = COMMON+f'''import {old_prefix}.Part{part} as Original
import {old_prefix}.Family as Family
import {old_prefix}.BodyData{part} as Body
import {own_module} as Own
'''
        body += ''.join(f'import {prefix}.Citations{i} as E{i}\n' for i in group_ids)
        expression = tree(group_ids, lambda i:f'E{i}.demand',
            lambda i,l,r:f'(M.branch {groups[i][0]} {l} {r})')
        proof = tree(group_ids, lambda i:f'(E{i}.aligned G same)',
                     lambda _,l,r:f'({l} , {r})')
        body += f'''demand : M.Map (State six)
demand = {expression}
states = Original.states
bodies = Original.bodies
embed = Original.embed
aligned : ∀ G → Laws.Aligned Original.demand G → Laws.Aligned demand G
aligned G same = {proof}
abstract
  accepted : Family.L.checkPart (M.lookup demand) embed Own.text Body.text ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned Original.demand G → Laws.Aligned states G → Laws.Aligned bodies C →
    Family.A.Partial G C states
  linked G C sameDemand sameStates sameBodies =
    Family.L.linkedAligned {{n = 200}} {200*part} demand Own.text Body.text accepted
      G C (aligned G sameDemand) sameStates sameBodies
'''
        add(prefix+'.Part'+str(part), body)
        add(prefix+'.BodyData'+str(part), COMMON+f'''import {old_prefix}.BodyData{part} as Body
text = Body.text
bodies = Body.bodies
''')
        add(prefix+'.Family', COMMON+f'''import {old_prefix}.Family as Original
module L = Original.L
module A = Original.A
''')
        bridge_prefix = PREFIX+'.Bridge'+str(part)
        old_bridge = 'Tests.CompletionBatchLowerA6.Bridge'+str(part)
        root = (prior.WORK/f'prepared/parts/{part}/bridge/src'/
                (old_bridge.replace('.', '/')+'/Root.agda')).read_text()
        root = root.replace('module '+old_bridge+'.Root where', 'module '+bridge_prefix+'.Root where')
        root = root.replace('import '+old_prefix+'.Part'+str(part)+' as Part',
                            'import '+prefix+'.Part'+str(part)+' as Part')
        relative = 'src/'+bridge_prefix.replace('.', '/')+'/Root.agda'
        sources[relative] = root.encode()
        units.append(dict(part=part,rows=200,row_prefix=prefix,bridge_prefix=bridge_prefix))
    CHECK.mkdir(parents=True)
    for relative, raw in sources.items():
        destination = CHECK/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw)
    # emit_join requires a fresh root; its source is then moved into CHECK.
    joint = emit_join(OUT/'joint-source', manifest, units, prefix=PREFIX+'.Combined')
    for path in (OUT/'joint-source/src').rglob('*.agda'):
        relative = path.relative_to(OUT/'joint-source')
        destination = CHECK/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(path,destination)
    (CHECK/'othello.agda-lib').write_text((ROOT/'othello.agda-lib').read_text())
    return dict(parts=PARTS,semantic_owned_rows=400,new_distinct_rows=0,
                source=source_identity(CHECK),root_module=joint['root_module'],
                expected_modules=sorted(re.search(r'(?m)^module (\S+) where',p.read_text())[1]
                                        for p in (CHECK/'src').rglob('*.agda')),
                source_sha256={str(p.relative_to(CHECK)):sha(p) for p in (CHECK/'src').rglob('*.agda')})


def storage(reserve=0):
    used = prior.allocated(full.BASE)+prior.allocated(ROOT/'results/grouped-bridge6-20261018')
    used += prior.allocated(prior.OUT)
    used += sum(prior.allocated(p) for p in (ROOT/'results').glob('sparse-citation-pilot6-20261018*'))
    used += prior.allocated(ROOT/'results/citation-diagnostic6-20261018')
    free = shutil.disk_usage(ROOT).free
    require(used+reserve<12*2**30 and free-reserve>=80*2**30
            and prior.allocated(OUT)+reserve<=64*2**20, 'unchanged storage limits reached')
    return dict(allocated_study_bytes=used,free_bytes=free,new_artifact_bytes=prior.allocated(OUT),
                reserved_bytes=reserve,checked_utc=utc())


def donors():
    expected,_=prior.expected_donors()
    accepted=json.loads((prior.OUT/'report.json').read_text())
    require(accepted['accepted'], 'accepted previous batch required')
    pools=json.loads((prior.OUT/'interfaces.json').read_text())
    for path,pool in pools.items():
        path=Path(path)
        expected[path]=(source_identity(path)['source_sha256'],prior.digest_entries(pool))
    return expected


def worker():
    prior.authorized()
    group=prior.resources()
    plan=json.loads((OUT/'plan.json').read_text())
    require(all(sha(ROOT/'tools'/n)==h for n,h in plan['helper_sha256'].items()), 'worker changed')
    require(sha(prior.AUTH)==plan['authorization_sha256'], 'authorization changed')
    expected={Path(p):tuple(pin) for p,pin in plan['donors'].items()}
    with contextlib.ExitStack() as stack:
        for path in sorted(expected):
            lock=stack.enter_context((path/'_build/.study6.lock').open('rb'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before=prior.donor_snapshot(expected)
        stack.enter_context(build_lock(CHECK))
        require(not assembly6.interfaces(CHECK), 'owned target must start cold')
        require(source_identity(CHECK)==plan['layout']['source'], 'new sources changed')
        failures=[]
        stop=threading.Event()
        def watch():
            while not stop.wait(3):
                try:
                    require(prior.usage(group)['cpu_seconds']<550,'550CPU service stop')
                    atomic_json(OUT/'storage.json',storage(8*2**20))
                except BaseException as error:
                    failures.append(str(error))
                    atomic_json(OUT/'resource-stop.json',dict(reason=str(error),finished_utc=utc()))
                    os.kill(os.getpid(),signal.SIGTERM)
                    return
        watcher=threading.Thread(target=watch,daemon=True);watcher.start()
        try:
            argv=['/usr/bin/bwrap','--ro-bind','/','/','--bind',str(CHECK),str(CHECK),
                  '--proc','/proc','--dev-bind','/dev','/dev','--tmpfs','/tmp','--die-with-parent','--',
                  full.AGDA,'--no-libraries','-i','src']
            for path in expected:argv+=['-i',str(path/'src')]
            argv+=['--safe','--without-K','--cubical-compatible','--save-metas','--profile=modules',
                   'src/'+plan['layout']['root_module'].replace('.','/')+'.agda',
                   '+RTS','-M10G','-c','-s','-RTS']
            record=run_job('sparse-agda',argv,OUT/'records',root=CHECK,timeout=1400,cpu_limit=420,
                           rss_limit_gib=11.5,log_limit_mib=8,
                           expected_source_sha256=plan['layout']['source']['source_sha256'],
                           metadata=dict(checker_binary_sha256=full.AGDA_SHA,own_targets_cold=True,
                                         native_search_allowed=False,production_authorized=False))
        finally:
            stop.set();watcher.join()
        checked=re.findall(r'(?m)^\s*Checking (\S+) \(', (OUT/'records/sparse-agda.log').read_text())
        intact=prior.donor_snapshot(expected)==before
        pool=assembly6.interfaces(CHECK)
        history=json.loads((ROOT/'results/migration-handoff6-20261018-021658/handoff.json').read_text())
        p1=all(sha(ROOT/n)==h for n,h in history['p1_files'].items())
        accepted=bool(record['accepted'] and not failures and intact and p1
            and source_identity(CHECK)==plan['layout']['source']
            and set(checked)==set(plan['layout']['expected_modules']) and len(checked)==len(pool)
            and len(checked)==len(plan['layout']['expected_modules']))
        atomic_json(OUT/'interfaces.json',pool)
        atomic_json(OUT/'report.json',dict(format='othello-sparse-citation6-report-v1',accepted=accepted,
            record=record,checked_modules=checked,accepted_donors_unchanged=intact,p1_unchanged=p1,
            storage=storage(),cgroup=prior.usage(group),new_distinct_rows=0,semantic_owned_rows=400,
            initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
            finished_utc=utc()))
        require(accepted,'sparse resolver measurement not accepted; preserve receipts')


def supervise():
    prior.authorized()
    group=prior.resources()
    job=json.loads((OUT/'job.json').read_text())
    require(not (OUT/'records'/(LABEL+'.json')).exists(),'never restart existing job')
    record=run_job(LABEL,['/usr/bin/python3','-B',str(Path(__file__).resolve()),'worker-fixed' if FIXED else 'worker'],
        OUT/'records',root=OUT/'control',timeout=1600,cpu_limit=500,rss_limit_gib=11.75,
        log_limit_mib=4,reservation_id=job['reservation']['reservation_id'],
        expected_source_sha256=job['control_source']['source_sha256'])
    atomic_json(OUT/'service-accounting.json',prior.usage(group))
    return 0 if record['accepted'] else 1


def launch():
    prior.authorized()
    require(not OUT.exists(),'fresh output required')
    require(not subprocess.check_output(['systemctl','--user','list-units','--state=activating,running',
            '--type=service','--no-legend','--plain','othello*'],text=True).strip(),'Othello job active')
    require(not any(x.strip().lower()=='agda' for x in subprocess.check_output(
        ['ps','-eo','comm='],text=True).splitlines()),'Agda already active')
    require(sha(full.AGDA)==full.AGDA_SHA,'checker binary changed')
    storage(64*2**20)
    expected=donors()
    layout=emit()
    helpers=sorted(set(prior.HELPERS+['sparse_citation_pilot6.py','full_map_pilot6.py']))
    plan=dict(format='othello-sparse-citation6-plan-v1',layout=layout,
        authorization_sha256=sha(prior.AUTH),helper_sha256={n:sha(ROOT/'tools'/n) for n in helpers},
        donors={str(p):pin for p,pin in expected.items()},cpu_scope_cap_seconds=650,
        kernel_reservation_seconds=600,assembly_allowance_seconds=50,
        hard_memory_gib=12,swap_bytes=0,ordinary_free_disk_floor_gib=80,artifact_cap_gib=12,
        full_workflow_forecast_validated=False,production_authorized=False,created_utc=utc(),
        explicit_resolver_parameter=FIXED,
        diagnostic_evidence='results/citation-diagnostic6-20261018/closure.json' if FIXED else None)
    atomic_json(OUT/'plan.json',plan)
    control=OUT/'control';control.mkdir()
    shutil.copy2(Path(__file__),control/'worker.py')
    ledger=Ledger(ROOT/'results/study6-ledger.json')
    summary=Ledger.summary(json.loads(ledger.path.read_text()))
    require(not summary['outstanding'] and summary['categories']['kernel']['available_cpu_seconds']>=600
        and summary['categories']['assembly']['available_cpu_seconds']>=50,'existing balance insufficient')
    allowance=ledger.withhold('assembly',50,'Continuing completion6: conservative sparse citation pilot preparation/final audit and supervisor allowance; no additional budget.')
    reservation=ledger.reserve('kernel',600,LABEL)
    atomic_json(OUT/'job.json',dict(reservation=reservation,control_allowance=allowance,
        control_source=source_identity(control),plan_sha256=sha(OUT/'plan.json'),unit=UNIT))
    args=['systemd-run','--user','--no-block','--unit='+UNIT,'--property=MemoryMax=12G',
        '--property=MemorySwapMax=0','--property=CPUQuota=100%','--property=TasksMax=256',
        '--property=KillMode=control-group','--property=RuntimeMaxSec=1700','--property=TimeoutStopSec=10',
        '--property=WorkingDirectory='+str(control),'--property=StandardOutput=append:'+str(OUT/'service.log'),
        '--property=StandardError=append:'+str(OUT/'service.log'),'/usr/bin/python3','-B',str(Path(__file__).resolve()),'supervise-fixed' if FIXED else 'supervise']
    response=subprocess.run(args,capture_output=True,text=True)
    atomic_json(OUT/'dispatch.json',dict(argv=args,exit_code=response.returncode,stdout=response.stdout,stderr=response.stderr,submitted_utc=utc()))
    print(json.dumps(dict(unit=UNIT,parts=PARTS,modules=len(layout['expected_modules']),reservation=reservation)))
    require(response.returncode==0,'dispatch failed; retain reservation')


if __name__=='__main__':
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['GIT_OPTIONAL_LOCKS']='0'
    require(len(sys.argv)==2 and sys.argv[1] in ('launch','supervise','worker','launch-fixed','supervise-fixed','worker-fixed'),'explicit action required')
    action=sys.argv[1]
    if action.endswith('-fixed'):
        FIXED=True
        LABEL='sparse-citation-pilot6-20261018-fixed'
        OUT=ROOT/'results'/LABEL
        CHECK=OUT/'check'
        UNIT='othello6-'+LABEL+'.service'
        PREFIX='Tests.SparseCitationFixed6'
        action=action[:-6]
    if action=='launch':launch()
    elif action=='supervise':raise SystemExit(supervise())
    else:worker()
