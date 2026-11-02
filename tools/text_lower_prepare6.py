"""Full LOWER direct-text map and conditional composition from the pinned old wire.

This is untrusted data preparation. Only Agda accepts rows or resolver alignment.
No native solver is called and the protected input is never opened for writing.
"""
import json, shutil
from pathlib import Path
import bench6
import compact_shared6 as compact
from compact_global_prepare6 import row_text
from directed_probe6 import converted
from native_layout_samples6 import convert_body
from sparse_citation_pilot6 import tree
from unicode_codec_probe6 import encode
from wire_part_samples6 import _records, _fingerprint
from provenance import source_identity
from run_job import atomic_json, utc

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Tests.TextLowerPacked6'
ROWS = 6873047
TRAIN, HOLDOUT = 6, 686
HEADER = '{-# OPTIONS --safe --without-K --cubical-compatible -WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n'
COMMON = '''open import Prelude
open import Game.Core using (white)
open import Game.Symmetry using (Proven)
open import Othello.Statements using (lowerGoal)
import Othello.RowPacked6 as Packed
import Othello.TextStateMap6 as T
import Othello.TextStateAssembly6 as Assembly
import Othello.InlineEntries6 as Rules
module Parts = Assembly.Assembly white (lowerGoal 4)
'''


def prepare(out):
    out = Path(out); request = json.loads((out/'input-request.json').read_text())
    wire = Path(request['wire']); assert wire.is_file() and not wire.is_symlink()
    assert wire.stat().st_size == request['wire_bytes'] <= 512*2**20
    assert request['wire_rows'] == ROWS
    identity = _fingerprint(wire.stat()); assert list(identity) == request['wire_fingerprint']
    check = out/'check'; assert not check.exists()
    folder = check/'src/Tests/TextLowerPacked6'; folder.mkdir(parents=True)
    def add(name, body):
        (folder/(name+'.agda')).write_text(HEADER+'-- AI-assisted data/proofs; every row ownership remains explicit.\nmodule '+PREFIX+'.'+name+' where\n'+body)
    selected = {TRAIN:[], HOLDOUT:[]}; wanted = set(); references_count = 0
    chunk = []; group_parts = []; group_body = ''; chunks = 0
    for rank, state, body, refs in _records(wire, request['wire_sha256'], ROWS, identity):
        chunk.append(state.decode('ascii')); group = rank//10000
        if group in selected:
            keys = [refs[j:j+13] for j in range(0,len(refs),13)]
            wanted.update(keys); references_count += len(keys)
            assert len(wanted) <= 300000 and references_count <= 1000000
            selected[group].append((rank,state.decode('ascii'),body.decode('ascii'),keys))
        if len(chunk) == 200 or rank+1 == ROWS:
            part = rank//200; n = len(chunk); literal = row_text(''.join(chunk))
            assert len(literal) == 7*n and part == chunks
            group_body += f't{part} : String\nt{part} = '+json.dumps(literal,ensure_ascii=False)+'\n'
            group_parts.append((part,n)); chunks += 1; chunk = []
            if len(group_parts) == 50 or rank+1 == ROWS:
                table = tree(group_parts,lambda p:f'(T.rows {200*p[0]} {p[1]} t{p[0]})',
                    lambda p,l,r:f'(T.branch {200*p[0]} {l} {r})')
                add('Group'+str(group),'open import Agda.Builtin.String using (String)\nimport Othello.TextStateMap6 as T\n'+group_body+'table : T.Map\ntable = '+table+'\n')
                group_parts = []; group_body = ''
    assert chunks == 34366 and all(len(v)==10000 for v in selected.values())
    found = {}
    for rank,state,_,_ in _records(wire,request['wire_sha256'],ROWS,identity):
        if state in wanted:
            assert state not in found; found[state] = rank
    assert found.keys() == wanted
    groups = (ROWS+9999)//10000
    imports = ''.join(f'import {PREFIX}.Group{g} as G{g}\n' for g in range(groups))
    table = tree(list(range(groups)),lambda g:f'G{g}.table',lambda g,l,r:f'(T.branch {10000*g} {l} {r})')
    add('Root',COMMON+imports+'''open import Game.Certificate using (leaf)
import Othello.Finite as F
table : T.Map
table = '''+table+'''
fallback : Packed.PackedState
fallback = Packed.packed (728 F.∷ 728 F.∷ 728 F.∷ 728 F.∷ 728 F.∷ 728 F.∷ F.[]) white
G : ℕ → Packed.PackedState
G = T.totalize table fallback
abstract
  fallback-won : Proven Rules.specializedGame6 white (lowerGoal 4) (Packed.decode fallback)
  fallback-won = leaf , refl
''')
    cases = {}
    for group, rows in selected.items():
        texts = []; tokens = 0; counts = {}
        for rank,state,body,keys in rows:
            ids = [found[k] for k in keys]; assert all(j<rank for j in ids)
            numeric,n = convert_body(body,ids); tokens += n
            directed,new = converted(numeric,[bench6.decode(compact.unpack_state(state))],text_output=True)
            texts.append(encode(directed[0]))
            for k,v in new.items(): counts[k] = counts.get(k,0)+v
        assert tokens <= 500000
        add('Body'+str(group),'open import Agda.Builtin.String using (String)\ntext : String\ntext = '+json.dumps(''.join(texts),ensure_ascii=False)+'\n')
        base=10000*group
        add('Rows'+str(group),COMMON+f'''import Game.NatMap as M
import Game.StepRangeAssembly as Range
import Othello.ConsecutivePackedRows6 as Rows
import Othello.UnicodeCompact6 as Codec
import {PREFIX}.Root as Global
import {PREFIX}.Group{group} as Own
import {PREFIX}.Body{group} as Body
abstract
  source : Rows.A.Partial Global.G (M.rows {base} 10000 (Rows.ps Global.G {base} 10000))
  source = Rows.partial Global.G {base} 10000 (Codec.bodies 10000 Body.text) refl
  partial : Parts.Partial Global.G Own.table
  partial = Parts.from-rows {{G = Global.G}} {{base = {base}}} {{n = 10000}}
    {{xs = Rows.ps Global.G {base} 10000}} {{target = Own.table}}
    (Rows.lookup-ps Global.G {base} 10000) source
    (Range.check-sound {base} 10000 (T.domain Own.table) refl)
''')
        cases[str(group)] = dict(rows=10000,tokens=tokens,counts=counts)
    add('Compatible',COMMON+'''import Othello.FullUpperAlign6 as Align
import Tests.InlineLowerPrefixes6.Data as PrefixData
import Tests.InlineLowerPrefixes6.Closed as Prefix
import Tests.TextLowerPacked6.Root as Global
module Check = Align.Checking Packed.equal Packed.equal-sound
abstract
  compatible : Prefix.Check.Local.V.Compatible PrefixData.L Global.G
  compatible = Check.compatible-sound PrefixData.demand Global.G refl
''')
    add('Load',COMMON+f'import {PREFIX}.Root as Global\nG : ℕ → Packed.PackedState\nG = Global.G\n')
    boxed = COMMON.replace('Othello.TextStateAssembly6 as Assembly','Othello.TextCertifiedAssembly6 as Assembly')
    body = boxed+f'import {PREFIX}.Root as Global\n'+imports+'''module Generic (G : ℕ → Packed.PackedState) where
  record CheckedParts : Set where
    field
'''
    for g in range(groups): body += f'      part{g} : Parts.Certified G G{g}.table\n'
    def compose(lo,hi):
        if hi-lo==1:return f'G{lo}.table',f'(CheckedParts.part{lo} accepted)'
        mid=(lo+hi)//2; l,lp=compose(lo,mid); r,rp=compose(mid,hi)
        return f'(T.branch {10000*mid} {l} {r})',f'(Parts.join {{G = G}} {{l = {l}}} {{r = {r}}} {10000*mid} {lp} {rp})'
    _,joined=compose(0,groups)
    body += '''  abstract
    assemble : CheckedParts → Parts.Certified G Global.table
    assemble accepted = '''+joined+'''
module Actual = Generic Global.G
abstract
  complete : Actual.CheckedParts → Parts.ProvenMap Global.G
  complete accepted = Parts.finish Global.table Global.fallback Global.fallback-won (Actual.assemble accepted)
-- All688 actual certified fields remain premises; this is conditional closure.
'''
    add('Assembly',body)
    add('Samples',boxed+f'''import {PREFIX}.Root as Global
import {PREFIX}.Group{TRAIN} as GT
import {PREFIX}.Group{HOLDOUT} as GH
import {PREFIX}.Rows{TRAIN} as RT
import {PREFIX}.Rows{HOLDOUT} as RH
abstract
  training : Parts.Certified Global.G GT.table
  training = Parts.certify Global.G GT.table RT.partial
  heldout : Parts.Certified Global.G GH.table
  heldout = Parts.certify Global.G GH.table RH.partial
''')
    add('Joint', '''open import Prelude
open import Game.Core using (white; black)
open import Othello.Statements using (lowerGoal; upperGoal; Problem2)
import Othello.RowPacked6 as Packed
import Othello.TextCertifiedAssembly6 as Box
import Tests.InlineLowerPrefixes6.Joint as PrefixJoint
import Tests.InlineLowerPrefixes6.Closed as LowerPrefix
import Tests.InlineLowerPrefixes6.Data as LowerData
import Tests.InlineUpperPrefixes6.Closed as UpperPrefix
import Tests.InlineUpperPrefixes6.Data as UpperData
import Tests.TextLowerPacked6.Root as Lower
import Tests.TextLowerPacked6.Assembly as LowerAssembly
import Tests.TextLowerPacked6.Compatible as LowerCompatible
import Tests.TextUpperPacked6.Root as Upper
import Tests.ParametricFullUpper6.Assembly as UpperAssembly
import Tests.TextUpperPacked6.Compatible as UpperCompatible
module L = Box.Assembly white (lowerGoal 4)
module U = Box.Assembly black (upperGoal 4)
abstract
  bridge : (GL GU : ℕ → Packed.PackedState) →
    LowerPrefix.Check.Local.V.Compatible LowerData.L GL →
    UpperPrefix.Check.Local.V.Compatible UpperData.L GU →
    L.ProvenMap GL → U.ProvenMap GU → Problem2
  bridge GL GU lc uc lp up =
    PrefixJoint.problem2-from-complete-maps GL GU lc uc (L.at lp) (U.at up)
  complete : LowerAssembly.Actual.CheckedParts → UpperAssembly.Actual.CheckedParts → Problem2
  complete lower upper = bridge Lower.G Upper.G
    LowerCompatible.compatible UpperCompatible.compatible
    (LowerAssembly.complete lower) (UpperAssembly.complete upper)
-- No CheckedParts record is supplied. The initial6x6 theorem is still open.
''')
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    assert _fingerprint(wire.stat()) == identity
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        full_state_rows=ROWS,data_groups=groups,text_chunks=chunks,cases=cases,
        tested_owner_rows=20000,training_group=TRAIN,heldout_group=HOLDOUT,
        indexed_reference_states=len(found),reference_occurrences=references_count,
        whole_authenticated_wire_scans=2,wire_unchanged=True,new_native_solver_runs=0,
        source_bytes=sum(p.stat().st_size for p in (check/'src').rglob('*.agda')),
        previous_different_map_coverage_not_added=True,full_row_coverage_proved=False,
        initial_bounds_proved=False,mathematical_objective_complete=False))


if __name__=='__main__':
    import sys
    prepare(Path(sys.argv[1]))
