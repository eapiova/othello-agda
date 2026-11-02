#!/usr/bin/env python3
"""Untrusted bounded conditional assembly of already accepted initial samples.

This emits only map joins and proof linkage. Agda acceptance, donor cache
provenance, global self-alignment and the initial root remain the caller's job.
"""
import hashlib
from pathlib import Path
import re

from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require


def _prefix(value):
    return (isinstance(value, str) and len(value) <= 180 and
            re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*){1,10}', value))


def emit(check, *, side, sample_prefix, parts, sizes,
         prefix='Tests.InitialSampleAssembly6'):
    """Emit cumulative stages of at most 4, 8 and 16 owned parts.

    ``parts`` is a strictly increasing list of 1..16 original numeric part IDs,
    each below 40000; ``sizes`` supplies their respective 1..200 row counts.
    Sizes are bounded descriptive metadata: imported maps remain authoritative.
    The caller supplies accepted, same-side sample modules exporting Family and
    Part<ID>. No original data or acceptance proof is emitted or evaluated here.
    """
    require(side in ('lower', 'upper'), 'one lower or upper side required')
    require(_prefix(prefix) and _prefix(sample_prefix), 'safe bounded module prefixes required')
    require(sample_prefix == 'Tests.InitialLazyTraining' + side.title(),
            'accepted same-side sample module prefix required')
    require(prefix != sample_prefix and not prefix.startswith(sample_prefix + '.')
            and not sample_prefix.startswith(prefix + '.'), 'output must not shadow sample modules')
    require(isinstance(parts, (list, tuple)) and 1 <= len(parts) <= 16,
            'one to sixteen owned parts required')
    require(all(type(j) is int and 0 <= j < 40000 for j in parts)
            and all(a < b for a, b in zip(parts, parts[1:])),
            'part IDs must be unique, sorted and below 40000')
    require(isinstance(sizes, (list, tuple)) and len(sizes) == len(parts)
            and all(type(n) is int and 1 <= n <= 200 for n in sizes),
            'one bounded row count per part required')
    raw_root = Path(check).absolute()
    require(not any(p.is_symlink() for p in (raw_root, *raw_root.parents)),
            'symlink source root refused')
    require(not any('cache' in p.lower() or p.lower() == '_build'
                    for p in raw_root.parts), 'cache path writes refused')
    root = raw_root.resolve()
    folder = root / 'src' / Path(*prefix.split('.'))
    require(not folder.exists() and not any(p.is_symlink() for p in (folder, *folder.parents)),
            'fresh non-symlink output prefix required')
    require(not any((root / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    sources = {}
    counts = sorted({min(limit, len(parts)) for limit in (4, 8, 16)})
    common = '''open import Prelude
import Game.Indexed as I
import Game.NatMap as M
import Game.NatMapLaws as Laws
open import Othello.Board using (State; six)
'''

    def tree(ids, field):
        if len(ids) == 1:
            return f'P{ids[0]}.{field}'
        middle = len(ids) // 2
        return f'(M.branch {200 * ids[middle]} {tree(ids[:middle], field)} {tree(ids[middle:], field)})'

    def demands(ids):
        if len(ids) == 1:
            return f'Laws.Aligned P{ids[0]}.demand G'
        middle = len(ids) // 2
        return f'({demands(ids[:middle])} × {demands(ids[middle:])})'

    def project(value, direction):
        return f'(proj{direction} {value})'

    def linked(ids, demand, states, bodies):
        if len(ids) == 1:
            return f'(P{ids[0]}.linked G C {demand} {states} {bodies})'
        middle = len(ids) // 2
        left = linked(ids[:middle], project(demand, '₁'), project(states, '₁'), project(bodies, '₁'))
        right = linked(ids[middle:], project(demand, '₂'), project(states, '₂'), project(bodies, '₂'))
        return f'(Family.A.join {{G = G}} {{C = C}} {200 * ids[middle]} {left} {right})'

    targets = []
    stages = []
    for count in counts:
        ids = parts[:count]
        name = f'Stage{count}'
        module = prefix + '.' + name
        body = common + f'import {sample_prefix}.Family as Family\n'
        body += ''.join(f'import {sample_prefix}.Part{j} as P{j}\n' for j in ids)
        body += f'''
-- Conditional assembly only: explicit per-part demands need not share tree shape.
states : M.Map (State six)
states = {tree(ids, 'states')}
bodies : M.Map (I.IndexedCertificate ℕ)
bodies = {tree(ids, 'bodies')}
Demands : (ℕ → State six) → Set
Demands G = {demands(ids)}
abstract
  linked : (G : ℕ → State six) → (C : ℕ → I.IndexedCertificate ℕ) →
    Demands G → Laws.Aligned states G → Laws.Aligned bodies C →
    Family.A.Partial G C states
  linked G C demand sameStates sameBodies =
    {linked(ids, 'demand', 'sameStates', 'sameBodies')}
'''
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        sources[relative] = (HEADER + '-- AI-assisted untrusted conditional assembly; safe Agda must check linkage.\n'
                             + f'module {module} where\n\n' + body).encode()
        targets.append(name)
        stages.append(dict(target=name, module=module, parts=list(ids), rows=sum(sizes[:count])))
    for relative in sources:
        require(not (root / relative).exists(), 'refusing existing assembly source')
    for relative, raw in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    return dict(format='othello-initial-sample-assembly6-v1', side=side, prefix=prefix,
                sample_prefix=sample_prefix, targets=targets, stages=stages,
                parts=list(parts), sizes=list(sizes), rows=sum(sizes),
                generated_bytes=sum(map(len, sources.values())),
                generated_sha256={name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()},
                assumptions=['accepted same-side imported part modules and matching donor provenance',
                             'per-part demand alignment to G', 'combined states alignment to G',
                             'combined bodies alignment to C'],
                scope='conditional real initial sample import and proof linkage only',
                global_self_alignment_measured=False, initial_root_measured=False,
                complete_initial_bound_measured=False, agda_checked=False,
                initial_problem2_proved=False, optimal_initial_pair_proved=False,
                production_authorized=False)
