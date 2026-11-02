#!/usr/bin/env python3
"""Bounded uniform-lazy feasibility layouts; acceptance remains safe Agda's job.

Only a fresh module root is generated. Existing source and interfaces are never
rewritten. State modules need only export their compact String ``text``. No
initial theorem or production authorization is supplied by this generator.
"""
from pathlib import Path
import hashlib
import re

import nat_tree_assembly6 as tree
from compact_shared6 import TRIPLES
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require

LAZY_IMPORT = 'import Othello.LazyIndexed6 as Lazy\n'


def _prefix(value):
    require(isinstance(value, str) and len(value) <= 240, 'bounded module prefix required')
    parts = value.split('.')
    require(1 <= len(parts) <= 16 and all(
        re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', part) for part in parts),
        'unsafe module prefix')
    return Path(*parts)


def _destination(check, prefix):
    check = Path(check).resolve()
    relative = _prefix(prefix)
    folder = check / 'src' / relative
    # A symlink in any existing ancestor could redirect writes into old source.
    require(not any(p.is_symlink() for p in (folder, *folder.parents)
                    if p == check or check in p.parents), 'symlink source path refused')
    return check, folder


def _state_text(n, text):
    require(type(n) is int and 0 < n <= 200, 'bounded state row count required')
    require(isinstance(text, str) and len(text) == 13 * n, 'state text row count mismatch')
    require(all(text[i] in 'bw' and all(c in TRIPLES for c in text[i + 1:i + 13])
                for i in range(0, len(text), 13)), 'invalid compact state symbols')


def _metadata(sources):
    return dict(generated_sha256={name: hashlib.sha256(raw).hexdigest()
                                  for name, raw in sources.items()},
                generated_bytes=sum(map(len, sources.values())))


def emit_state_text(check, state_prefix, j, n, text):
    """Emit one new safe text-only state module, with 1..200 compact rows.

    ``j`` is a part index in 0..511. Syntax is validated here; the safe checker
    remains the authority for semantic state/certificate validity.
    """
    require(type(j) is int and 0 <= j < 512, 'bounded part index required')
    _state_text(n, text)
    check, folder = _destination(check, state_prefix)
    path = folder / f'StateData{j}.agda'
    require(not path.exists() and not path.is_symlink(), 'refusing state data overwrite')
    require(not path.with_suffix('.agdai').exists() and not any(
        (check / '_build').glob('*/agda/src/' + path.relative_to(check / 'src').with_suffix('.agdai').as_posix())),
        'preexisting state interface refused')
    content = (HEADER + '-- AI-assisted untrusted state text; safe Agda checks every row.\n'
               + f'module {state_prefix}.StateData{j} where\n\n'
               + 'open import Agda.Builtin.String using (String)\n\n'
               + f'text : String\ntext = "{text}"\n')
    folder.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(content)
    return dict(rows=n, part=j, **_metadata({path.relative_to(check).as_posix(): content.encode()}))


def generate(check, *, sizes, dependencies, body_texts, root_packed,
             state_prefix, prefix='Tests.NatTree6', cut_depth=4, side='lower',
             lazy_accessibility=False):
    """Use tree.generate's API and limits, with Lazy states and checking.

    Both state and body literals are untrusted data. The state prefix must
    expose StateData{j}.text for each part. This wrapper preserves assembly,
    body decoding, goal4, hierarchy routes and original-rule root transfer.
    It refuses an existing output module root, including symlinks and caches.
    The optional recursor changes only Root; existing row judgments and all
    other generated sources are identical. The default preserves old layouts.
    """
    require(type(lazy_accessibility) is bool, 'Boolean accessibility mode required')
    check, folder = _destination(check, prefix)
    state_path = _prefix(state_prefix)
    output_path = _prefix(prefix)
    require(not (state_path == output_path or state_path in output_path.parents
                 or output_path in state_path.parents), 'state and output roots must be separate')
    require(not folder.exists() and not folder.is_symlink(), 'fresh generated module root required')
    require(not any((check / '_build').glob('*/agda/src/' + output_path.as_posix())),
            'preexisting generated interface root refused')
    sizes = list(sizes)
    require(0 < len(sizes) <= 512 and all(type(n) is int and 0 < n <= 200 for n in sizes),
            'feasibility size cap reached')
    require(type(cut_depth) is int and 0 <= cut_depth <= 12 and side in ('lower', 'upper'),
            'bounded direction required')
    require(isinstance(dependencies, dict) and all(type(j) is int for j in dependencies),
            'integer dependency keys required')
    dependencies = {j: set(ds) for j, ds in dependencies.items()}
    require(all(type(d) is int for ds in dependencies.values() for d in ds),
            'integer dependency indices required')
    body_texts = list(body_texts)
    require(len(body_texts) == len(sizes) and all(isinstance(t, str) and
            re.fullmatch(r'[0-9A-Z_;]+', t) for t in body_texts), 'unsafe body literal')
    _state_text(1, root_packed)
    result = tree.generate(check, sizes=sizes, dependencies=dependencies,
                           body_texts=body_texts, root_packed=root_packed,
                           state_prefix=state_prefix, prefix=prefix,
                           cut_depth=cut_depth, side=side)
    updated = {}
    for relative, original_digest in result['generated_sha256'].items():
        path = check / relative
        require(path.parent == folder, 'unexpected generated path')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == original_digest, 'generated source changed')
        original = raw.decode('utf-8')
        text = original
        if path.stem == 'Family':
            require(text.count('module A = Assembly.Assembly ') == 1, 'family shape changed')
            player, goal, laws = (('white', 'lowerGoal', 'lowerTransport6') if side == 'lower'
                                  else ('black', 'upperGoal', 'upperTransport6'))
            text += (LAZY_IMPORT + f'module L = Lazy.Checking Fast.fastGame6 {player} '
                     + f'({goal} 4) {laws}\n')
        if re.search(r'\bS[0-9]+\.states\b', text):
            def lazy_states(match):
                j = int(match[1])
                require(j < len(sizes), 'unexpected state vector reference')
                return f'(Lazy.states {sizes[j]} S{j}.text)'
            text = re.sub(r'\bS([0-9]+)\.states\b', lazy_states, text)
            text = text.replace('open import Prelude\n', 'open import Prelude\n' + LAZY_IMPORT, 1)
        if re.fullmatch(r'Part[0-9]+', path.stem):
            require(text.count('Family.A.Lower.checkPart') == 1 and
                    text.count('Family.A.linkedAligned') == 1, 'part shape changed')
            text = text.replace('Family.A.Lower.checkPart', 'Family.L.checkPart')
            text = text.replace('Family.A.linkedAligned', 'Family.L.linkedAligned')
        if path.stem == 'Root' and lazy_accessibility:
            text = with_lazy_accessibility(text, side=side)
        require(not re.search(r'\bS[0-9]+\.states\b', text), 'eager state reference remains')
        updated[relative] = text.encode('utf-8')
    # Only files returned by the fresh generator are eligible for rewriting.
    for relative, raw in updated.items():
        (check / relative).write_bytes(raw)
    result.update(_metadata(updated), uniform_lazy=True)
    if lazy_accessibility:
        result['lazy_accessibility'] = True
    return result


def with_lazy_accessibility(source, *, side):
    """Change only a fresh root's recursor, retaining the original row facts.

    The caller must write to a new source/module, never an accepted root. The
    exact-match guards refuse an unexpected template or an already changed one.
    Agda acceptance is still required; text rewriting supplies no proof fact.
    """
    require(side in ('lower', 'upper'), 'bounded direction required')
    old = '  provenAt = Family.A.Lower.V.global-proven G C rows\n'
    anchor = 'import Othello.Fast6 as Fast\n'
    require(source.count(old) == 1 and source.count(anchor) == 1
            and 'Game.NatIndexedRecursion' not in source, 'root recursor shape changed')
    player, goal, laws = (('white', 'lowerGoal', 'lowerTransport6') if side == 'lower'
                          else ('black', 'upperGoal', 'upperTransport6'))
    imports = ('import Game.NatIndexedRecursion as Rec\n'
               'open import Othello.Encode6 using (stateEquality6)\n'
               f'open import Othello.SharedSymmetry6 using ({laws})\n')
    new = (f'  provenAt = Rec.Checking.global-proven stateEquality6 Fast.fastGame6\n'
           f'    {player} ({goal} 4) {laws} G C rows\n')
    return source.replace(anchor, anchor + imports).replace(old, new)
