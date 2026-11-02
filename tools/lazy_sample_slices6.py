#!/usr/bin/env python3
"""Emit UNTRUSTED <=50-row safe checks with original native global ranks.

emit(check, path, *, side, prefix, rows_per_slice) validates the complete native
JSONL first, then rereads its bounded raw row records. Slice bodies are converted
row by row, never recovered by parsing concatenated encoded bodies. No native
proof premise, completion call, reindexing, or initial-board guarantee is emitted.
"""
import hashlib
import json
from pathlib import Path
import re

import native_layout_samples6 as native
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require

MAX_BYTES = 16 * 1024**2
COMMON = '''open import Prelude
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


def _read(path):
    require(0 < path.stat().st_size <= MAX_BYTES, 'sample file byte cap')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(0 < len(raw) <= MAX_BYTES, 'sample file byte cap')
    return raw


def _fresh(check, prefix):
    # Inspect lexical ancestors before resolving, so a symlink cannot disappear.
    check = Path(check).absolute()
    folder = check / 'src' / Path(*prefix.split('.'))
    require(not any(p.is_symlink() for p in (folder, *folder.parents)),
            'symlink source ancestry refused')
    require(not folder.exists(), 'fresh private source namespace required')
    require(not (check / '_build').is_symlink(), 'symlink cache root refused')
    require(not any((check / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    return check, folder


def emit(check, path, *, side, prefix='Tests.InitialSlices6', rows_per_slice=50):
    require(side in ('lower', 'upper'), 'lower or upper required')
    require(type(rows_per_slice) is int and 1 <= rows_per_slice <= 50,
            'slice row bound must be 1..50')
    require(isinstance(prefix, str) and len(prefix) <= 180 and
            re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){1,10}', prefix),
            'safe bounded module prefix required')
    check, folder = _fresh(check, prefix)
    path = Path(path)
    before = _read(path)
    try:
        sample = native.decode_samples(path)
    except (TypeError, KeyError, UnicodeError, AttributeError, IndexError) as error:
        raise ValueError('malformed native sample') from error
    raw = _read(path)
    require(raw == before, 'sample changed during validation')
    cases, chunks = sample['cases'], sample['states']
    require(0 < len(cases) <= 16 and 0 < len(chunks) <= 8192,
            'bounded selected parts and needed chunks required')
    rows = {case['part']: [] for case in cases}
    for line in raw.splitlines():
        item = json.loads(line)
        if item['kind'] == 'row':
            require(item['part'] in rows, 'raw selected part mismatch')
            rows[item['part']].append(item)
    for case in cases:
        part = rows[case['part']]
        converted = [native.convert_body(row['body'], row['references']) for row in part]
        require(len(part) == case['rows'] and
                [row['row'] for row in part] == list(range(case['rows'])) and
                ''.join(row['state'] for row in part) == case['state_text'] and
                ''.join(body for body, _ in converted) == case['body_text'] and
                sum(tokens for _, tokens in converted) == case['tokens'] and
                [ref for row in part for ref in row['references']] == case['references'],
                'raw rows differ from validated case')

    player, goal, laws = (('white', 'lowerGoal', 'lowerTransport6') if side == 'lower'
                          else ('black', 'upperGoal', 'upperTransport6'))
    sources = {}

    def add(name, body):
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        sources[relative] = (HEADER + '-- AI-assisted UNTRUSTED sample; safe Agda checks assertions.\n'
            + f'module {prefix}.{name} where\n\n' + body).encode('utf-8')

    add('Family', COMMON + f'''open import Game.Core using (white; black)
open import Othello.Statements using (lowerGoal; upperGoal)
open import Othello.SharedSymmetry6 using (lowerTransport6; upperTransport6)
import Othello.Fast6 as Fast
module L = Lazy.Checking Fast.fastGame6 {player} ({goal} 4) {laws}
module A = L.A
''')
    for j, chunk in sorted(chunks.items()):
        add('StateData' + str(j), 'open import Agda.Builtin.String using (String)\n\n'
            + f'text : String\ntext = "{chunk["text"]}"\n')

    def demand(ds):
        if len(ds) == 1:
            j = ds[0]
            return f'(M.rows {200*j} {chunks[j]["rows"]} (Lazy.states {chunks[j]["rows"]} S{j}.text))'
        middle = len(ds) // 2
        return f'(M.branch {200*ds[middle]} {demand(ds[:middle])} {demand(ds[middle:])})'

    targets = ['Family']
    metadata = []
    for case in cases:
        j = case['part']
        for start in range(0, case['rows'], rows_per_slice):
            own = rows[j][start:start + rows_per_slice]
            n, base = len(own), 200*j + start
            own_text = ''.join(row['state'] for row in own)
            converted = [native.convert_body(row['body'], row['references']) for row in own]
            body = ''.join(text for text, _ in converted)
            refs = [ref for row in own for ref in row['references']]
            ds = sorted({j} | {ref // 200 for ref in refs})
            require(own_text == chunks[j]['text'][13*start:13*(start+n)] and len(own_text) == 13*n,
                    'slice state range differs')
            require(all(ref < base + row['row'] - start for row in own for ref in row['references']),
                    'slice citation rank differs')
            suffix = f'{j}X{start}'
            name = 'Slice' + suffix
            add('BodyData' + suffix, COMMON + f'''text : String
text = "{body}"
bodies : B.Vec (I.IndexedCertificate ℕ) {n}
bodies = D.bodies {n} text
''')
            add(name, COMMON
                + ''.join(f'import {prefix}.StateData{d} as S{d}\n' for d in ds)
                + f'''import {prefix}.Family as Family
import {prefix}.BodyData{suffix} as Body
ownSliceText : String
ownSliceText = "{own_text}"
demand : M.Map (State six)
demand = {demand(ds)}
states : M.Map (State six)
states = M.rows {base} {n} (Lazy.states {n} ownSliceText)
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = M.rows {base} {n} Body.bodies
embed : B.Fin {n} → ℕ
embed i = {base} + B.finToNat i
abstract
  accepted : Family.L.checkPart (M.lookup demand) embed ownSliceText Body.text ≡ true
  accepted = refl
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Laws.Aligned demand G → Laws.Aligned states G → Laws.Aligned bodies C →
    Family.A.Partial G C states
  linked = Family.L.linkedAligned {{n = {n}}} {base} demand ownSliceText Body.text accepted
''')
            targets.append(name)
            metadata.append(dict(target=name, part=j, start_offset=start, slice_base=base,
                rows=n, tokens=sum(tokens for _, tokens in converted), dependencies=ds,
                references=refs, body_bytes=len(body)))
    # Recheck immediately before exclusive creation; no existing sources are replaced.
    _fresh(check, prefix)
    for relative in sources:
        destination = check / relative
        require(not destination.exists() and not destination.is_symlink(), 'existing sample source refused')
    for relative, content in sources.items():
        destination = check / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(content)
    return dict(format='othello-lazy-sample-slices6-v1', side=side, prefix=prefix,
        rows_per_slice=rows_per_slice, slices=metadata, targets=targets, state_chunks=len(chunks),
        input_sha256=hashlib.sha256(raw).hexdigest(), input_bytes=len(raw),
        generated_bytes=sum(map(len, sources.values())),
        generated_sha256={name: hashlib.sha256(content).hexdigest() for name, content in sources.items()},
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False,
        scope='UNTRUSTED independent slice checker assertions and conditional links; no initial theorem')
