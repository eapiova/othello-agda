"""Emit a genuine multi-part Partial theorem over one common certificate map.

This is untrusted source generation, not checker acceptance. It specializes
already checked per-part symbolic bridge exports and joins their owned rows.
Cited but unowned full-map rows remain obligations for eventual production.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from full_state_map6 import _namespace
from initial_global_alignment6 import _tree
from new_row_bridge6 import HEADER
from wire_workflow6 import require


def _route(tree, part):
    if isinstance(tree, int):
        require(tree == part, 'selected body absent from route')
        return 'R.here'
    pivot, left, right = tree
    branch = 'left' if 200 * part < pivot else 'right'
    return '(R.' + branch + ' refl ' + _route(left if branch == 'left' else right, part) + ')'


def emit_join(check, full, units, *, prefix='Tests.CanonicalCombined6'):
    """Generate one safe module; caller must subsequently obtain Agda receipts.

    Each unit names exactly one row module and its symbolic full-map bridge.
    The kernel checks their types under the same G and C. There is no blanket
    conversion of separate closed Partial results with different body maps.
    """
    _namespace(prefix)
    _namespace(full['prefix'])
    require(full.get('complete') is True and type(full.get('rows')) is int
            and 0 < full['rows'] <= 8000000 and full.get('rows_per_part') == 200
            and type(full.get('parts')) is int and full['parts'] == (full['rows'] + 199) // 200,
            'complete bounded full state map required')
    require(isinstance(units, (list, tuple)) and 2 <= len(units) <= 16,
            'two to sixteen existing row/bridge units required')
    parts, names = set(), set()
    for u in units:
        j = u['part']
        require(type(j) is int and 0 < j < full['parts'] and j not in parts
                and type(u['rows']) is int and u['rows'] == min(200, full['rows'] - 200*j),
                'unique in-range parts and exact row counts required')
        parts.add(j)
        for key in ('row_prefix', 'bridge_prefix'):
            n = _namespace(u[key])
            require(n not in names and n != prefix and not n.startswith(prefix + '.')
                    and not prefix.startswith(n + '.'), 'distinct nonsubsuming module namespaces required')
            names.add(n)
    require(full['prefix'] not in names and full['prefix'] != prefix
            and not full['prefix'].startswith(prefix + '.')
            and not prefix.startswith(full['prefix'] + '.'), 'separate full-map namespace required')
    selected = sorted(units, key=lambda u: u['part'])
    check = Path(check).absolute()
    require(not check.exists() and 'results' in check.parts
            and not any(p.is_symlink() for p in (check, *check.parents)),
            'fresh private nonsymlink output required')
    tree = _tree(sorted(parts))
    def term(t, field):
        if isinstance(t, int):
            return f'P{t}.{field}'
        return f'(M.branch {t[0]} {term(t[1], field)} {term(t[2], field)})'
    def together(t):
        if isinstance(t, int):
            return 'Laws.rows-pair'
        return f'(Laws.fork-pair {together(t[1])} {together(t[2])})'
    def joined(t):
        if isinstance(t, int):
            return 'part' + str(t)
        return f'(Family.A.join {{G = LookupStates}} {{C = LookupBodies}} {t[0]} {joined(t[1])} {joined(t[2])})'
    body = '''open import Prelude
import Game.NatMap as M
import Game.NatMapLaws as Laws
import Game.NatMapRoute as R
import Game.Indexed as I
open import Othello.Board using (State; six; initial)
open import Othello.CompactShared6 using (decodeCompactState)
'''
    body += f'import {full["prefix"]}.Root as Full using (stateMap)\n'
    body += f'import {selected[0]["row_prefix"]}.Family as Family using (module A)\n'
    for u in selected:
        j = u['part']
        body += (f'import {u["row_prefix"]}.Part{j} as P{j} using (states; bodies)\n'
                 f'import {u["row_prefix"]}.BodyData{j} as Body{j} using (bodies)\n'
                 f'import {u["bridge_prefix"]}.Root as Bridge{j} using (symbolic)\n')
    body += f'''
-- Shared body map for these owned rows only; full state data stays canonical.
globalBodies : M.Map (I.IndexedCertificate ℕ)
globalBodies = {term(tree, 'bodies')}
ownedStates : M.Map (State six)
ownedStates = {term(tree, 'states')}
ownedTogether : Laws.Together ownedStates globalBodies
ownedTogether = {together(tree)}
'''
    for u in selected:
        j, n = u['part'], u['rows']
        body += f'''bodyRoute{j} : R.Route globalBodies {200*j} {n} Body{j}.bodies
bodyRoute{j} = {_route(tree, j)}
'''
    body += '''
-- Keep lookups neutral until all per-part symbolic proofs are composed.
module Model (LookupStates : ℕ → State six)
  (LookupBodies : ℕ → I.IndexedCertificate ℕ)
  (sameStates : Laws.Compatible Full.stateMap LookupStates)
  (sameBodies : Laws.Compatible globalBodies LookupBodies) where
'''
    for u in selected:
        j = u['part']
        body += f'''  part{j} : Family.A.Partial LookupStates LookupBodies P{j}.states
  part{j} = Bridge{j}.symbolic LookupStates LookupBodies sameStates
    (R.compatible LookupBodies bodyRoute{j} sameBodies)
'''
    body += f'''  abstract
    partial : Family.A.Partial LookupStates LookupBodies ownedStates
    partial = {joined(tree)}

fallback : State six
fallback = fromMaybe (initial six) (decodeCompactState "wQQQQQQQQQQQQ")
G : ℕ → State six
G = Laws.totalize Full.stateMap fallback
C : ℕ → I.IndexedCertificate ℕ
C = Laws.totalize globalBodies I.indexedLeaf
module Closed = Model G C
  (Laws.self-compatible Full.stateMap fallback)
  (Laws.self-compatible globalBodies I.indexedLeaf)
abstract
  partial : Family.A.Partial G C ownedStates
  partial = Closed.partial
-- Unowned full-map states still need row proofs; no complete initial theorem.
'''
    module = prefix + '.Root'
    relative = 'src/' + module.replace('.', '/') + '.agda'
    raw = (HEADER + '-- AI-assisted untrusted multi-part partial-coverage composition.\n'
           + 'module ' + module + ' where\n\n' + body).encode()
    require(len(raw) < 2**20 and b'accepted = refl' not in raw and b'postulate' not in raw,
            'bounded specialization-only source required')
    sources = {relative: raw, 'othello.agda-lib':
               (Path(__file__).resolve().parents[1]/'othello.agda-lib').read_bytes()}
    check.mkdir(parents=True)
    for name, data in sources.items():
        p = check / name;p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
    return dict(format='othello-canonical-joint-partial-layout6-v1', root_module=module,
        parts=sorted(parts), owned_rows=sum(u['rows'] for u in selected), units=selected,
        generated_sha256={n:hashlib.sha256(b).hexdigest() for n,b in sources.items()},
        generated_bytes=sum(map(len,sources.values())), source_modules=1,
        common_state_map=full['prefix']+'.Root.stateMap', common_body_map=True,
        symbolic_specialization=True, joint_target_is_import_only=False,
        partial_only=True, agda_checked=False, combined_partial_coverage_proved=False,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False)
