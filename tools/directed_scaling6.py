"""AI-assisted prospective cold source/check comparison with held-out parts."""
import hashlib
import json
from pathlib import Path
import re

import bench6
import compact_shared6 as compact
import completion_batch6 as prior
from directed_probe6 import converted
from direct_rows_probe6 import HEADER,vec
from provenance import source_identity
from run_job import atomic_json,utc
from sparse_citation_pilot6 import tree

TRAIN=[342,10441,17236,26707]
HOLD=[4913,15761,23417,33154]
PREFIX='Tests.DirectedScaling6'
LOWER_TOKENS=88689949
UPPER_TOKENS=87739734  # historical untrusted census; no upper wire is claimed.


def emit(check,recovery=False):
    check=Path(check);assert not check.exists();check.mkdir(parents=True)
    source=prior.ROOT/'src/Othello/DirectedParts6.agda';raw=source.read_bytes()
    if not recovery:
        target=check/'src/Othello/DirectedParts6.agda';target.parent.mkdir(parents=True);target.write_bytes(raw)
    sample=json.loads((prior.OUT/'sample.json').read_text());features={}
    first=prior.ROOT/'results/directed-scaling6-20261018'
    namespace='Tests.DirectedScalingFixed6' if recovery else PREFIX
    if recovery:
        features=json.loads((first/'comparison-plan.json').read_text())['features']
        (check.parent/'forecast-freeze.json').write_bytes((first/'forecast-freeze.json').read_bytes())
    common='''open import Prelude
open import Agda.Builtin.Nat using (_+_)
open import Othello.Board using (State; Coord; six)
import Othello.Finite as F
import Game.Balanced as B
import Game.DirectedIndexed as D
import Game.NatMap as M
import Othello.LazyIndexed6 as Lazy
import Othello.DirectedCompact6 as Codec
'''
    settings='''open import Game.Core using (white)
open import Othello.Statements using (lowerGoal)
open import Othello.DirectSymmetry6 using (lowerTransport6)
import Othello.DirectedParts6 as Parts
module Check = Parts.Checking white (lowerGoal 4) lowerTransport6
'''
    def add(module,body):
        path=check/'src'/(module.replace('.','/')+'.agda');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(HEADER+'-- AI-assisted existing-row resource comparison.\nmodule '+module+' where\n\n'+body)
    for case in sample['cases']:
        part=case['part'];assert part in TRAIN+HOLD
        if recovery and part in TRAIN:continue
        prefix=namespace+'.Part'+str(part)
        states=[bench6.decode(compact.unpack_state(case['state_text'][13*i:13*i+13])) for i in range(200)]
        literals,counts=converted(case['body_text'],states)
        texts,text_counts=converted(case['body_text'],states,text_output=True)
        assert counts==text_counts and case['tokens']==sum(v for k,v in counts.items() if k!='directed_choices')
        keys=sorted(set(case['references']))
        def singleton(k):
            chunk=sample['states'][str(k//200)]
            packed=chunk['text'][13*(k%200):13*(k%200+1)]
            assert len(packed)==13
            return f'(M.rows {k} 1 (Lazy.states 1 "{packed}"))'
        expression=tree(keys,singleton,lambda pivot,l,r:f'(M.branch {pivot} {l} {r})')
        data=common+'''open import Agda.Builtin.String using (String)
text : String
text = "'''+case['state_text']+'''"
ss : B.Vec (State six) 200
ss = Lazy.states 200 text
embed : B.Fin 200 → ℕ
embed i = B.finToNat i + '''+str(200*part)+'''
demand : M.Map (State six)
demand = '''+expression+'\n'
        add(prefix+'.States',data)
        add(prefix+'.LiteralBodies',common+'''bodies : B.Vec (D.DirectedCertificate ℕ (Coord six)) 200
bodies = '''+vec(literals,'B.cons','B.nil')+'\n')
        add(prefix+'.TextBodies','open import Agda.Builtin.String using (String)\ntext : String\ntext = "'+''.join(texts)+'"\n')
        shared=common+settings+f'import {prefix}.States as Data\n'
        add(prefix+'.Literal',shared+f'''import {prefix}.LiteralBodies as Body
abstract
  linked : (G : ℕ → State six) → Check.R.V.Compatible (M.lookup Data.demand) G → ∀ i →
    Check.R.V.TreeOK G (Data.embed i) (B.lookupVec Data.ss i) (B.lookupVec Body.bodies i)
  linked = Check.literalLinked (M.lookup Data.demand) Data.embed Data.text Body.bodies refl
''')
        add(prefix+'.Compact',shared+f'''import {prefix}.TextBodies as Body
abstract
  linked : (G : ℕ → State six) → Check.R.V.Compatible (M.lookup Data.demand) G → ∀ i →
    Check.R.V.TreeOK G (Data.embed i) (B.lookupVec Data.ss i) (B.lookupVec (Codec.bodies 200 Body.text) i)
  linked = Check.linked (M.lookup Data.demand) Data.embed Data.text Body.text refl
''')
        features[str(part)]=dict(rows=200,tokens=case['tokens'],distinct_references=len(keys),counts=counts,
            compact_characters=sum(map(len,texts)),literal_source_bytes=sum(map(len,literals)))
    for name,parts in [('Training',TRAIN),('Holdout',HOLD)]:
        if recovery and name=='Training':continue
        add(namespace+'.'+name,''.join(f'import {namespace}.Part{part}.{style}\n' for part in parts for style in ['Literal','Compact']))
    (check/'othello.agda-lib').write_bytes((prior.ROOT/'othello.agda-lib').read_bytes())
    atomic_json(check.parent/'comparison-plan.json',dict(format='othello-directed-scaling6-plan-v1',
        created_utc=utc(),train=TRAIN,holdout=HOLD,features=features,module_prefix=namespace,
        new_distinct_rows=0,common_map_join=False,reused_training=recovery,source_sha256=hashlib.sha256(raw).hexdigest(),
        frozen_forecast_sha256=hashlib.sha256((check.parent/'forecast-freeze.json').read_bytes()).hexdigest() if recovery else None,
        model='Per style sum source-body and row module profiles / sum certificate tokens. Shared state/resolver source cost reported separately, not hidden in the forecast.',
        holdout_gate_relative_error=.30,lower_tokens=LOWER_TOKENS,upper_tokens_historical=UPPER_TOKENS,
        upper_count_is_untrusted_historical=True,full_workflow_forecast_validated=False,mathematical_objective_complete=False))
    return source_identity(check)


def profiles(path,namespace=PREFIX):
    found={}
    for line in Path(path).read_text().splitlines():
        m=re.match(r'^('+re.escape(namespace)+r'\.[^ ]+)\s+([\d,]+)ms',line)
        if m:found[m[1]]=int(m[2].replace(',',''))/1000
    return found


def summarize(out,phase):
    out=Path(out);plan=json.loads((out/'comparison-plan.json').read_text())
    namespace=plan.get('module_prefix',PREFIX)
    prof=profiles(out/'records'/(namespace.lower().replace('.','-')+'-'+phase+'.log'),namespace)
    parts=plan['train'] if phase=='training' else plan['holdout']
    tokens=sum(plan['features'][str(p)]['tokens'] for p in parts)
    import assembly6
    interfaces=assembly6.interfaces(out/'check')
    omitted=[]
    for p in parts:
        name=f'{namespace}.Part{p}.TextBodies'
        if name not in prof:
            assert any(path.endswith(name.replace('.','/')+'.agdai') for path in interfaces)
            omitted.append(name)
    costs={style:sum(prof.get(f'{namespace}.Part{p}.{body}',.001)+prof[f'{namespace}.Part{p}.{style}'] for p in parts)
        for style,body in [('Literal','LiteralBodies'),('Compact','TextBodies')]}
    shared=sum(prof[f'{namespace}.Part{p}.States'] for p in parts)
    result=dict(phase=phase,created_utc=utc(),tokens=tokens,costs_cpu_seconds=costs,
        omitted_sub_millisecond_text_modules=omitted,conservative_seconds_per_omitted_module=.001,
        shared_state_resolver_source_cpu_seconds=shared,module_profiles=prof)
    if phase=='training':
        result['slopes_seconds_per_token']={k:v/tokens for k,v in costs.items()}
        result['lower_source_body_and_row_prediction_seconds']={k:v/tokens*LOWER_TOKENS for k,v in costs.items()}
        result['both_directions_component_prediction_seconds']={k:v/tokens*(LOWER_TOKENS+UPPER_TOKENS) for k,v in costs.items()}
        result['frozen_before_holdout']=True
        atomic_json(out/'forecast-freeze.json',result)
    else:
        assert hashlib.sha256((out/'forecast-freeze.json').read_bytes()).hexdigest()==plan['frozen_forecast_sha256']
        frozen=json.loads((out/'forecast-freeze.json').read_text())
        result['predicted_cpu_seconds']={k:v*tokens for k,v in frozen['slopes_seconds_per_token'].items()}
        result['relative_errors']={k:abs(result['predicted_cpu_seconds'][k]-v)/v for k,v in costs.items()}
        result['heldout_component_gate_passed']={k:v<=.30 for k,v in result['relative_errors'].items()}
        result['whole_workflow_forecast_validated']=False
        atomic_json(out/'holdout-comparison.json',result)
    return result
