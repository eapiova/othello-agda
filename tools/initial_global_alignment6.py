#!/usr/bin/env python3
"""Fresh bounded global lookup alignments and CLOSED sample partial coverage.

Untrusted source generator only. Imported checker facts must have already been
accepted by safe Agda; these stages never complete the global map or prove an
initial bound. Numeric routes cross independently balanced demand trees.
"""
import hashlib
from pathlib import Path
import re
import tempfile

from lazy_sample_parts6 import emit as emit_samples
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require


def _prefix(value):
    require(isinstance(value, str) and len(value) <= 180 and
            re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){1,10}', value),
            'safe bounded module prefix required')


def _tree(ids):
    if len(ids) == 1:
        return ids[0]
    mid = len(ids) // 2
    return ids[mid] * 200, _tree(ids[:mid]), _tree(ids[mid:])


def emit(check, *, side, sample, sample_prefix, prefix='Tests.InitialGlobalAlignment6'):
    _prefix(prefix)
    _prefix(sample_prefix)
    require(side in ('lower', 'upper'), 'lower or upper required')
    require(prefix != sample_prefix and not prefix.startswith(sample_prefix + '.')
            and not sample_prefix.startswith(prefix + '.'), 'distinct source namespaces required')
    check = Path(check).absolute()
    folder = check / 'src' / Path(*prefix.split('.'))
    require(not folder.exists() and not any(p.is_symlink() for p in (folder, *folder.parents)),
            'fresh nonsymlink source root required')
    require(not any((check / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    # The existing sample generator is the source-of-truth validator and byte
    # template. Exact equality pins state literals, body vectors, demands and
    # family direction. No accepted source/interface is modified or rechecked.
    with tempfile.TemporaryDirectory(prefix='alignment6-source-') as tmp:
        metadata = emit_samples(Path(tmp), sample, side=side, prefix=sample_prefix)
        for relative, expected in metadata['generated_sha256'].items():
            source = check / relative
            require(not any(p.is_symlink() for p in (source, *source.parents)),
                    'symlinked accepted source refused')
            require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == expected,
                    'accepted sample source metadata mismatch: ' + relative)
    cases = sorted(sample['cases'], key=lambda c: c['part'])
    require(4 <= len(cases) <= 16, 'four to sixteen selected parts required')
    chunks = sample['states']
    sizes = {j: chunk['rows'] for j, chunk in chunks.items()}
    sources, stages, targets = {}, [], []
    common = '''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.Indexed as I
import Othello.LazyIndexed6 as Lazy
open import Othello.Board using (State; six)
'''

    def map_term(tree, kind):
        if isinstance(tree, int):
            j, n = tree, sizes[tree]
            vector = f'(Lazy.states {n} S{j}.text)' if kind == 'states' else f'Body{j}.bodies'
            return f'(M.rows {200*j} {n} {vector})'
        pivot, left, right = tree
        return f'(M.branch {pivot} {map_term(left, kind)} {map_term(right, kind)})'

    def route(tree, j):
        if isinstance(tree, int):
            require(tree == j, 'route leaf mismatch')
            return 'Laws.here'
        pivot, left, right = tree
        if 200 * j < pivot:
            return f'(Laws.left (Laws.at-most {200*j+sizes[j]} {pivot} refl) {route(left, j)})'
        return f'(Laws.right (Laws.at-most {pivot} {200*j} refl) {route(right, j)})'

    for count in (4, 8, 16):
        if count > len(cases):
            continue
        selected = cases[:count]
        owned = [case['part'] for case in selected]
        needed = sorted(set().union(*(set(case['dependencies']) for case in selected)))
        require(len(needed) <= 8192, 'demanded chunk cap reached')
        global_tree, own_tree = _tree(needed), _tree(owned)
        body = common + f'import {sample_prefix}.Family as Family\n'
        body += ''.join(f'import {sample_prefix}.StateData{j} as S{j}\n' for j in needed)
        body += ''.join(f'import {sample_prefix}.BodyData{j} as Body{j}\n'
                        f'import {sample_prefix}.Part{j} as P{j}\n' for j in owned)
        terminal = 'wQQQQQQQQQQQQ' if side == 'lower' else 'bDDDDDDDDDDDD'
        body += f'''open import Othello.Board using (initial)
open import Othello.CompactShared6 using (decodeCompactState)
fallbackState : State six
fallbackState = fromMaybe (initial six) (decodeCompactState "{terminal}")
globalStates : M.Map (State six)
globalStates = {map_term(global_tree, 'states')}
globalBodies : M.Map (I.IndexedCertificate ℕ)
globalBodies = {map_term(own_tree, 'bodies')}
ownedStates : M.Map (State six)
ownedStates = {map_term(own_tree, 'states')}
G : ℕ → State six
G = Laws.totalize globalStates fallbackState
C : ℕ → I.IndexedCertificate ℕ
C = Laws.totalize globalBodies I.indexedLeaf
'''
        for j in needed:
            n = sizes[j]
            body += f'''stateRoute{j} : Laws.Route globalStates {200*j} {n} (Lazy.states {n} S{j}.text)
stateRoute{j} = {route(global_tree, j)}
'''
        for j in owned:
            n = sizes[j]
            body += f'''bodyRoute{j} : Laws.Route globalBodies {200*j} {n} Body{j}.bodies
bodyRoute{j} = {route(own_tree, j)}
'''

        # Keep lookup functions neutral while checking pointwise alignments.
        # Unfolding a concrete totalized lookup at base+finToNat(i) can make
        # the evaluator expand enormous numeric offsets before i is known.
        symbolic = ''
        for j in needed:
            n = sizes[j]
            symbolic += f'''stateAligned{j} : Laws.Aligned (M.rows {200*j} {n} (Lazy.states {n} S{j}.text)) LookupStates
stateAligned{j} = Laws.route-aligned {{map = globalStates}} {{base = {200*j}}} {{n = {n}}}
  {{xs = Lazy.states {n} S{j}.text}} LookupStates stateRoute{j} sameStates
'''
        for j in owned:
            n = sizes[j]
            symbolic += f'''bodyAligned{j} : Laws.Aligned P{j}.bodies LookupBodies
bodyAligned{j} = Laws.route-aligned {{map = globalBodies}} {{base = {200*j}}} {{n = {n}}}
  {{xs = Body{j}.bodies}} LookupBodies bodyRoute{j} sameBodies
'''

        def aligned(tree, kind):
            if isinstance(tree, int):
                return f'{kind}Aligned{tree}'
            return f'({aligned(tree[1], kind)} , {aligned(tree[2], kind)})'

        for case in selected:
            j = case['part']
            symbolic += f'''demandAligned{j} : Laws.Aligned P{j}.demand LookupStates
demandAligned{j} = {aligned(_tree(sorted(set(case['dependencies']))), 'state')}
'''
        symbolic += f'''globalStatesAligned : Laws.Aligned globalStates LookupStates
globalStatesAligned = {aligned(global_tree, 'state')}
ownedStatesAligned : Laws.Aligned ownedStates LookupStates
ownedStatesAligned = {aligned(own_tree, 'state')}
globalBodiesAligned : Laws.Aligned globalBodies LookupBodies
globalBodiesAligned = {aligned(own_tree, 'body')}
'''

        def partial(tree):
            if isinstance(tree, int):
                j = tree
                return f'(P{j}.linked LookupStates LookupBodies demandAligned{j} stateAligned{j} bodyAligned{j})'
            return f'(Family.A.join {{G = LookupStates}} {{C = LookupBodies}} {tree[0]} {partial(tree[1])} {partial(tree[2])})'

        symbolic += f'''-- Sample coverage; cited unowned state rows have no proof here.
abstract
  partial : Family.A.Partial LookupStates LookupBodies ownedStates
  partial = {partial(own_tree)}
'''
        body += '''module AlignedModel (LookupStates : ℕ → State six)
  (LookupBodies : ℕ → I.IndexedCertificate ℕ)
  (sameStates : Laws.Compatible globalStates LookupStates)
  (sameBodies : Laws.Compatible globalBodies LookupBodies) where
'''
        body += ''.join('  ' + line + '\n' for line in symbolic.splitlines())
        body += '''module Closed = AlignedModel G C
  (Laws.self-compatible globalStates fallbackState)
  (Laws.self-compatible globalBodies I.indexedLeaf)
-- Both lookup compatibilities are discharged; this is still partial coverage.
abstract
  partial : Family.A.Partial G C ownedStates
  partial = Closed.partial
'''
        name = 'Stage' + str(count)
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        sources[relative] = (HEADER + '-- AI-assisted untrusted global sample alignment.\n'
                             + f'module {prefix}.{name} where\n\n' + body).encode()
        targets.append(name)
        stages.append(dict(target=name, parts=count, owned_parts=owned, needed_chunks=len(needed),
                           needed_parts=needed, owned_rows=sum(sizes[j] for j in owned)))
    for relative in sources:
        require(not (check / relative).exists(), 'refusing source overwrite')
    for relative, raw in sources.items():
        path = check / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    return dict(format='othello-initial-global-alignment6-v1', side=side, prefix=prefix,
                sample_prefix=sample_prefix, targets=targets, stages=stages,
                generated_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in sources.items()},
                generated_bytes=sum(map(len, sources.values())), initial_problem2_proved=False,
                optimal_initial_pair_proved=False, production_authorized=False,
                scope='actual global lookup alignment and closed sample partial coverage only; no initial theorem')
