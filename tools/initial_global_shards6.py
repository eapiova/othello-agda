#!/usr/bin/env python3
"""UNTRUSTED bounded module shards for CLOSED global sample partial coverage.

These sources require safe Agda checking. They preserve exact global IDs and
sample vectors; they neither complete coverage nor establish an initial bound.
"""
import hashlib
from pathlib import Path
import tempfile

from initial_global_alignment6 import _prefix, _tree
from lazy_sample_parts6 import emit as emit_samples
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require


COMMON = '''open import Prelude
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.Indexed as I
import Othello.LazyIndexed6 as Lazy
open import Othello.Board using (State; six)
'''


def emit(check, *, side, sample, sample_prefix, prefix='Tests.InitialGlobalShards6', route_batch=32):
    _prefix(prefix)
    _prefix(sample_prefix)
    require(side in ('lower', 'upper'), 'lower or upper required')
    require(type(route_batch) is int and 1 <= route_batch <= 64,
            'route batch must be an integer from one to sixty-four')
    require(prefix != sample_prefix and not prefix.startswith(sample_prefix + '.')
            and not sample_prefix.startswith(prefix + '.'), 'distinct source namespaces required')
    check = Path(check).absolute()
    folder = check / 'src' / Path(*prefix.split('.'))
    require(not folder.exists() and not any(p.is_symlink() for p in (folder, *folder.parents)),
            'fresh nonsymlink source root required')
    require(not any((check / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    # Reproduce every accepted sample source, including checker facts, before
    # creating any output. The existing generator also validates all bounds.
    with tempfile.TemporaryDirectory(prefix='shards6-source-') as tmp:
        metadata = emit_samples(Path(tmp), sample, side=side, prefix=sample_prefix)
        for relative, expected in metadata['generated_sha256'].items():
            source = check / relative
            require(not any(p.is_symlink() for p in (source, *source.parents)),
                    'symlinked accepted source refused')
            require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == expected,
                    'accepted sample source metadata mismatch: ' + relative)
    cases = sorted(sample['cases'], key=lambda c: c['part'])
    require(1 <= len(cases) <= 16, 'one to sixteen selected parts required')
    sizes = {j: c['rows'] for j, c in sample['states'].items()}
    owned = [c['part'] for c in cases]
    needed = sorted(set().union(*(set(c['dependencies']) for c in cases)))
    require(0 < len(needed) <= 8192, 'demanded chunk cap reached')
    global_tree, own_tree = _tree(needed), _tree(owned)
    sources, targets, shards = {}, [], []

    def add(name, body):
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        sources[relative] = (HEADER + '-- AI-assisted UNTRUSTED global sample shard.\n'
                             + f'module {prefix}.{name} where\n\n' + body).encode()
        targets.append(name)

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
        if 200*j < pivot:
            return f'(Laws.left (Laws.at-most {200*j+sizes[j]} {pivot} refl) {route(left, j)})'
        return f'(Laws.right (Laws.at-most {pivot} {200*j} refl) {route(right, j)})'

    terminal = 'wQQQQQQQQQQQQ' if side == 'lower' else 'bDDDDDDDDDDDD'
    model = COMMON + ''.join(f'import {sample_prefix}.StateData{j} as S{j}\n' for j in needed)
    model += ''.join(f'import {sample_prefix}.BodyData{j} as Body{j}\n' for j in owned)
    model += f'''open import Othello.Board using (initial)
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
    add('Model', model)
    owner = {}
    for start in range(0, len(needed), route_batch):
        ids = needed[start:start+route_batch]
        name = 'Routes' + str(start // route_batch)
        for j in ids:
            owner[j] = name
        body = COMMON + f'open import {prefix}.Model\n'
        body += ''.join(f'import {sample_prefix}.StateData{j} as S{j}\n' for j in ids)
        for j in ids:
            n = sizes[j]
            body += f'''stateRoute{j} : Laws.Route globalStates {200*j} {n} (Lazy.states {n} S{j}.text)
stateRoute{j} = {route(global_tree, j)}
'''
        body += '''module AlignedModel (LookupStates : ℕ → State six)
  (sameStates : Laws.Compatible globalStates LookupStates) where
'''
        for j in ids:
            n = sizes[j]
            body += f'''  stateAligned{j} : Laws.Aligned (M.rows {200*j} {n} (Lazy.states {n} S{j}.text)) LookupStates
  stateAligned{j} = Laws.route-aligned {{map = globalStates}} {{base = {200*j}}} {{n = {n}}}
    {{xs = Lazy.states {n} S{j}.text}} LookupStates stateRoute{j} sameStates
'''
        add(name, body)
        shards.append(dict(target=name, needed_parts=ids, needed_chunks=len(ids)))

    params = '''module AlignedModel (LookupStates : ℕ → State six)
  (LookupBodies : ℕ → I.IndexedCertificate ℕ)
  (sameStates : Laws.Compatible globalStates LookupStates)
  (sameBodies : Laws.Compatible globalBodies LookupBodies) where
'''
    for case in cases:
        j, n = case['part'], sizes[case['part']]
        ds = sorted(set(case['dependencies']))
        batches = sorted({owner[d] for d in ds}, key=lambda s: int(s[6:]))
        body = COMMON + f'''open import {prefix}.Model
import {sample_prefix}.Family as Family
import {sample_prefix}.Part{j} as P
import {sample_prefix}.BodyData{j} as Body
'''
        body += ''.join(f'import {prefix}.{b} as {b}\n' for b in batches)
        body += f'''bodyRoute : Laws.Route globalBodies {200*j} {n} Body.bodies
bodyRoute = {route(own_tree, j)}
''' + params
        body += ''.join(f'  module R{b[6:]} = {b}.AlignedModel LookupStates sameStates\n' for b in batches)

        def aligned(tree):
            if isinstance(tree, int):
                return f'R{owner[tree][6:]}.stateAligned{tree}'
            return f'({aligned(tree[1])} , {aligned(tree[2])})'

        body += f'''  demandAligned : Laws.Aligned P.demand LookupStates
  demandAligned = {aligned(_tree(ds))}
  bodyAligned : Laws.Aligned P.bodies LookupBodies
  bodyAligned = Laws.route-aligned {{map = globalBodies}} {{base = {200*j}}} {{n = {n}}}
    {{xs = Body.bodies}} LookupBodies bodyRoute sameBodies
  abstract
    partial : Family.A.Partial LookupStates LookupBodies P.states
    partial = P.linked LookupStates LookupBodies demandAligned {aligned(j)} bodyAligned
'''
        add('Part' + str(j), body)

    root = COMMON + f'open import {prefix}.Model\nimport {sample_prefix}.Family as Family\n'
    root += ''.join(f'import {prefix}.Part{j} as Part{j}\n' for j in owned)
    root += params
    root += ''.join(f'  module P{j} = Part{j}.AlignedModel LookupStates LookupBodies sameStates sameBodies\n'
                    for j in owned)

    def partial(tree):
        if isinstance(tree, int):
            return f'P{tree}.partial'
        return f'(Family.A.join {{G = LookupStates}} {{C = LookupBodies}} {tree[0]} {partial(tree[1])} {partial(tree[2])})'

    root += f'''  abstract
    partial : Family.A.Partial LookupStates LookupBodies ownedStates
    partial = {partial(own_tree)}
module Closed = AlignedModel G C
  (Laws.self-compatible globalStates fallbackState)
  (Laws.self-compatible globalBodies I.indexedLeaf)
-- Closed sample coverage only; unowned state rows have no proof here.
abstract
  partial : Family.A.Partial G C ownedStates
  partial = Closed.partial
'''
    add('Root', root)
    for relative in sources:
        require(not (check / relative).exists(), 'refusing source overwrite')
    for relative, raw in sources.items():
        path = check / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    return dict(format='othello-initial-global-shards6-v1', side=side, prefix=prefix,
                sample_prefix=sample_prefix, route_batch=route_batch, targets=targets,
                root_target='Root', owned_parts=owned, needed_parts=needed,
                owned_rows=sum(sizes[j] for j in owned), needed_chunks=len(needed), shards=shards,
                generated_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in sources.items()},
                generated_bytes=sum(map(len, sources.values())), initial_problem2_proved=False,
                optimal_initial_pair_proved=False, production_authorized=False,
                scope='actual global lookup alignment and closed sample partial coverage only; no initial theorem')
