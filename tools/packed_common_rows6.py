"""Close the sampled1000-row Steps on one common encoded map; no solver."""
import hashlib
import json
from pathlib import Path
import shutil

from big_rows_scaling6 import BUNDLES, _packed_leaf
from provenance import source_identity
from run_job import atomic_json, utc
from sparse_citation_pilot6 import tree
from text_map_scaling6 import word

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Tests.PackedCommonRows6'
HEADER = ('{-# OPTIONS --safe --without-K --cubical-compatible '
          '-WnoUnsupportedIndexedMatch -WnoRewritesNothing #-}\n')


def emit(out):
    out = Path(out)
    request = json.loads((out/'input-request.json').read_text())
    sample_path = Path(request['sample'])
    assert hashlib.sha256(sample_path.read_bytes()).hexdigest() == request['sample_sha256']
    sample = json.loads(sample_path.read_text())
    assert sample['input_unchanged'] and sample['wire_scans'] == 2
    check = out/'check'
    assert not check.exists()
    folder = check/'src/Tests/PackedCommonRows6'
    folder.mkdir(parents=True)
    generic = ROOT/'src/Othello/PackedVectors6.agda'
    target = check/'src/Othello/PackedVectors6.agda'
    target.parent.mkdir(parents=True)
    shutil.copy2(generic, target)
    map_check = ROOT/'src/Game/NatMapCheck.agda'
    target_check = check/'src/Game/NatMapCheck.agda'
    target_check.parent.mkdir(parents=True)
    shutil.copy2(map_check,target_check)
    partial_source=ROOT/'src/Othello/PackedRowPartial6.agda'
    shutil.copy2(partial_source,check/'src/Othello/PackedRowPartial6.agda')
    cases = {c['part']: c for c in sample['cases']}
    labels = list(BUNDLES)
    bases = [200*BUNDLES[label][0] for label in labels]
    assert bases == sorted(bases) and all(b+1000 <= c for b,c in zip(bases,bases[1:]))
    refs = sorted({key for label in labels for part in BUNDLES[label]
                   for key in cases[part]['references']
                   if not any(base <= key < base+1000 for base in bases)})
    zones = []
    for i in range(4):
        low = 0 if i == 0 else bases[i-1]+1000
        high = bases[i] if i < 3 else sample['wire_rows']
        keys = [key for key in refs if low <= key < high]
        text = tree(keys, lambda key: _packed_leaf(sample,key),
                    lambda pivot,l,r: 'B'+word(pivot)+l+r) if keys else 'A'
        zones.append((keys,text))
    assert sum(len(keys) for keys,_ in zones) == len(refs)
    body = '''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.RowPacked6 as Packed
import Othello.PackedVectors6 as Vectors
import Othello.PackedMapText6 as Text
'''
    for label in labels:
        body += f'import Tests.BigRowsScaling6.{label}.States as {label}\n'
        body += f'own{label} : B.Vec Packed.PackedState 1000\nown{label} = Vectors.pack {label}.ss\n'
    for i,(_,text) in enumerate(zones):
        body += f'zone{i} : M.Map Packed.PackedState\nzone{i} = Text.table '+json.dumps(text,ensure_ascii=False)+'\n'
    # Each cut separates complete numeric domains, including gaps.
    expr = 'zone3'
    for i in reversed(range(3)):
        label = labels[i];base = bases[i]
        expr = f'(M.branch {base} zone{i} (M.branch {base+1000} (M.rows {base} 1000 own{label}) {expr}))'
    body += 'table : M.Map Packed.PackedState\ntable = '+expr+'\n'
    body += '''fallback : Packed.PackedState
fallback = Packed.initialPacked
G : ℕ → Packed.PackedState
G = Laws.totalize table fallback
'''
    (folder/'Data.agda').write_text(HEADER+'-- AI-assisted untrusted common-map data.\nmodule '+PREFIX+'.Data where\n\n'+body)
    proof = '''open import Prelude
open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapRoute as R
import Game.NatMapCheck as MapCheck
import Game.EncodedStepAssembly as Assembly
import Othello.InlineEntries6 as Rules
import Othello.RowPacked6 as Packed
import Othello.PackedVectors6 as Vectors
import Othello.SharedInlineSteps6 as Shared
import Othello.UnicodeCompact6 as Codec
import Othello.PackedRowPartial6 as Link
import Tests.PackedCommonRows6.Data as Data

module A = Assembly.Assembly Packed.decode Rules.specializedGame6 white (lowerGoal 4)
module Checks = MapCheck.Checking Packed.equal Packed.equal-sound
'''
    for i,label in enumerate(labels):
        base = bases[i]
        proof += f'import Tests.BigRowsScaling6.{label}.States as {label}\n'
        proof += f'import Tests.BigRowsScaling6.{label}.TextBodies as Body{label}\n'
        route = 'R.right refl (R.left refl R.here)'
        for _ in range(i):
            route = 'R.right refl (R.right refl ('+route+'))'
        proof += f'''
route{label} : R.Route Data.table {base} 1000 Data.own{label}
route{label} = {route}
abstract
  citations{label} : Shared.Compatible (M.lookup {label}.demand) Data.G
  citations{label} = Checks.compatible-sound {label}.demand Data.G refl
  partial{label} : A.Partial Data.G (M.rows {base} 1000 Data.own{label})
  partial{label} = Link.partial {base} {label}.ss (Codec.bodies 1000 Body{label}.text)
    (M.lookup {label}.demand) refl Data.G citations{label}
    (R.compatible Data.G route{label} (Laws.self-compatible Data.table Data.fallback))
'''
    # Only the3000 owned rows are covered; referenced rows are not claimed.
    owned = f'(M.branch {bases[1]} (M.rows {bases[0]} 1000 Data.own{labels[0]}) (M.branch {bases[2]} (M.rows {bases[1]} 1000 Data.own{labels[1]}) (M.rows {bases[2]} 1000 Data.own{labels[2]})))'
    proof += 'owned : M.Map Packed.PackedState\nowned = '+owned+'\n'
    proof += f'''
abstract
  partial : A.Partial Data.G owned
  partial = A.join {{G = Data.G}} {bases[1]} partial{labels[0]}
    (A.join {{G = Data.G}} {bases[2]} partial{labels[1]} partial{labels[2]})
-- No complete/global-proven call: unowned citations and initial bounds remain open.
'''
    (folder/'Closed.agda').write_text(HEADER+'-- AI-assisted checked partial assembly, with open unowned citations.\nmodule '+PREFIX+'.Closed where\n\n'+proof)
    shutil.copy2(ROOT/'othello.agda-lib',check/'othello.agda-lib')
    atomic_json(out/'emission.json',dict(created_utc=utc(),source=source_identity(check),
        copied_core_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [generic,map_check,partial_source]},
        owned_rows=3000,own_bases=bases,distinct_reference_keys_outside_owned=len(refs),
        reference_zone_sizes=[len(keys) for keys,_ in zones],
        sample_sha256=request['sample_sha256'],additional_wire_scans=0,
        same_common_map_for_all_three=True,initial_bounds_proved=False,
        mathematical_objective_complete=False))


if __name__ == '__main__':
    import sys
    emit(Path(sys.argv[1]))
