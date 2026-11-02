"""Reuse authenticated full state data; explicit map arguments, no new scans."""
import json
from pathlib import Path
import shutil
from provenance import source_identity
from run_job import atomic_json,utc
from full_upper_prepare6 import COMMON,HEADER

ROOT=Path(__file__).resolve().parents[1]
PREFIX='Tests.FullUpperRecovered6'
OLD='Tests.FullUpperPacked6'


def prepare(out):
    out=Path(out);donor=out.with_name('full-upper-probe6-20261018')/'check'
    check=out/'check';assert not check.exists();folder=check/'src/Tests/FullUpperRecovered6';folder.mkdir(parents=True)
    core=check/'src/Game/EncodedMapClosure.agda';core.parent.mkdir(parents=True)
    shutil.copy2(ROOT/'src/Game/EncodedMapClosure.agda',core)
    aligned=check/'src/Othello/FullUpperAlign6.agda';aligned.parent.mkdir(parents=True)
    aligned.write_text((donor/'src/Game/NatMapCheck.agda').read_text().replace('module Game.NatMapCheck where','module Othello.FullUpperAlign6 where'))
    for name in ['Rows6','Rows652','Body6','Body652','Compatible']:
        source=(donor/'src/Tests/FullUpperPacked6'/(name+'.agda')).read_text()
        source=source.replace('module '+OLD+'.'+name,'module '+PREFIX+'.'+name)
        if name.startswith('Rows'):source=source.replace('import '+OLD+'.Body','import '+PREFIX+'.Body')
        if name=='Compatible':source=source.replace('import Game.NatMapCheck as Align','import Othello.FullUpperAlign6 as Align')
        (folder/(name+'.agda')).write_text(source)
    groups=654
    imports=''.join(f'import {OLD}.Group{g} as G{g}\n' for g in range(groups))
    body=COMMON+f'''import Othello.ConsecutivePackedUpper6 as Rows
import {OLD}.Root as Global
import Game.EncodedMapClosure as Closure
open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.InlineEntries6 as Rules
module Close = Closure.Closure Packed.decode Rules.specializedGame6 black (upperGoal 4)
'''+imports+'''record CheckedParts : Set where
  field
'''
    for g in range(groups):body+=f'    part{g} : Rows.A.Partial Global.G G{g}.table\n'
    def assemble(lo,hi):
        if hi-lo==1:return f'G{lo}.table',f'(CheckedParts.part{lo} accepted)'
        middle=(lo+hi)//2;l,lp=assemble(lo,middle);r,rp=assemble(middle,hi)
        return f'(M.branch {10000*middle} {l} {r})', f'(Rows.A.join {{G = Global.G}} {{l = {l}}} {{r = {r}}} {10000*middle} {lp} {rp})'
    _,proof=assemble(0,groups)
    body+='''abstract
  assemble : CheckedParts → Rows.A.Partial Global.G Global.table
  assemble accepted = '''+proof+'''
  complete : CheckedParts → ∀ key →
    Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (Global.G key))
  complete accepted = Close.finish Global.table Global.fallback Global.fallback-won (assemble accepted)
-- All654 CheckedParts fields remain required; no complete map is supplied here.
'''
    (folder/'Assembly.agda').write_text(HEADER+'-- AI-assisted explicit map composition; checked data reused exactly.\nmodule '+PREFIX+'.Assembly where\n'+body)
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    old=json.loads((out.with_name('full-upper-probe6-20261018')/'emission.json').read_text())
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        cases=old['cases'],full_state_rows=6530011,data_groups=654,tested_owner_rows=20000,
        reused_data_interfaces=655,additional_zip_scans=0,new_native_solver_runs=0,
        explicit_G_and_both_maps_in_every_join=True,generic_closure_abstract=True,
        full_row_coverage_proved=False,initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
