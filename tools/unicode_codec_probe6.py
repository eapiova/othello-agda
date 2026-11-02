"""AI-assisted fixed-width conversion; safe equality and game checks required."""
import hashlib,json
from pathlib import Path
import bench6
import compact_shared6 as compact
import completion_batch6 as prior
from directed_probe6 import converted
from direct_rows_probe6 import HEADER
from provenance import source_identity
from run_job import atomic_json,utc


def encode(text):
    alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    at=0
    def small(n):
        assert 0<=n<=128
        return chr(256+n)
    def key(n):
        assert 0<=n<20000000
        return chr(16384+n//1024)+chr(16384+n%1024)
    def number(base):
        nonlocal at
        end=text.index(';',at);raw=text[at:end];assert raw
        at=end+1;n=0
        for c in raw:
            d=alphabet.index(c);assert d<base;n=base*n+d
        return n
    def one():
        nonlocal at
        tag=text[at];at+=1
        if tag=='L':return 'A'
        if tag=='K':return 'B'+key(number(37))
        if tag=='R':
            sym=alphabet.index(text[at]);at+=1
            return 'C'+small(sym)+key(number(37))
        if tag=='S':return 'D'+small(number(10))
        if tag=='P':return 'E'+one()
        if tag in ('C','Q'):
            arg=alphabet.index(text[at]);at+=1
            return ('F' if tag=='C' else 'G')+small(arg)+one()
        assert tag=='F'
        n=alphabet.index(text[at]);at+=1
        return 'H'+small(n)+''.join(one() for _ in range(n))
    output=one();assert at==len(text)
    return output


def emit(check):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    source=prior.ROOT/'src/Othello/UnicodeCompact6.agda';raw=source.read_bytes()
    target=check/'src/Othello/UnicodeCompact6.agda';target.parent.mkdir(parents=True);target.write_bytes(raw)
    case=next(c for c in json.loads((prior.OUT/'sample.json').read_text())['cases'] if c['part']==33154)
    states=[bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
    texts,counts=converted(case['body_text'],states,text_output=True)
    before=''.join(texts);after=''.join(encode(text) for text in texts)
    data='''open import Prelude
open import Agda.Builtin.String using (String)
import Othello.UnicodeCompact6 as Codec
import Tests.DirectedProbe6.Data as Data
oldText : String
oldText = '''+json.dumps(before,ensure_ascii=False)+'''
text : String
text = '''+json.dumps(after,ensure_ascii=False)+'''
abstract
  exact : Codec.decodeBodies 200 text ≡ just Data.newBodies
  exact = refl
'''
    old=prior.ROOT/'results/length-rays-probe6-20261018/check/src/Tests/LengthProbe6/Variant.agda'
    baseline=old.read_text().replace('module Tests.LengthProbe6.Variant where','module Tests.UnicodeCodecProbe6.Baseline where')
    baseline=baseline.replace('import Tests.DirectedProbe6.Data as Data','import Tests.DirectedProbe6.Data as Data\nimport Tests.UnicodeCodecProbe6.Data as Text\nimport Othello.DirectedCompact6 as Codec')
    baseline=baseline.replace('Data.newBodies','(Codec.bodies 200 Text.oldText)')
    variant=baseline.replace('Tests.UnicodeCodecProbe6.Baseline','Tests.UnicodeCodecProbe6.Variant').replace('import Othello.DirectedCompact6 as Codec','import Othello.UnicodeCompact6 as Codec').replace('Text.oldText','Text.text')
    folder=check/'src/Tests/UnicodeCodecProbe6';folder.mkdir(parents=True)
    for name,body in [('Data',HEADER+'module Tests.UnicodeCodecProbe6.Data where\n'+data),('Baseline',baseline),('Variant',variant)]:
        (folder/(name+'.agda')).write_text(body)
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'formal-source-provenance.json',dict(format='othello-unicode-codec6-sources-v1',created_utc=utc(),copied_core_sha256={str(source):hashlib.sha256(raw).hexdigest()},existing_rows=200,new_distinct_rows=0,old_characters=len(before),new_characters=len(after),old_utf8_bytes=len(before.encode()),new_utf8_bytes=len(after.encode()),counts=counts,strict_full_decode_equality_required=True,native_solver_executed=False,mathematical_objective_complete=False))
    return source_identity(check)
