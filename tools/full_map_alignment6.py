"""UNTRUSTED map-only compatibility bridge; never checks game-certificate rows."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import fcntl

import assembly6
import full_map_pilot6 as pilot
from initial_global_alignment6 import _tree
from provenance import source_identity,digest_entries
from readonly_dependencies6 import command
from run_job import atomic_json,build_lock,run_job,utc
from wire_workflow6 import require

FULL_SOURCE_SHA='89af60afb7ffa45b64af8984e8efff695df98e34cf3e4305cc1c780f1bfc4839'
FULL_POOL_SHA='0a9eff6c999bba736a63186e3a9008b2783fa34432a7546304d9ef75fd708e7c'
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'
PREFIX='Tests.FullLowerAlignment6'


def route(low,high,j):
    require(type(low) is int and type(high) is int and type(j) is int
            and 0 <= low <= j < high,'invalid bounded route interval')
    if high-low==1:return 'R.here'
    mid=(low+high)//2
    return ('(R.left refl '+route(low,mid,j)+')' if j<mid
            else '(R.right refl '+route(mid,high,j)+')')


def emit(check, full, named):
    require(not check.exists() and full['complete'] and full['rows']==6873047
            and full['parts']==34366 and full['rows_per_part']==200
            and full['prefix']=='Tests.FullInitialLower6','complete pinned full lower map required')
    needed=named['needed_parts']
    require(named['side']=='lower' and len(needed)==2702
            and needed==sorted(set(needed)),'exact lower demand map required')
    chunks={c['part']:c for c in full['chunks']}
    expected={j:named['sample_prefix']+'.StateData'+str(j) for j in needed}
    require(all(chunks[j]['module']==module and str(j) in full['reused_chunks']
            for j,module in expected.items()),'reused lower literals must name the same accepted source')
    candidates=[h['target'] for h in named['map_helpers'] if h['kind']=='states' and h['parts']==needed]
    require(len(candidates)==1,'one exact sparse map root required')
    check.mkdir(parents=True)
    root=Path(__file__).resolve().parents[1]
    shutil.copy2(root/'othello.agda-lib',check/'othello.agda-lib')
    (check/'src/Game').mkdir(parents=True)
    shutil.copy2(root/'src/Game/NatMapRoute.agda',check/'src/Game/NatMapRoute.agda')
    sources={}
    common='''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapRoute as R
import Othello.LazyIndexed6 as Lazy using (states)
open import Othello.Board using (State; six; initial)
import Tests.FullInitialLower6.Root as Full using (stateMap)
'''
    owner={}
    def add(name,body):
        p='src/'+PREFIX.replace('.','/')+'/'+name+'.agda'
        raw=(HEADER+'-- Map compatibility only; zero game rows.\nmodule '+PREFIX+'.'+name+' where\n\n'+body).encode()
        require(sum(map(len,sources.values()))+len(raw)<8*2**20,'alignment source byte cap reached')
        sources[p]=raw
    for start in range(0,len(needed),32):
        batch=needed[start:start+32];name='Batch'+str(start//32)
        body=common+''.join('import '+expected[j]+' as S'+str(j)+' using (text)\n' for j in batch)
        for j in batch:
            n=chunks[j]['rows'];base=200*j;xs=f'(Lazy.states {n} S{j}.text)'
            body+=f'''path{j} : R.Route Full.stateMap {base} {n} {xs}
path{j} = {route(0,34366,j)}
aligned{j} : ∀ G → Laws.Compatible Full.stateMap G →
  Laws.Aligned (M.rows {base} {n} {xs}) G
aligned{j} G same = R.aligned G path{j} same
compatible{j} : ∀ G → Laws.Compatible Full.stateMap G →
  Laws.Compatible (M.rows {base} {n} {xs}) G
compatible{j} G same = R.compatible G path{j} same
'''
            owner[j]=name
        add(name,body)
    body=common+'import '+named['prefix']+'.'+candidates[0]+' as Sparse using (map)\n'
    body+=''.join('import '+PREFIX+'.Batch'+str(i)+' as B'+str(i)+'\n' for i in range((len(needed)+31)//32))
    def combine(tree):
        if isinstance(tree,int):
            return '(B'+owner[tree][5:]+'.compatible'+str(tree)+' G same)'
        return '(R.join-compatible '+str(tree[0])+' '+combine(tree[1])+' '+combine(tree[2])+')'
    body+='''symbolic : ∀ G → Laws.Compatible Full.stateMap G → Laws.Compatible Sparse.map G
symbolic G same = '''+combine(_tree(needed))+'''
G : ℕ → State six
G = Laws.totalize Full.stateMap (initial six)
abstract
  closed : Laws.Compatible Sparse.map G
  closed = symbolic G (Laws.self-compatible Full.stateMap (initial six))
'''
    add('Root',body)
    for name,raw in sources.items():
        p=check/name;p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(raw)
    all_sources={p.relative_to(check).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in check.rglob('*') if p.is_file()}
    return dict(prefix=PREFIX,root_module=PREFIX+'.Root',batches=(len(needed)+31)//32,
        aligned_chunks=len(needed),aligned_encoded_rows=sum(chunks[j]['rows'] for j in needed),
        generated_sha256=all_sources,game_rows_checked=0,initial_problem2_proved=False)


def run(current,out):
    full_check=pilot.GENERATED/'check'
    report=dict(format='othello-full-lower-alignment6-v1',accepted=False,status='preflight',
        game_rows_checked=0,initial_problem2_proved=False,optimal_initial_pair_proved=False,
        production_authorized=False,created_utc=utc())
    with build_lock(full_check),build_lock(pilot.DONOR):
        prior,donor_source,donor_pool,machine=pilot.donor_identity()
        full_source=source_identity(full_check);full_pool=assembly6.interfaces(full_check)
        require(full_source['source_sha256']==FULL_SOURCE_SHA and digest_entries(full_pool)==FULL_POOL_SHA,
                'accepted complete map source/cache changed')
        manifest=json.loads((full_check/'results/full-state-map6.json').read_text())
        check=out/'check';layout=emit(check,manifest,prior['layout']);source=source_identity(check)
        atomic_json(out/'generated.json',layout)
        report.update(layout=layout,checked_source=source,full_source=full_source,
            full_interface_pool_sha256=FULL_POOL_SHA,donor_source=donor_source,
            donor_interface_pool_sha256=digest_entries(donor_pool),machine=machine,status='checking')
        atomic_json(out/'alignment-report.json',report)
        argv=command(machine,layout['root_module'],check,pilot.DONOR)
        i=argv.index('--')+1
        argv[i+4:i+4]=['-i',str(full_check/'src')]
        argv[argv.index('-M2700M')]='-M10G'
        rec=run_job('map-alignment',argv,out/'alignment-records',root=check,
            expected_source_sha256=source['source_sha256'],timeout=1300,cpu_limit=900,
            rss_limit_gib=11.5,log_limit_mib=8,
            metadata=dict(checker_binary_sha256=pilot.AGDA_SHA,own_target_cold=True,
                          game_rows_checked=0,initial_problem2_proved=False))
        unchanged=(source_identity(full_check)==full_source and assembly6.interfaces(full_check)==full_pool
            and source_identity(pilot.DONOR)==donor_source and assembly6.interfaces(pilot.DONOR)==donor_pool)
        own_pool=assembly6.interfaces(check);atomic_json(out/'alignment-interface-map.json',own_pool)
        report.update(record=rec,borrowed_sources_interfaces_unchanged=unchanged,
            own_interface_pool_sha256=digest_entries(own_pool),own_interfaces=len(own_pool),
            accepted=bool(rec['accepted'] and unchanged),status='complete' if rec['accepted'] and unchanged else 'not-accepted',
            storage=pilot.storage(current),finished_utc=utc())
        atomic_json(out/'alignment-report.json',report)
        require(report['accepted'],'map alignment did not pass; data and accepted interfaces retained')
