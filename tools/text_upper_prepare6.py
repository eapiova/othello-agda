"""Same full UPPER strings, direct state lookup and existing body data."""
import json
from pathlib import Path
import re
import shutil
from sparse_citation_pilot6 import tree
from provenance import source_identity
from run_job import atomic_json,utc
from full_upper_prepare6 import HEADER

ROOT=Path(__file__).resolve().parents[1]
OLD='Tests.FullUpperPacked6'
PREFIX='Tests.TextUpperPacked6'
CORES=['DirectPackedText6','TextStateMap6','TextStateAssembly6']


def core(out):
    out=Path(out);check=out/'check';assert not check.exists()
    for name in CORES:
        target=check/'src/Othello'/(name+'.agda');target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/'src/Othello'/(name+'.agda'),target)
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission-core.json',dict(created_utc=utc(),source=source_identity(check)))


def data(out):
    out=Path(out);check=out/'check';donor=out.with_name('full-upper-probe6-20261018')/'check'
    folder=check/'src/Tests/TextUpperPacked6';folder.mkdir(parents=True)
    def add(name,body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted data/proofs; global ownership remains explicit.\nmodule '+PREFIX+'.'+name+' where\n'+body)
    counts=rows=0
    for group in range(654):
        text=(donor/'src/Tests/FullUpperPacked6'/(f'Group{group}.agda')).read_text()
        matches=re.findall(r'^p([0-9]+) = Text.states ([0-9]+) (".*")$',text,re.M)
        assert len(matches)==(50 if group<653 else 1)
        body='open import Agda.Builtin.String using (String)\nimport Othello.TextStateMap6 as T\n'
        parts=[]
        for raw,n,literal in matches:
            p=int(raw);n=int(n);value=json.loads(literal)
            assert p==counts and len(value)==7*n
            body+=f't{p} : String\nt{p} = '+json.dumps(value,ensure_ascii=False)+'\n'
            parts.append((p,n));counts+=1;rows+=n
        table=tree(parts,lambda p:f'(T.rows {200*p[0]} {p[1]} t{p[0]})',
            lambda p,l,r:f'(T.branch {200*p[0]} {l} {r})')
        add('Group'+str(group),body+'table : T.Map\ntable = '+table+'\n')
    assert counts==32651 and rows==6530011
    imports=''.join(f'import {PREFIX}.Group{g} as G{g}\n' for g in range(654))
    common='''open import Prelude
open import Game.Core using (black)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (upperGoal)
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.InlineEntries6 as Rules
module Parts = Assembly.Assembly black (upperGoal 4)
'''
    table=tree(list(range(654)),lambda g:f'G{g}.table',lambda g,l,r:f'(T.branch {10000*g} {l} {r})')
    add('Root',common+imports+'''open import Game.Certificate using (leaf)
import Othello.Finite as F
table : T.Map
table = '''+table+'''
fallback : Packed.PackedState
fallback = Packed.packed (364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ 364 F.∷ F.[]) black
G : ℕ → Packed.PackedState
G = T.totalize table fallback
abstract
  fallback-won : Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode fallback)
  fallback-won = leaf , refl
''')
    for g in [6,652]:
        old=(donor/'src/Tests/FullUpperPacked6'/(f'Body{g}.agda')).read_text()
        (folder/(f'Body{g}.agda')).write_text(old.replace('module '+OLD+'.Body','module '+PREFIX+'.Body'))
        base=10000*g
        add('Rows'+str(g),common+f'''import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.ConsecutivePackedUpper6 as Rows
import Othello.UnicodeCompact6 as Codec
import {PREFIX}.Root as Global
import {PREFIX}.Group{g} as Own
import {PREFIX}.Body{g} as Body
abstract
  source : Rows.A.Partial Global.G (M.rows {base} 10000 (Rows.ps Global.G {base} 10000))
  source = Rows.partial Global.G {base} 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {{G = Global.G}} {{base = {base}}} {{n = 10000}}
    {{xs = Rows.ps Global.G {base} 10000}} {{target = Own.table}}
    (Rows.lookup-ps Global.G {base} 10000) source
    (Range.check-sound {base} 10000 (T.domain Own.table) refl)
''')
    body=common+f'import {PREFIX}.Root as Global\n'+imports+'''record CheckedParts : Set where
  field
'''
    for g in range(654):body+=f'    part{g} : Parts.Partial Global.G G{g}.table\n'
    def compose(lo,hi):
        if hi-lo==1:return f'G{lo}.table',f'(CheckedParts.part{lo} accepted)'
        middle=(lo+hi)//2;l,lp=compose(lo,middle);r,rp=compose(middle,hi)
        return f'(T.branch {10000*middle} {l} {r})',f'(Parts.join {{G = Global.G}} {{l = {l}}} {{r = {r}}} {10000*middle} {lp} {rp})'
    _,joined=compose(0,654)
    add('Assembly',body+'''abstract
  assemble : CheckedParts → Parts.Partial Global.G Global.table
  assemble accepted = '''+joined+'''
  complete : CheckedParts → ∀ key → Proven Rules.specializedGame6 black (upperGoal 4) (Packed.decode (Global.G key))
  complete accepted = Parts.finish Global.table Global.fallback Global.fallback-won (assemble accepted)
-- CheckedParts is still an explicit premise; initial bounds remain open.
''')
    add('Compatible',common+'''import Othello.FullUpperAlign6 as Align
import Tests.InlineUpperPrefixes6.Data as PrefixData
import Tests.InlineUpperPrefixes6.Closed as Prefix
import Tests.TextUpperPacked6.Root as Global
module Check = Align.Checking Packed.equal Packed.equal-sound
abstract
  compatible : Prefix.Check.Local.V.Compatible PrefixData.L Global.G
  compatible = Check.compatible-sound PrefixData.demand Global.G refl
''')
    add('Load',common+'''import Tests.TextUpperPacked6.Root as Global
G : ℕ → Packed.PackedState
G = Global.G
''')
    old=json.loads((out.with_name('full-upper-probe6-20261018')/'emission.json').read_text())
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),cases=old['cases'],
        full_state_rows=rows,data_groups=654,text_chunks=counts,tested_owner_rows=20000,
        every_state_string_literal_reused_exactly=True,certificates_reused_exactly=True,
        additional_zip_scans=0,new_native_solver_runs=0,previous_vector_map_coverage_not_added=True,
        full_row_coverage_proved=False,initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    assert len(sys.argv)==3 and sys.argv[1] in ['core','data']
    globals()[sys.argv[1]](Path(sys.argv[2]))
