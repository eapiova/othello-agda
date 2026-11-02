#!/usr/bin/env python3
"""UNTRUSTED bounded named-map modules for CLOSED global sample partial coverage.

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


COMMON = '''open import Prelude hiding (map)
import Game.Balanced as B
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.Indexed as I
import Othello.LazyIndexed6 as Lazy
open import Othello.Board using (State; six)
'''


def emit(check, *, side, sample, sample_prefix, prefix='Tests.InitialGlobalNamed6', route_batch=32, map_batch=32):
    _prefix(prefix)
    _prefix(sample_prefix)
    require(side in ('lower', 'upper'), 'lower or upper required')
    require(type(route_batch) is int and 1 <= route_batch <= 64,
            'route batch must be an integer from one to sixty-four')
    require(type(map_batch) is int and 1 <= map_batch <= 64,
            'map batch must be an integer from one to sixty-four')
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
    with tempfile.TemporaryDirectory(prefix='named6-source-') as tmp:
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
        sources[relative] = (HEADER + '-- AI-assisted UNTRUSTED global sample named map.\n'
                             + f'module {prefix}.{name} where\n\n' + body).encode()
        targets.append(name)

    refs = {}
    map_helpers = []

    def leaves(tree):
        if isinstance(tree, int):
            return [tree]
        return leaves(tree[1]) + leaves(tree[2])

    def factor(tree, kind, stem):
        """Cut only at existing tree nodes, preserving every original pivot."""
        ids = leaves(tree)
        if len(ids) > map_batch:
            left = factor(tree[1], kind, stem)
            right = factor(tree[2], kind, stem)
            name = stem + str(len(map_helpers))
            body = COMMON + f'import {prefix}.{left[0]} as L\nimport {prefix}.{right[0]} as R\n'
            body += f'map : M.Map {map_type(kind)}\nmap = M.branch {tree[0]} L.map R.map\n'
            refs[kind, tree] = (name, 'map')
        else:
            name = stem + str(len(map_helpers))
            body = COMMON
            if kind == 'bodies':
                body += ''.join(f'import {sample_prefix}.BodyData{j} as Body{j}\n' for j in ids)
            else:
                body += ''.join(f'import {sample_prefix}.StateData{j} as S{j}\n' for j in ids)
            definitions = []

            def local(node):
                if isinstance(node, int):
                    j, n = node, sizes[node]
                    vector = f'(Lazy.states {n} S{j}.text)' if kind != 'bodies' else f'Body{j}.bodies'
                    term = f'M.rows {200*j} {n} {vector}'
                else:
                    l, r = local(node[1]), local(node[2])
                    term = f'M.branch {node[0]} {l} {r}'
                field = 'map' if node == tree else 'node' + str(len(definitions))
                definitions.append(f'{field} : M.Map {map_type(kind)}\n{field} = {term}\n')
                refs[kind, node] = (name, field)
                return field

            local(tree)
            body += ''.join(definitions)
        add(name, body)
        map_helpers.append(dict(target=name, kind=kind, parts=ids, leaf_chunks=len(ids),
                                group=len(ids) <= map_batch))
        return name, 'map'

    def map_type(kind):
        return '(I.IndexedCertificate ℕ)' if kind == 'bodies' else '(State six)'

    state_root = factor(global_tree, 'states', 'StateMap')
    body_root = factor(own_tree, 'bodies', 'BodyMap')
    owned_root = factor(own_tree, 'owned', 'OwnedMap')

    def ref(kind, tree):
        name, field = refs[kind, tree]
        return name + '.' + field

    def route(tree, j, kind, vector, imports):
        imports.add(refs[kind, tree][0])
        n, base = sizes[j], 200*j
        args = f'{{base = {base}}} {{n = {n}}} {{xs = {vector}}}'
        if isinstance(tree, int):
            require(tree == j, 'route leaf mismatch')
            return f'(Laws.here {args})'
        pivot, left, right = tree
        imports.update((refs[kind, left][0], refs[kind, right][0]))
        args = f'{{pivot = {pivot}}} {{l = {ref(kind, left)}}} {{r = {ref(kind, right)}}} ' + args
        if base < pivot:
            path = route(left, j, kind, vector, imports)
            return f'(Laws.left {args} (Laws.at-most {base+n} {pivot} refl) {path})'
        path = route(right, j, kind, vector, imports)
        return f'(Laws.right {args} (Laws.at-most {pivot} {base} refl) {path})'

    def import_maps(names):
        return ''.join(f'import {prefix}.{name} as {name}\n' for name in sorted(names))

    terminal = 'wQQQQQQQQQQQQ' if side == 'lower' else 'bDDDDDDDDDDDD'
    model = COMMON + f'import {prefix}.{state_root[0]} as Global\n'
    model += f'import {prefix}.{body_root[0]} as Bodies\n'
    model += f'import {prefix}.{owned_root[0]} as Owned\n'
    model += f'''open import Othello.Board using (initial)
open import Othello.CompactShared6 using (decodeCompactState)
fallbackState : State six
fallbackState = fromMaybe (initial six) (decodeCompactState "{terminal}")
globalStates : M.Map (State six)
globalStates = Global.map
globalBodies : M.Map (I.IndexedCertificate ℕ)
globalBodies = Bodies.map
ownedStates : M.Map (State six)
ownedStates = Owned.map
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
        route_imports = set()
        route_definitions = ''
        for j in ids:
            n = sizes[j]
            expression = route(global_tree, j, 'states', f'Lazy.states {n} S{j}.text', route_imports)
            route_definitions += f'''stateRoute{j} : Laws.Route globalStates {200*j} {n} (Lazy.states {n} S{j}.text)
stateRoute{j} = {expression}
'''
        body += import_maps(route_imports) + route_definitions
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
        route_imports = set()
        expression = route(own_tree, j, 'bodies', 'Body.bodies', route_imports)
        body += import_maps(route_imports)
        body += f'''bodyRoute : Laws.Route globalBodies {200*j} {n} Body.bodies
bodyRoute = {expression}
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
    return dict(format='othello-initial-global-named6-v1', side=side, prefix=prefix,
                sample_prefix=sample_prefix, route_batch=route_batch, map_batch=map_batch,
                targets=targets, map_helpers=map_helpers,
                root_target='Root', owned_parts=owned, needed_parts=needed,
                owned_rows=sum(sizes[j] for j in owned), needed_chunks=len(needed), shards=shards,
                generated_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in sources.items()},
                generated_bytes=sum(map(len, sources.values())), initial_problem2_proved=False,
                optimal_initial_pair_proved=False, production_authorized=False,
                scope='actual global lookup alignment and closed sample partial coverage only; no initial theorem')
