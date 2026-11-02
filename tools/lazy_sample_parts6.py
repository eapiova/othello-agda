#!/usr/bin/env python3
"""Emit independent safe checks for bounded samples of initial-layout parts.

Global numeric IDs stay unchanged. A check imports only the state text it
actually cites and exports a conditional linking theorem. It does not import
other parts, assemble the initial board, or supply a production permission.
"""
import hashlib
from pathlib import Path
import re

from compact_shared6 import TRIPLES
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require


def emit(check, sample, *, side, prefix='Tests.LazyInitialSample6', state_exports=None):
    require(side in ('lower', 'upper'), 'lower or upper required')
    require(isinstance(prefix, str) and len(prefix) <= 180 and
            re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){1,10}', prefix),
            'safe bounded module prefix required')
    check = Path(check).resolve()
    folder = check / 'src' / Path(*prefix.split('.'))
    require(not folder.exists() and not any(p.is_symlink() for p in (folder, *folder.parents)
            if p == check or check in p.parents), 'fresh private source root required')
    require(not any((check / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    cases = sample['cases']
    chunks = sample['states']
    require(isinstance(cases, list) and 0 < len(cases) <= 16 and isinstance(chunks, dict)
            and 0 < len(chunks) <= 8192, 'bounded cases and state chunks required')
    require(all(type(j) is int and 0 <= j < 40000 for j in chunks), 'state part index out of range')
    for j, chunk in chunks.items():
        n, text = chunk['rows'], chunk['text']
        require(type(n) is int and 0 < n <= 200 and isinstance(text, str) and len(text) == n * 13,
                'state chunk row count mismatch')
        require(all(text[i] in 'bw' and all(c in TRIPLES for c in text[i + 1:i + 13])
                    for i in range(0, len(text), 13)), 'bad compact state literal')
    needed = set()
    seen = set()
    for case in cases:
        j, n, body, refs = case['part'], case['rows'], case['body_text'], case['references']
        require(type(j) is int and j in chunks and j not in seen and n == chunks[j]['rows'],
                'duplicate or inconsistent selected part')
        seen.add(j)
        require(case['state_text'] == chunks[j]['text'], 'own state text differs')
        require(isinstance(body, str) and 0 < len(body) <= 2**20
                and re.fullmatch(r'[0-9A-Z_;]+', body), 'unsafe or oversized body literal')
        require(isinstance(refs, list) and len(refs) <= 32000
                and all(type(r) is int and 0 <= r < 200 * j + n for r in refs),
                'unbounded or forward citation')
        ds = {j} | {r // 200 for r in refs}
        require(ds <= chunks.keys() and all(r % 200 < chunks[r // 200]['rows'] for r in refs),
                'missing or out-of-bounds cited state')
        require(set(case['dependencies']) == ds, 'dependency list differs from references')
        needed.update(ds)
    require(needed == chunks.keys(), 'state chunks differ from actual demands')
    if state_exports is not None:
        require(isinstance(state_exports, dict) and set(state_exports) == set(chunks)
                and all(isinstance(module, str) and len(module) <= 240
                        and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){1,10}', module)
                        and not module.startswith(prefix + '.') for module in state_exports.values()),
                'exact external state module exports required')
    player, goal, laws = (('white', 'lowerGoal', 'lowerTransport6') if side == 'lower'
                          else ('black', 'upperGoal', 'upperTransport6'))
    sources = {}

    def add(name, body):
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        sources[relative] = (HEADER + '-- AI-assisted untrusted sample; safe Agda checks every assertion.\n'
            + f'module {prefix}.{name} where\n\n' + body).encode()

    common = '''open import Prelude
open import Agda.Builtin.String using (String)
open import Agda.Builtin.Nat using (_+_)
import Game.Balanced as B
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Othello.LazyIndexed6 as Lazy
import Othello.NatIndexed6 as D
open import Othello.Board using (State; six)
'''
    add('Family', common + f'''open import Game.Core using (white; black)
open import Othello.Statements using (lowerGoal; upperGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
import Othello.Fast6 as Fast
module L = Lazy.Checking Fast.fastGame6 {player} ({goal} 4) {laws}
module A = L.A
''')
    if state_exports is None:
        for j in sorted(chunks):
            add('StateData' + str(j), 'open import Agda.Builtin.String using (String)\n\n'
                + f'text : String\ntext = "{chunks[j]["text"]}"\n')
    state_modules = state_exports if state_exports is not None else {
        j: prefix + '.StateData' + str(j) for j in chunks}

    def demand(ds):
        if len(ds) == 1:
            j = ds[0]
            return f'(M.rows {200*j} {chunks[j]["rows"]} (Lazy.states {chunks[j]["rows"]} S{j}.text))'
        middle = len(ds) // 2
        return f'(M.branch {200*ds[middle]} {demand(ds[:middle])} {demand(ds[middle:])})'

    targets = ['Family']
    metadata = []
    for case in cases:
        j, n = case['part'], case['rows']
        ds = sorted(set(case['dependencies']))
        add('BodyData' + str(j), common + f'''text : String
text = "{case['body_text']}"
bodies : B.Vec (I.IndexedCertificate ℕ) {n}
bodies = D.bodies {n} text
''')
        add('Part' + str(j), common
            + ''.join(f'import {state_modules[d]} as S{d}\n' for d in ds)
            + f'''import {prefix}.Family as Family
import {prefix}.BodyData{j} as Body
demand : M.Map (State six)
demand = {demand(ds)}
states : M.Map (State six)
states = M.rows {200*j} {n} (Lazy.states {n} S{j}.text)
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = M.rows {200*j} {n} Body.bodies
embed : B.Fin {n} → ℕ
embed i = {200*j} + B.finToNat i
abstract
  accepted : Family.L.checkPart (M.lookup demand) embed S{j}.text Body.text ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned demand G → Laws.Aligned states G → Laws.Aligned bodies C →
    Family.A.Partial G C states
  linked = Family.L.linkedAligned {{n = {n}}} {200*j} demand S{j}.text Body.text accepted
''')
        targets.append('Part' + str(j))
        metadata.append(dict(part=j, rows=n, dependencies=len(ds), references=len(case['references']),
            body_bytes=len(case['body_text']), tokens=case['tokens']))
    for relative in sources:
        require(not (check / relative).exists(), 'refusing existing sample source')
    for relative, raw in sources.items():
        path = check / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    return dict(format='othello-lazy-sample-parts6-v1', side=side, prefix=prefix, cases=metadata,
        state_chunks=len(chunks), targets=targets, generated_bytes=sum(map(len, sources.values())),
        emitted_state_chunks=len(chunks) if state_exports is None else 0,
        reused_state_modules=0 if state_exports is None else len(state_exports),
        generated_sha256={name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()},
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='independent part checker facts and conditional links; no global or initial theorem')
