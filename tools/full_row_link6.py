"""UNTRUSTED linkage of already checked LOWER rows to the accepted full map.

No Agda/native invocation; no new Boolean acceptance facts or initial theorem.
"""
import hashlib
from pathlib import Path
from initial_global_alignment6 import _prefix,_tree
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require


def emit(check,named,*,prefix='Tests.FullLowerLinked6',alignment='Tests.FullLowerAlignment6'):
    _prefix(prefix);_prefix(alignment)
    require(named['format']=='othello-initial-global-named6-v1' and named['side']=='lower'
            and named['prefix']=='Tests.InitialGlobalNamedLower'
            and named['sample_prefix']=='Tests.InitialLazyTrainingLower'
            and named['owned_rows']==3047 and named['needed_chunks']==2702,
            'exact accepted lower sample layout required')
    owned=named['owned_parts'];require(len(owned)==16 and owned==sorted(set(owned)),
            'sixteen distinct accepted parts required')
    check=Path(check).absolute()
    require(not check.exists() and 'results' in check.parts
            and not any(p.is_symlink() for p in (check,*check.parents)),
            'fresh private results root required')
    require(prefix not in (named['prefix'],named['sample_prefix'],alignment),
            'distinct linkage namespace required')
    common='''open import Prelude
import Game.NatMapLaws as Laws
import Game.Indexed as I
open import Othello.Board using (State; six)
'''
    sources={}
    def add(name,body):
        path='src/'+prefix.replace('.','/')+'/'+name+'.agda'
        sources[path]=(HEADER+'-- Link old row facts only; no new checker reduction.\nmodule '+prefix+'.'+name+' where\n\n'+body).encode()
    add('Model',common+f'''import {alignment}.Root as Aligned using (G; closed)
import {named['prefix']}.Model as Old using (globalStates; globalBodies)
G : ℕ → State six
G = Aligned.G
C : ℕ → I.IndexedCertificate ℕ
C = Laws.totalize Old.globalBodies I.indexedLeaf
sameStates : Laws.Compatible Old.globalStates G
sameStates = Aligned.closed
sameBodies : Laws.Compatible Old.globalBodies C
sameBodies = Laws.self-compatible Old.globalBodies I.indexedLeaf
''')
    for j in owned:
        add('Part'+str(j),common+f'''import {prefix}.Model as Model using (G; C; sameStates; sameBodies)
import {named['sample_prefix']}.Family as Family using (module A)
import {named['sample_prefix']}.Part{j} as Local using (states)
import {named['prefix']}.Part{j} as Accepted using (module AlignedModel)
abstract
  partial : Family.A.Partial Model.G Model.C Local.states
  partial = Accepted.AlignedModel.partial Model.G Model.C Model.sameStates Model.sameBodies
''')
    body=common+f'''import {prefix}.Model as Model using (G; C)
import {named['sample_prefix']}.Family as Family using (module A)
import {named['prefix']}.Model as Old using (ownedStates)
'''
    body+=''.join(f'import {prefix}.Part{j} as P{j} using (partial)\n' for j in owned)
    def combine(tree):
        if isinstance(tree,int):return f'P{tree}.partial'
        return f'(Family.A.join {{G = Model.G}} {{C = Model.C}} {tree[0]} {combine(tree[1])} {combine(tree[2])})'
    body+='''abstract
  partial : Family.A.Partial Model.G Model.C Old.ownedStates
  partial = '''+combine(_tree(owned))+'\n'
    add('Root',body)
    require(all(b'accepted = refl' not in raw and b'postulate' not in raw for raw in sources.values()),
            'new imported acceptance claim refused')
    check.mkdir(parents=True)
    for name,raw in sources.items():
        p=check/name;p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(raw)
    return dict(format='othello-full-lower-row-link-proposal6-v1',prefix=prefix,
        root_module=prefix+'.Root',parts=owned,existing_owned_rows=3047,
        generated_sha256={p:hashlib.sha256(b).hexdigest() for p,b in sources.items()},
        generated_bytes=sum(map(len,sources.values())),agda_acceptance_measured=False,
        new_game_rows_to_check=0,initial_problem2_proved=False,
        optimal_initial_pair_proved=False,production_authorized=False)


