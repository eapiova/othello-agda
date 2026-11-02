#!/usr/bin/env python3
"""Check an exhausted row part in bounded slices, retaining all original data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil

import assembly6
from cache_resume6 import copy_interface
from indexed_family6 import pinned
from indexed_wire_resume6 import closed
from owner_cache_dedup6 import allocated
from provenance import digest_entries, source_files, source_identity
from run_job import atomic_json, run_job, utc
from wire_workflow6 import require

PREFIX='Tests.IndexedWire6'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'


def generate(check: Path, part: int):
    path=check/('src/Tests/IndexedWire6/Part'+str(part)+'.agda')
    original=path.read_text()
    require('embed : B.Fin 200 →' in original and original.count('\nabstract\n')==1,
            'a real 200-row unaccepted part required')
    prelude=original[original.index('open import Prelude\n'):original.index('\nabstract\n')]
    instance='module Lower = D.Checking Shape.shape Fast.fastGame6 white (lowerGoal 4) lowerTransport6\n'
    require(prelude.count(instance)==1, 'known lower checker instance required')
    prelude=prelude.replace(instance,'import '+PREFIX+'.Family as Family\n')
    name='SliceContext'+str(part)
    context=prelude+'\nimport Game.BalancedSlice as Slice\n'
    context+=f'\nfullStates : B.Vec (State six) 200\nfullStates = S{part}.states\n'
    context+='fullBodies : B.Vec (I.IndexedCertificate (B.Id Shape.shape)) 200\nfullBodies = Body.bodies\n'
    context+='''
private
  parsed : ∀ {A : Set} → Maybe A → Bool
  parsed nothing = false
  parsed (just x) = true

abstract
  parseOK : parsed (D.decodeStates 200 S'''+str(part)+'''.text) ∧
    parsed (D.decodeBodies Shape.shape 200 Body.text) ≡ true
  parseOK = refl

linkRows : ∀ {n} (at : B.Fin n → B.Id Shape.shape)
  (ss : B.Vec (State six) n) (cs : B.Vec (I.IndexedCertificate (B.Id Shape.shape)) n) →
  Family.Lower.checkRows L at ss cs ≡ true →
  (G : B.Id Shape.shape → State six) →
  (C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)) →
  Family.Lower.V.Compatible L G →
  (∀ i → G (at i) ≡ B.lookupVec ss i) →
  (∀ i → C (at i) ≡ B.lookupVec cs i) →
  ∀ i → Family.Lower.V.TreeOK G (at i) (G (at i)) (C (at i))
linkRows at ss cs accepted G C compatible sameState sameBody i =
  subst (λ s → Family.Lower.V.TreeOK G (at i) s (C (at i))) (sym (sameState i))
    (subst (λ c → Family.Lower.V.TreeOK G (at i) (B.lookupVec ss i) c) (sym (sameBody i))
      (Family.Lower.V.lift-local compatible
        (Family.Lower.V.checkLocal-sound L (at i) (B.lookupVec ss i) (B.lookupVec cs i)
          (Family.Lower.checkRows-row L at ss cs accepted i))))
'''
    sources={}
    def emit(module,body):
        sources['src/Tests/IndexedWire6/'+module+'.agda']=HEADER+'-- AI-assisted; the kernel checks parser guards and every row.\nmodule '+PREFIX+'.'+module+' where\n\n'+body
    for block in range(4):
        first,second=('prefix' if block<2 else 'suffix'),('prefix' if block%2==0 else 'suffix')
        inner=('Slice.prefix {n = 50} {m = 50} i' if second=='prefix' else 'Slice.suffix 50 i')
        idx=('Slice.prefix {n = 100} {m = 100} ('+inner+')' if first=='prefix' else 'Slice.suffix 100 ('+inner+')')
        outer='take' if first=='prefix' else 'drop';inside='take' if second=='prefix' else 'drop'
        context+=f'\nindex{block} : B.Fin 50 → B.Fin 200\nindex{block} i = {idx}\n'
        for field,full,element in [('states','S'+str(part)+'.states','State six'),
                                   ('bodies','Body.bodies','I.IndexedCertificate (B.Id Shape.shape)')]:
            mid='Slice.'+outer+' 100 '+full
            vector='Slice.'+inside+' 50 ('+mid+')'
            context+=f'{field}{block} : B.Vec ({element}) 50\n{field}{block} = {vector}\n'
            context+=f'''{field}Aligned{block} : ∀ i → B.lookupVec {full} (index{block} i) ≡ B.lookupVec {field}{block} i
{field}Aligned{block} i =
  trans (Slice.lookup-{outer} 100 {full} ({inner}))
    (Slice.lookup-{inside} 50 ({mid}) i)
'''
    emit(name,context)
    common='''open import Prelude
import Game.Balanced as B
import Game.BalancedSlice as Slice
import Game.BalancedView as View
import Game.Indexed as I
open import Othello.Board using (State; six)
import Tests.IndexedWire6.Shape as Shape
import Tests.IndexedWire6.Family as Family
import Tests.IndexedWire6.'''+name+' as Context\n'
    targets=[name]
    for block in range(4):
        module='Slice'+str(part)+'q'+str(block)
        body=common+f'''
embed : B.Fin 50 → B.Id Shape.shape
embed i = Context.embed (Context.index{block} i)
abstract
  accepted : Family.Lower.checkRows Context.L embed Context.states{block} Context.bodies{block} ≡ true
  accepted = refl
  linked : (G : B.Id Shape.shape → State six) →
    (C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)) →
    Family.Lower.V.Compatible Context.L G →
    (∀ i → G (embed i) ≡ B.lookupVec Context.states{block} i) →
    (∀ i → C (embed i) ≡ B.lookupVec Context.bodies{block} i) →
    ∀ i → Family.Lower.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
  linked G C compatible sameState sameBody =
    Context.linkRows embed Context.states{block} Context.bodies{block} accepted G C compatible sameState sameBody
'''
        emit(module,body);targets.append(module)
    parent=common+''.join('import '+PREFIX+'.Slice'+str(part)+'q'+str(b)+' as P'+str(b)+'\n' for b in range(4))
    parent+='''
embed : B.Fin 200 → B.Id Shape.shape
embed = Context.embed
localView : View.View (State six) Shape.shape
localView = Context.localView
L : I.Resolver (B.Id Shape.shape) (State six)
L = Context.L

abstract
  linked : (G : B.Id Shape.shape → State six) →
    (C : B.Id Shape.shape → I.IndexedCertificate (B.Id Shape.shape)) →
    Family.Lower.V.Compatible L G →
    (∀ i → G (embed i) ≡ B.lookupVec Context.fullStates i) →
    (∀ i → C (embed i) ≡ B.lookupVec Context.fullBodies i) →
    ∀ i → Family.Lower.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
  linked G C compatible sameState sameBody =
    Slice.combine {n = 100} {m = 100} P
      (Slice.combine {n = 50} {m = 50} (λ i → P (Slice.prefix {n = 100} {m = 100} i)) low0 low1)
      (Slice.combine {n = 50} {m = 50} (λ i → P (Slice.suffix 100 i)) low2 low3)
    where
    P : B.Fin 200 → Set
    P i = Family.Lower.V.TreeOK G (embed i) (G (embed i)) (C (embed i))
'''
    for b in range(4):
        parent+=f'''    low{b} : ∀ i → P (Context.index{b} i)
    low{b} = P{b}.linked G C compatible
      (λ i → trans (sameState (Context.index{b} i)) (Context.statesAligned{b} i))
      (λ i → trans (sameBody (Context.index{b} i)) (Context.bodiesAligned{b} i))
'''
    emit('Part'+str(part),parent);targets.append('Part'+str(part))
    for relative,text in sources.items():
        file=check/relative
        require(not file.exists() or file==path, 'refusing generated source overwrite')
        file.write_text(text)
    return dict(targets=targets,generated_sha256={n:assembly6.sha(check/n) for n in sources},part=part,
                rows=200,rows_per_slice=50,all_original_state_and_body_data_preserved=True)


def run(args):
    current=Path.cwd();out=args.output.resolve();require(not out.exists() and 'results' in out.parts, 'fresh output required');out.mkdir(parents=True)
    old=args.previous/'results/indexed-wire-resume6/check'
    previous_receipt=pinned(args.previous/'results/indexed-wire-resume-20261009.json',
        'e5a8cc5542a53a30cc45097091f228355603ef5a576aaf4e4ea83ad6656cf9eb')
    require(previous_receipt.get('finished_utc') and previous_receipt['source_unchanged'] and
            previous_receipt['expected_source_matches'] and not previous_receipt['accepted'] and
            source_identity(args.previous)['source_sha256']==previous_receipt['source_sha256'],
            'terminal unchanged previous outer run required')
    previous_service=closed(previous_receipt)
    prior=pinned(old.parent/'report.json',args.expected_previous_report_sha256)
    pool=pinned(old.parent/'interface-map.json',args.expected_previous_map_sha256)
    source_old=source_identity(old);machine=assembly6.machine_identity(args.agda)
    require(prior['checked_source']==source_old and assembly6.interfaces(old)==pool and
            digest_entries(pool)==prior['last_interface_pool_sha256'], 'unchanged terminal prefix required')
    require(machine==prior['machine'] and machine['agda_sha256']==args.expected_agda_sha256 and machine['hostname']=='eapiova', 'same pinned compiler required')
    require(prior['reused_parts']==172 and len(prior['phases'])==61 and
            all(p['record']['accepted'] for p in prior['phases'][:-1]) and
            prior['phases'][-1]['target']=='Tests.IndexedWire6.Part232' and not prior['phases'][-1]['record']['accepted'], 'exact 232-part prefix required')
    require(not any(n.endswith('/Part232.agdai') for n in pool), 'failed own proof cache cannot be reused')
    family=args.family/'results/indexed-family6/check'
    family_receipt=pinned(args.family/'results/indexed-rewrite-warning-20261009.json',
        '22763d2e5ce9f29d9343b9fe6b52d85698af613078e53126d0f54b6c2cff1846')
    require(family_receipt.get('finished_utc') and family_receipt['accepted'] and
            family_receipt['source_unchanged'] and family_receipt['expected_source_matches'] and
            source_identity(args.family)['source_sha256']==family_receipt['source_sha256'],
            'terminal unchanged family donor required')
    family_service=closed(family_receipt)
    fr=pinned(family.parent/'report.json',args.expected_family_report_sha256)
    fp=pinned(family.parent/'interface-map.json',args.expected_family_map_sha256)
    require(fr['accepted'] and fr['machine']==machine and fr['checked_source']==source_identity(family) and
            assembly6.interfaces(family)==fp and fr['redundant_rewrite_warning_filter']=='-WnoRewritesNothing', 'accepted filtered family required')
    family_source='src/Tests/IndexedWire6/Family.agda';family_names=[n for n in fp if n.endswith('/Tests/IndexedWire6/Family.agdai')]
    require(len(family_names)==1 and not (old/family_source).exists(), 'one new shared checker instance required')
    for name,h in fp.items():
        if '/Tests/' not in name or name.endswith('/Tests/IndexedWire6/Shape.agdai'):
            require(pool.get(name)==h, 'shared checker dependency differs from the accepted prefix')
    report=dict(format='othello-indexed-slices6-v1',accepted=False,status='preparing',created_utc=utc(),machine=machine,
                phases=[],kernel_cpu_seconds=0.,reused_indexed_parts=232,previous_report_sha256=args.expected_previous_report_sha256,
                initial_problem2_proved=False,optimal_initial_pair_proved=False,production_authorized=False,
                scope='four 50-row checks and exact original-ID recombination for exhausted Part232')
    report.update(previous_closed_service=previous_service,family_closed_service=family_service,
        previous_outer_receipt_sha256=assembly6.sha(args.previous/'results/indexed-wire-resume-20261009.json'),
        family_outer_receipt_sha256=assembly6.sha(args.family/'results/indexed-rewrite-warning-20261009.json'))
    def save():atomic_json(out/'report.json',report)
    def guard(extra=0):
        used=allocated(current.parent);free=shutil.disk_usage(current.parent).free
        report['last_storage_gate']=dict(allocated_study_bytes=used,free_bytes=free,checked_utc=utc());save()
        require(used+extra<10*2**30 and free-extra>=100*2**30, 'storage gate reached; prefix preserved')
    estimate=sum((old/n).stat().st_blocks*512 for n,_ in source_files(old))+sum((old/n).stat().st_blocks*512 for n in pool)
    guard(estimate+4*2**20)
    check=out/'check';check.mkdir()
    for name,_ in source_files(old):
        path=check/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/name,path)
    for name,h in pool.items():copy_interface(old/name,check/name,h)
    helper='src/Game/BalancedSlice.agda';require(not (check/helper).exists(),'new slice helper required');shutil.copy2(current/helper,check/helper)
    shutil.copy2(family/family_source,check/family_source)
    family_name=family_names[0];copy_interface(family/family_name,check/family_name,fp[family_name])
    layout=generate(check,232)
    reused_targets=set()
    if args.reuse_context:
        recovery=args.reuse_context.resolve();rc=recovery/'results/indexed-slices6/check'
        rr=pinned(rc.parent/'report.json','04334a2998446930e9fe8689a0b031c54fa9d3d18d27f962181ab7b642e3b734')
        rm=pinned(rc.parent/'interface-map.json','685ddc115ebba9f2c7b28856efbe051bc9123c875bab2778f0fbf3e8fb1e51ba')
        ra=json.loads((recovery/'results/indexed-slices-pilot-20261009.json').read_text())
        require(ra.get('finished_utc') and not ra['accepted'] and ra['source_unchanged'] and
            ra['expected_source_matches'] and source_identity(recovery)['source_sha256']==ra['source_sha256'],
            'terminal unchanged context pilot required')
        report['context_previous_closed_service']=closed(ra)
        require(rr['machine']==machine and rr['checked_source']==source_identity(rc) and
            assembly6.interfaces(rc)==rm and digest_entries(rm)==rr['last_interface_pool_sha256'] and
            len(rr['phases'])==2 and rr['phases'][0]['target']=='SliceContext232' and
            rr['phases'][0]['record']['accepted'] and rr['phases'][0]['borrowed_interfaces_unchanged'] and
            not rr['phases'][1]['record']['accepted'], 'exact accepted context required')
        for relative in (helper,'src/Tests/IndexedWire6/SliceContext232.agda'):
            require((rc/relative).read_bytes()==(check/relative).read_bytes(), 'context source differs')
            shutil.copy2(rc/relative,check/relative)
        extra={n:h for n,h in rm.items() if n not in pool and n!=family_name}
        require(len(extra)==2 and any(n.endswith('/Game/BalancedSlice.agdai') for n in extra) and
            any(n.endswith('/Tests/IndexedWire6/SliceContext232.agdai') for n in extra),
            'only accepted helper and context interfaces can be adopted')
        before=assembly6.interfaces(check)
        require(all(before.get(n)==h for n,h in rm.items() if n not in extra), 'context dependencies differ')
        for name,h in extra.items():copy_interface(rc/name,check/name,h)
        report['reused_context_phase']=rr['phases'][0]
        report['reused_context_report_sha256']=assembly6.sha(rc.parent/'report.json')
        report['reused_context_receipt_sha256']=assembly6.sha(recovery/'results/indexed-slices-pilot-20261009.json')
        reused_targets.add('SliceContext232')
    source=source_identity(check);report.update(checked_source=source,layout=layout);save()
    for index,target in enumerate(layout['targets']):
        if target in reused_targets:continue
        guard();left=args.kernel_cpu_limit-report['kernel_cpu_seconds'];require(left>=1,'nested CPU cap reached')
        before=assembly6.interfaces(check);suffix='/Tests/IndexedWire6/'+target+'.agdai'
        require(not any(n.endswith(suffix) for n in before), 'own target is warm')
        r=run_job('target'+str(index),[args.agda,'--no-libraries','-i','src','--safe','--without-K','--cubical-compatible',
                  '--save-metas','src/Tests/IndexedWire6/'+target+'.agda','+RTS','-M1350M','-c','-s','-RTS'],out/'records',
                  root=check,expected_source_sha256=source['source_sha256'],timeout=300,cpu_limit=min(120,left),rss_limit_gib=1.5,
                  log_limit_mib=2,metadata=dict(target=target,own_target_cold=True,rows_per_slice=50))
        after=assembly6.interfaces(check);phase=dict(target=target,record=r,borrowed_interfaces_unchanged=all(after.get(n)==h for n,h in before.items()))
        report['phases'].append(phase);report['kernel_cpu_seconds']+=r['cpu_seconds'];atomic_json(out/'interface-map.json',after)
        report['last_interface_pool_sha256']=digest_entries(after);save()
        require(r['accepted'] and phase['borrowed_interfaces_unchanged'],'slice target failed: '+target)
    require(source_identity(old)==source_old and assembly6.interfaces(old)==pool and assembly6.interfaces(family)==fp,
            'historical source or interface donor changed')
    report.update(accepted=True,status='complete',finished_utc=utc(),original_data_and_accepted_prefix_unchanged=True);save()
    print(json.dumps(dict(accepted=True,kernel_cpu_seconds=report['kernel_cpu_seconds'],initial_problem2_proved=False)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','family','output'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('agda','expected-agda-sha256','expected-previous-report-sha256','expected-previous-map-sha256',
                 'expected-family-report-sha256','expected-family-map-sha256'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--kernel-cpu-limit',type=float,default=450.)
    parser.add_argument('--reuse-context',type=Path,help='authenticate and reuse the accepted first context pilot')
    run(parser.parse_args())


if __name__=='__main__':main()
