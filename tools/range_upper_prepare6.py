"""Retarget the accepted10000-row Partial; check the generic UPPER fixture."""
import json
from pathlib import Path
import shutil
from sparse_citation_pilot6 import tree
from provenance import source_identity
from run_job import atomic_json,utc

ROOT=Path(__file__).resolve().parents[1]
DATA=Path('/mnt/data/othello-agda-desktop-artifacts-20261018/compact-global-probe6-20261018')
CORES=['Game/StepRangeAssembly','Othello/ConsecutiveRange6','Othello/ConsecutivePackedUpper6']
HEADER='{-# OPTIONS --safe --without-K --cubical-compatible #-}\n'


def prepare(out):
    out=Path(out);check=out/'check';assert not check.exists()
    for name in CORES:
        p=check/'src'/(name+'.agda');p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'src'/(name+'.agda'),p)
    sample=json.loads((DATA/'sample.json').read_text())
    chunks=sorted(map(int,sample['states']))
    groups={part:i//50 for i,part in enumerate(chunks)}
    owned=list(range(342,392));assert all(sample['states'][str(p)]['rows']==200 for p in owned)
    body='''open import Prelude
import Game.NatMap as M
import Othello.RowPacked6 as Packed
import Othello.ConsecutiveRange6 as Range
import Tests.CompactGlobalBatch6.Root as Global
import Tests.ConsecutiveGlobalBatch6.Closed as Existing
'''
    for g in sorted({groups[p] for p in owned}):body+=f'import Tests.CompactGlobalBatch6.Group{g} as G{g}\n'
    table=tree(owned,lambda p:f'(M.rows {200*p} 200 G{groups[p]}.p{p})',
        lambda p,l,r:f'(M.branch {200*p} {l} {r})')
    body+='owned : M.Map Packed.PackedState\nowned = '+table+'''
abstract
  partial : Range.A.Partial Global.G owned
  partial = Range.checked {G = Global.G} {base = 68400} {n = 10000}
    {target = owned} Existing.partial refl
-- This retargets coverage only; 52800 other represented rows remain unowned.
'''
    folder=check/'src/Tests/RangeUpper6';folder.mkdir(parents=True)
    (folder/'Retarget.agda').write_text(HEADER+'-- AI-assisted; reuse exact checked rows, no certificate rerun.\nmodule Tests.RangeUpper6.Retarget where\n'+body)
    (folder/'Upper.agda').write_text(HEADER+'''-- AI-assisted terminal fixture only; no initial upper bound claimed.
module Tests.RangeUpper6.Upper where
open import Prelude
open import Game.Core using (black)
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.NatMap as M
import Othello.Finite as F
import Othello.RowPacked6 as Packed
import Othello.ConsecutivePackedUpper6 as Rows
fallback : Packed.PackedState
fallback = Packed.packed (364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ F.[]) black
G : ℕ → Packed.PackedState
G _ = fallback
abstract
  partial : Rows.A.Partial G (M.rows 0 1 (Rows.ps G 0 1))
  partial = Rows.partial G 0 1 (B.cons D.indexedLeaf B.nil) refl
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        retargeted_existing_rows=10000,actual_owned_state_chunks=50,
        upper_terminal_fixture_rows=1,additional_wire_scans=0,new_native_solver_runs=0,
        initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
