#!/usr/bin/env python3
"""AI-assisted bounded multi-root kernel pilot, supervised by the outer ledger.

Generated shards are checked cold in separate roots. Immutable source and
accepted same-machine interfaces are hard-linked to keep actual disk use small.
Every borrowed interface is checked before and after each run. No desktop
ledger writes, postulates, production run or initial-board claim are made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import assembly6
import bench6
import compact_shared6 as compact
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job

PREFIX='Tests.GlobalPilot6'
HEADER=bench6.OPTIONS
COMMON='''open import Prelude
open import Agda.Builtin.String using (String)
open import Game.Core using (white; black; Guarantees)
open import Game.Shared
open import Game.Soundness using (checkSound)
open import Game.Transfer using (guarantees-transfer)
open import Othello.Board using (State; six; initial)
open import Othello.Shared6 using (keyed6; key6; decodeSharedEntries)
open import Othello.CompactShared6 using (decodeCompactState; decodeCompactEntries)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
open import Othello.Statements using (lowerGoal; upperGoal)
open import Othello.Proof6 using (fastAgreement)
import Othello.Fast6 as Fast
import Othello.Rules as Rules

decode : String → State six
decode text = fromMaybe (initial six) (decodeCompactState text)

'''


def tokens(text):
    return sum(c in 'LCFPSKR' for c in text)


def validate_plan(plan):
    if (plan.get('format')!='othello-global-shared6-plan-v1' or
        plan.get('direction') not in ('lower','upper') or plan.get('threshold')!=4):
        raise ValueError('wrong graph plan or bound')
    roots=plan.get('roots',[]); entries=plan.get('entries',[])
    if not roots or len(set(roots))!=len(roots) or not entries:
        raise ValueError('empty or duplicate roots')
    owners=set()
    for entry in entries:
        state=entry['state'];compact.pack_state(state)
        compact.pack_certificate(entry['certificate'])
        if state in owners or not set(entry['references']) <= owners:
            raise ValueError('duplicate, forward or missing state reference')
        owners.add(state)
    if not set(roots) <= owners:
        raise ValueError('root is not exported')


def partition(entries,max_tokens=16000,max_entries=300):
    parts=[];part=[];count=0;owners={}
    for entry in entries:
        state=entry['state'];refs=set(entry['references'])
        if not refs <= owners.keys():raise ValueError('self or forward reference')
        size=tokens(entry['certificate'])
        if size>max_tokens:raise ValueError('one entry exceeds the part token cap')
        if part and (count+size>max_tokens or len(part)>=max_entries):
            parts.append(part);part=[];count=0
        owners[state]=len(parts);part.append(entry);count+=size
    if part:parts.append(part)
    return parts,owners


def part_source(index,part,owners,direction,variant='compact',suffix='',export_mode='equality'):
    player='white' if direction=='lower' else 'black'
    goal=f'({direction}Goal 4)'; laws=f'{direction}Transport6'
    dependencies=sorted({owners[r] for entry in part for r in entry['references']
                         if owners[r]!=index})
    if any(j>=index for j in dependencies):raise ValueError('non-acyclic shard imports')
    imports=''.join(f'import {PREFIX}.Part{j} as P{j}\n' for j in dependencies)
    selected=[]
    for j in dependencies:
        cited=sorted({r for entry in part for r in entry['references'] if owners[r]==j})
        keys=' ∷ '.join(f'key6 (decode "{compact.pack_state(s)}")' for s in cited)+' ∷ []'
        selected.append(f'selectExport ({keys}) P{j}.export')
    import_list=' ∷ '.join(selected)+' ∷ []' if selected else '[]'
    states='tip'
    for entry in reversed(part):
        literal=compact.pack_state(entry['state'])
        states=f'insertT (key6 (decode "{literal}")) (decode "{literal}") ({states})'
    if variant=='compact':
        decoder='decodeCompactEntries'
        wire=compact.encode((entry['state'],entry['certificate']) for entry in part)
    elif variant=='legacy':
        decoder='decodeSharedEntries'
        wire=''.join(entry['state']+entry['certificate'] for entry in part)
    else:raise ValueError('unknown wire variant')
    if export_mode == 'equality':
        export_import = ''
        export_fact = '  shape : shardStates keyed6 entries ≡ states\n  shape = refl'
        sound_term = f'''subst (AllT (Proven Fast.fastGame6 {player} {goal})) shape
    (shardBy-sound keyed6 Fast.fastGame6 {player} {goal} {laws} imports entries accepted)'''
    elif export_mode == 'coverage':
        export_import = 'open import Game.SharedExport using (covered; covered-sound)\n'
        export_fact = '  coverage : covered keyed6 (shardStates keyed6 entries) states ≡ true\n  coverage = refl'
        sound_term = f'''covered-sound keyed6 Fast.fastGame6 {player} {goal}
    (shardStates keyed6 entries) states
    (shardBy-sound keyed6 Fast.fastGame6 {player} {goal} {laws} imports entries accepted) coverage'''
    else:
        raise ValueError('unknown export proof mode')
    source=HEADER+f'module {PREFIX}.Part{index}{suffix} where\n\n'+COMMON+export_import+imports
    source+=f'''
imports : List (CheckedExport Fast.fastGame6 {player} {goal})
imports = {import_list}

states : Trie (State six)
states = {states}

abstract
  entries : List (SharedEntry (State six))
  entries = fromMaybe [] ({decoder} "{wire}")

{export_fact}

  accepted : checkShardBy keyed6 Fast.fastGame6 {player} {goal} {laws} imports entries ≡ true
  accepted = refl

  sound : AllT (Proven Fast.fastGame6 {player} {goal}) states
  sound = {sound_term}

export : CheckedExport Fast.fastGame6 {player} {goal}
export = checkedExport states sound
'''
    return source,dependencies,len(wire.encode())


def assembly_source(roots,owners,direction):
    player='white' if direction=='lower' else 'black';goal=f'({direction}Goal 4)'
    deps=sorted({owners[s] for s in roots})
    source=HEADER+f'module {PREFIX}.Check where\n\n'+COMMON
    source+=''.join(f'import {PREFIX}.Part{j} as P{j}\n' for j in deps)
    for i,state in enumerate(roots):
        j=owners[state]
        source+=f'''
position{i} : State six
position{i} = decode "{compact.pack_state(state)}"

accepted{i} : knownIn keyed6 P{j}.states position{i} ≡ true
accepted{i} = refl

proven{i} : Proven Fast.fastGame6 {player} {goal} position{i}
proven{i} = knownIn-sound keyed6 Fast.fastGame6 {player} {goal}
  P{j}.states position{i} P{j}.sound accepted{i}

fastGuarantee{i} : Guarantees Fast.fastGame6 {player} {goal} position{i}
fastGuarantee{i} = checkSound Fast.fastGame6 {player} {goal} position{i}
  (proj₁ proven{i}) (proj₂ proven{i})

guarantee{i} : Guarantees (Rules.game six) {player} {goal} position{i}
guarantee{i} = guarantees-transfer Fast.fastGame6 (Rules.game six) fastAgreement fastGuarantee{i}
'''
    return source


def hardlink(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    os.link(source,destination)


def metrics(record):
    return {k:record[k] for k in ['accepted','cpu_seconds','wall_seconds','peak_rss_gib',
                                  'cache_state','stop_reason','source_sha256','agda_source_sha256']}


def execute(args):
    started=time.monotonic();output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    raw=args.plan.read_bytes();plan=json.loads(raw);validate_plan(plan)
    parts,owners=partition(plan['entries'],args.max_tokens,args.max_entries)
    sources={};dependencies={};sizes={}
    for i,part in enumerate(parts):
        text,deps,size=part_source(i,part,owners,plan['direction'])
        sources[f'src/Tests/GlobalPilot6/Part{i}.agda']=text
        dependencies[i]=deps;sizes[i]=size
    sources['src/Tests/GlobalPilot6/Check.agda']=assembly_source(plan['roots'],owners,plan['direction'])
    # A/B has the same states, imports, graph and checker; only payload decoding
    # changes. Both target modules remain cold and use identical dependency facts.
    compare=max(range(len(parts)),key=lambda i:tokens(''.join(e['certificate'] for e in parts[i])))
    for variant,suffix in [('compact','CompactAB'),('legacy','LegacyAB')]:
        text,_,_=part_source(compare,parts[compare],owners,plan['direction'],variant,suffix)
        sources[f'src/Tests/GlobalPilot6/Part{compare}{suffix}.agda']=text
    if max(len(t.encode()) for t in sources.values())>args.max_source_bytes:
        raise ValueError('generated source sizing gate failed')
    source_root=Path(__file__).resolve().parents[1]
    origin=source_identity(source_root);machine=assembly6.machine_identity(args.agda)
    base=output/'source';base.mkdir()
    for name,_ in source_files(source_root):hardlink(source_root/name,base/name)
    for name,text in sources.items():
        p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    base_manifest=bench6.refresh_manifest(base,origin={k:origin[k] for k in ['revision','dirty']})
    files=list(source_files(base));del sources,raw
    report=dict(format='othello-global-assembly6-v1',status='checking',accepted=False,
                scope='100 sampled frontier roots; no initial-board proof',
                direction=plan['direction'],threshold=4,roots=len(plan['roots']),
                plan_sha256=assembly6.sha(args.plan),machine=machine,
                source_sha256=base_manifest['source_sha256'],parts=[],
                part_count=len(parts),comparison_part=compare,ab=[],dependency_graph=dependencies,
                max_tokens=args.max_tokens,max_entries=args.max_entries,
                part_heap_mib=args.heap_mib,compacting_gc=args.compact_gc,
                total_compact_bytes=sum(sizes.values()),interface_sharing='same-machine immutable hard links')
    atomic_json(output/'assembly.json',report)
    accepted_interfaces={};interface_donors={};spent=0.0

    def prepare(label,target):
        root=output/label;root.mkdir()
        for name,_ in files:hardlink(base/name,root/name)
        bench6.refresh_manifest(root,origin={k:origin[k] for k in ['revision','dirty']})
        if assembly6.interfaces(root):raise ValueError('fresh root contains interfaces')
        for rel,digest in accepted_interfaces.items():
            donor=interface_donors[rel]
            if assembly6.sha(donor)!=digest:raise ValueError('accepted donor interface changed')
            hardlink(donor,root/rel)
        before=assembly6.interfaces(root)
        if any(p.endswith('/'+target.rsplit('/',1)[-1].replace('.agda','.agdai')) for p in before):
            raise ValueError('own target is not cold')
        return root,before

    def check(label,target,limit,rss,heap,metadata):
        nonlocal spent
        remaining=args.kernel_cpu_budget-spent
        if remaining < 10:raise ValueError('pilot internal kernel budget exhausted')
        limit=min(limit,remaining)
        root,before=prepare(label,target)
        if assembly6.machine_identity(args.agda)!=machine:raise ValueError('machine or binary changed')
        record=run_job(label,[args.agda,*assembly6.FLAGS,'-i','src',target,
                             '+RTS',f'-M{heap}M',*(['-c'] if args.compact_gc else []),
                             '-RTS'],output/'records',root=root,
                       expected_source_sha256=base_manifest['source_sha256'],
                       cpu_limit=limit,timeout=max(90,limit*2),rss_limit_gib=rss,log_limit_mib=2,
                       metadata={'machine':machine,'own_target_cold':True,
                                 'borrowed_interfaces_sha256':digest_entries(before),**metadata})
        spent+=record['cpu_seconds']
        after=assembly6.interfaces(root)
        for rel,digest in before.items():
            if after.get(rel)!=digest:raise ValueError('imported interface mutated')
        if record['accepted']:
            for rel,digest in after.items():
                if rel in accepted_interfaces and accepted_interfaces[rel]!=digest:
                    raise ValueError('conflicting accepted interfaces')
                accepted_interfaces[rel]=digest;interface_donors.setdefault(rel,root/rel)
        return metrics(record)

    for i,part in enumerate(parts):
        metric=check(f'global-part{i}',f'src/Tests/GlobalPilot6/Part{i}.agda',
                     args.part_cpu_limit,1.5,args.heap_mib,{'dependencies':dependencies[i]})
        metric.update(index=i,entries=len(part),checked_tokens=sum(tokens(e['certificate']) for e in part),
                      compact_bytes=sizes[i],imported_states=len({r for e in part for r in e['references']
                                                                 if owners[r]!=i}))
        report['parts'].append(metric);report['measured_kernel_cpu_seconds']=spent
        atomic_json(output/'assembly.json',report)
        print(json.dumps({'part':i,'part_count':len(parts),**metric}),flush=True)
        if not metric['accepted']:
            report['status']='part-failed';atomic_json(output/'assembly.json',report);return False
    for variant,suffix in [('compact','CompactAB'),('legacy','LegacyAB')]:
        metric=check(f'global-ab-{variant}',f'src/Tests/GlobalPilot6/Part{compare}{suffix}.agda',
                     args.part_cpu_limit,1.5,args.heap_mib,{'paired_graph_part':compare,'variant':variant})
        metric.update(variant=variant);report['ab'].append(metric)
        atomic_json(output/'assembly.json',report)
        if not metric['accepted']:
            report['status']='ab-failed';atomic_json(output/'assembly.json',report);return False
    record=check('global-all-roots','src/Tests/GlobalPilot6/Check.agda',
                 args.assembly_cpu_limit,3,2500,{'root_guarantees':len(plan['roots'])})
    report.update(assembly=record,accepted=record['accepted'],
                  status='complete' if record['accepted'] else 'assembly-failed',
                  measured_kernel_cpu_seconds=spent,
                  borrowed_interface_count=len(accepted_interfaces),
                  accepted_interface_sha256=digest_entries(accepted_interfaces),
                  harness_wall_seconds=time.monotonic()-started)
    atomic_json(output/'assembly.json',report)
    print(json.dumps({'status':report['status'],'roots':len(plan['roots']),
                      'parts':len(parts),'kernel_cpu_seconds':spent}),flush=True)
    return report['accepted']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--agda',required=True)
    p.add_argument('--max-tokens',type=int,default=16000)
    p.add_argument('--max-entries',type=int,default=300)
    p.add_argument('--max-source-bytes',type=int,default=1048576)
    p.add_argument('--part-cpu-limit',type=float,default=120)
    p.add_argument('--assembly-cpu-limit',type=float,default=180)
    p.add_argument('--kernel-cpu-budget',type=float,default=4200)
    p.add_argument('--heap-mib',type=int,default=1200)
    p.add_argument('--compact-gc',action='store_true')
    args=p.parse_args()
    if min(args.max_tokens,args.max_entries,args.kernel_cpu_budget)<=0:
        p.error('sizing and CPU caps must be positive')
    if not 0<args.heap_mib<=1350:
        p.error('part heap cap must be positive and at most 1350 MiB; RSS remains 1.5 GiB')
    return 0 if execute(args) else 1


if __name__=='__main__':raise SystemExit(main())
