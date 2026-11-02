"""AI-assisted arithmetic-state comparison; existing rows, no native solver."""
import hashlib,json
from pathlib import Path
import completion_batch6 as prior
from provenance import source_identity
from run_job import atomic_json,utc
from sparse_citation_pilot6 import tree
from direct_rows_probe6 import HEADER


def emit(check,finite=False):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    pins={}
    for rel in ['Game/BooleanUIP.agda','Othello/RowArithmetic6.agda','Othello/ArithmeticState6.agda','Othello/ArithmeticGame6.agda','Othello/ArithmeticRows6.agda']+(['Othello/FiniteCheck6.agda'] if finite else []):
        source=prior.ROOT/'src'/rel;raw=source.read_bytes()
        assert all(f.encode() in raw.splitlines()[0] for f in ['--safe','--without-K','--cubical-compatible'])
        target=check/'src'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pins[str(source)]=hashlib.sha256(raw).hexdigest()
    sample=json.loads((prior.OUT/'sample.json').read_text());case=next(c for c in sample['cases'] if c['part']==33154)
    keys=sorted(set(case['references']))
    refs='''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Othello.ArithmeticState6 as S
import Tests.RowPackedProbe6.RefData as Old
'''
    for key in keys:
        refs+=f's{key} : S.Coded\ns{key} = S.coded Old.s{key} refl\n'
    expression=tree(keys,lambda k:f'(M.rows {k} 1 (B.cons s{k} B.nil))',lambda pivot,l,r:f'(M.branch {pivot} {l} {r})')
    refs+='demand : M.Map S.Coded\ndemand = '+expression+'\n'
    old=prior.ROOT/'results/row-packed-probe6-20261018-fixed/check/src/Tests/RowPackedProbe6/Variant.agda'
    baseline=old.read_text().replace('module Tests.RowPackedProbe6.Variant where','module Tests.ArithmeticGameProbe6.Baseline where')
    variant=baseline.replace('Tests.ArithmeticGameProbe6.Baseline','Tests.ArithmeticGameProbe6.Variant')
    variant=variant.replace('import Othello.RowPackedIndexed6 as Rows','import Othello.ArithmeticRows6 as Rows')
    variant=variant.replace('import Othello.RowPacked6 as Packed','import Othello.ArithmeticState6 as Packed')
    variant=variant.replace('Tests.RowPackedProbe6.RefData as Refs','Tests.ArithmeticGameProbe6.RefData as Refs')
    variant=variant.replace('ss : B.Vec (State six) 200\nss = Lazy.states 200 Own.text','''packVec : ∀ {n} → B.Vec (State six) n → B.Vec Packed.Coded n
packVec B.nil = B.nil
packVec (B.cons s ss) = B.cons (Packed.pack s) (packVec ss)
ss : B.Vec Packed.Coded 200
ss = packVec (Lazy.states 200 Own.text)''')
    variant=variant.replace('Packed.PackedState','Packed.Coded')
    variant=variant.replace('Check.V.Old.TreeOK (λ j → Packed.decode (G j))','Check.V.TreeOK G')
    folder=check/'src/Tests/ArithmeticGameProbe6';folder.mkdir(parents=True)
    for name,body in [('RefData',HEADER+'-- AI-assisted exact canonical code checks.\nmodule Tests.ArithmeticGameProbe6.RefData where\n'+refs),('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-arithmetic-game6-sources-v1',created_utc=utc(),copied_core_sha256=pins,existing_rows=200,new_distinct_rows=0,native_solver_executed=False,working_states_are_certified_six_nat_codes=True,arbitrary_canonical_state_refinement_required=True,exact_row_read_cases=4374,exact_row_replace_cases=13122,mathematical_objective_complete=False))
    return source_identity(check)