def run(current,out):
    """Bounded already-checked-fact assembly, under a separate scope approval."""
    import json
    import shutil
    import assembly6
    import full_map_pilot6 as pilot
    from full_map_alignment6 import FULL_SOURCE_SHA,FULL_POOL_SHA
    from provenance import source_identity,digest_entries
    from readonly_dependencies6 import command
    from run_job import atomic_json,build_lock,run_job,utc
    full=pilot.GENERATED/'check'
    aligned=pilot.BASE/'six-full-map-lower-alignment-20261016/results/full-map-pilot6/check'
    expected_aligned_source='1ba50cc7e5c94ee9b0e43dde0b417264bf252adb5704d9a5a7d6ec6a9d219a39'
    expected_aligned_pool='d97befd01b6db69e6262fc9ca94e0ffa8f7fa185dc831c5fcfc466d8505324ea'
    with build_lock(full),build_lock(pilot.DONOR),build_lock(aligned):
        prior,donor_source,donor_pool,machine=pilot.donor_identity()
        full_source=source_identity(full);full_pool=assembly6.interfaces(full)
        aligned_source=source_identity(aligned);aligned_pool=assembly6.interfaces(aligned)
        require(full_source['source_sha256']==FULL_SOURCE_SHA and digest_entries(full_pool)==FULL_POOL_SHA
                and aligned_source['source_sha256']==expected_aligned_source
                and digest_entries(aligned_pool)==expected_aligned_pool,
                'exact accepted full-map and alignment donors required')
        check=out/'check';layout=emit(check,prior['layout'])
        shutil.copy2(current/'othello.agda-lib',check/'othello.agda-lib')
        source=source_identity(check)
        report=dict(format='othello-full-lower-row-link6-v1',accepted=False,status='checking',
            layout=layout,checked_source=source,machine=machine,donor_source=donor_source,
            full_source=full_source,aligned_source=aligned_source,
            original_row_proofs_rechecked=0,new_game_rows_checked=0,reused_row_facts=3047,
            initial_problem2_proved=False,optimal_initial_pair_proved=False,
            production_authorized=False,created_utc=utc())
        atomic_json(out/'row-link-report.json',report)
        argv=command(machine,layout['root_module'],check,pilot.DONOR)
        i=argv.index('--')+1
        argv[i+4:i+4]=['-i',str(full/'src'),'-i',str(aligned/'src')]
        argv[argv.index('-M2700M')]='-M10G'
        rec=run_job('row-link',argv,out/'row-link-records',root=check,
            expected_source_sha256=source['source_sha256'],timeout=500,cpu_limit=250,
            rss_limit_gib=11.5,log_limit_mib=4,
            metadata=dict(checker_binary_sha256=pilot.AGDA_SHA,own_target_cold=True,
                original_row_proofs_rechecked=0,new_game_rows_checked=0,
                initial_problem2_proved=False,production_authorized=False))
        unchanged=(source_identity(full)==full_source and assembly6.interfaces(full)==full_pool
            and source_identity(aligned)==aligned_source and assembly6.interfaces(aligned)==aligned_pool
            and source_identity(pilot.DONOR)==donor_source and assembly6.interfaces(pilot.DONOR)==donor_pool)
        own=assembly6.interfaces(check);atomic_json(out/'row-link-interface-map.json',own)
        report.update(record=rec,borrowed_sources_interfaces_unchanged=unchanged,
            own_interfaces=len(own),own_interface_pool_sha256=digest_entries(own),
            accepted=bool(rec['accepted'] and unchanged),
            status='complete' if rec['accepted'] and unchanged else 'not-accepted',
            storage=pilot.storage(current),finished_utc=utc())
        atomic_json(out/'row-link-report.json',report)
        require(report['accepted'],'row linkage did not pass; accepted donors preserved')
