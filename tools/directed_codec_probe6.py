"""Safe strict-codec equality and matched directed row checks, no new coverage."""
import hashlib
import json
from pathlib import Path
import bench6
import compact_shared6 as compact
import completion_batch6 as prior
from directed_probe6 import converted
from direct_rows_probe6 import HEADER
from provenance import source_identity
from run_job import atomic_json, utc


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    source=prior.ROOT/'src/Othello/DirectedCompact6.agda';raw=source.read_bytes()
    target=check/'src/Othello/DirectedCompact6.agda';target.parent.mkdir(parents=True);target.write_bytes(raw)
    case=next(c for c in json.loads((prior.OUT/'sample.json').read_text())['cases'] if c['part']==33154)
    states=[bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
    texts,counts=converted(case['body_text'],states,text_output=True);text=''.join(texts)
    common='''open import Prelude
import Othello.DirectedCompact6 as Codec
import Tests.DirectedProbe6.Data as Data
'''
    data=common+'''open import Agda.Builtin.String using (String)
text : String
text = "'''+text+'''"
abstract
  exact : Codec.decodeBodies 200 text ≡ just Data.newBodies
  exact = refl
'''
    previous=prior.ROOT/'results/direct-symmetry-probe6-20261018/check/src/Tests/DirectSymmetryProbe6/Variant.agda'
    baseline=previous.read_text().replace('module Tests.DirectSymmetryProbe6.Variant where','module Tests.DirectedCodecProbe6.Baseline where')
    variant=baseline.replace('Tests.DirectedCodecProbe6.Baseline','Tests.DirectedCodecProbe6.Variant')
    variant=variant.replace('import Tests.DirectedProbe6.Data as Data','import Tests.DirectedProbe6.Data as Data\nimport Tests.DirectedCodecProbe6.Data as Text\nimport Othello.DirectedCompact6 as Codec')
    variant=variant.replace('Data.newBodies','(Codec.bodies 200 Text.text)')
    folder=check/'src/Tests/DirectedCodecProbe6';folder.mkdir(parents=True)
    for name,body in [('Data',HEADER+'module Tests.DirectedCodecProbe6.Data where\n'+data),('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-directed-codec6-sources-v1',created_utc=utc(),copied_core_sha256={str(source):hashlib.sha256(raw).hexdigest()},existing_rows=200,new_distinct_rows=0,converted_characters=len(text),counts=counts,strict_full_decode_equality_required=True,mathematical_objective_complete=False))
    return source_identity(check)
