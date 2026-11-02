#!/usr/bin/env python3
"""UNTRUSTED direct field applications for CLOSED sample partial coverage.

Borrowed named maps and routes must still have their exact generated sources.
Safe Agda checking is required; this generator establishes no initial theorem.
"""
import hashlib
from pathlib import Path
import re
import tempfile

from initial_global_alignment6 import _prefix
from initial_global_named6 import emit as emit_named
from lazy_sample_parts6 import emit as emit_samples
from wire_workflow6 import require


def _verify(check, metadata):
    for relative, digest in metadata['generated_sha256'].items():
        source = check / relative
        require(not any(p.is_symlink() for p in (source, *source.parents)),
                'symlinked accepted source refused')
        require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == digest,
                'accepted source metadata mismatch: ' + relative)


def _direct(source, *, named_prefix, prefix, target):
    source = source.replace(f'module {named_prefix}.{target} where',
                            f'module {prefix}.{target} where')
    source = source.replace('-- AI-assisted UNTRUSTED global sample named map.',
                            '-- AI-assisted UNTRUSTED direct sample field applications.')
    if target != 'Root':
        aliases = re.findall(r'^  module (R\d+) = (Routes\d+)\.AlignedModel LookupStates sameStates\n', source, re.M)
        source = re.sub(r'^  module R\d+ = Routes\d+\.AlignedModel LookupStates sameStates\n', '', source, flags=re.M)
        for alias, routes in aliases:
            source = re.sub(r'\b' + alias + r'\.stateAligned(\d+)\b',
                            lambda m: f'({routes}.AlignedModel.stateAligned{m[1]} LookupStates sameStates)', source)
    else:
        source = re.sub(r'import ' + re.escape(named_prefix) + r'\.(Part\d+) as',
                        lambda m: f'import {prefix}.{m[1]} as', source)
        aliases = re.findall(r'^  module (P\d+) = (Part\d+)\.AlignedModel LookupStates LookupBodies sameStates sameBodies\n', source, re.M)
        source = re.sub(r'^  module P\d+ = Part\d+\.AlignedModel LookupStates LookupBodies sameStates sameBodies\n', '', source, flags=re.M)
        for alias, part in aliases:
            source = re.sub(r'\b' + alias + r'\.partial\b',
                            f'({part}.AlignedModel.partial LookupStates LookupBodies sameStates sameBodies)', source)
        source = source.replace('module Closed = AlignedModel G C\n  (Laws.self-compatible globalStates fallbackState)\n  (Laws.self-compatible globalBodies I.indexedLeaf)\n', '')
        source = source.replace('partial = Closed.partial',
                               'partial = AlignedModel.partial G C\n    (Laws.self-compatible globalStates fallbackState)\n    (Laws.self-compatible globalBodies I.indexedLeaf)')
    require(not re.search(r'^\s*module \w+ =', source, re.M), 'parameterized aliases remain')
    require(not re.search(r'import ' + re.escape(named_prefix) + r'\.(?:Part\d+|Root)\b', source),
            'named coverage module import refused')
    return source.encode()


def _private_imports(raw):
    lines = raw.decode().splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(('open import ', 'import '))]
    require(starts, 'generated imports missing')
    first, last = starts[0], starts[-1]
    require(all(not line.strip() or line.startswith(('open import ', 'import '))
                for line in lines[first:last + 1]), 'noncontiguous generated imports refused')
    return (''.join(lines[:first]) + 'private\n'
            + ''.join('  ' + line if line.strip() else line for line in lines[first:last + 1])
            + ''.join(lines[last + 1:])).encode()


def _module_imports(raw, *, named_prefix, prefix, target):
    """Filter existing imports; retain every proof term and parameter unchanged."""
    stem, kind = (prefix, 'Part') if target == 'Root' else (named_prefix, 'Routes')
    pattern = r'^import ' + re.escape(stem) + r'\.(' + kind + r'\d+) as (\1)\n'
    source, count = re.subn(pattern, lambda m: m[0].rstrip('\n')
                          + ' using (module AlignedModel)\n', raw.decode(), flags=re.M)
    require(count > 0, 'expected direct module imports missing')
    return source.encode()


def emit(check, *, side, sample, sample_prefix, named_layout, prefix='Tests.InitialGlobalDirect6',
         private_imports=False, module_imports_only=False):
    require(type(private_imports) is bool, 'Boolean private-import mode required')
    require(type(module_imports_only) is bool, 'Boolean module-import mode required')
    _prefix(prefix)
    _prefix(sample_prefix)
    require(isinstance(named_layout, dict) and named_layout.get('format') == 'othello-initial-global-named6-v1',
            'exact named layout required')
    named_prefix = named_layout.get('prefix')
    _prefix(named_prefix)
    for donor in (sample_prefix, named_prefix):
        require(prefix != donor and not prefix.startswith(donor + '.') and not donor.startswith(prefix + '.'),
                'distinct source namespaces required')
    check = Path(check).absolute()
    folder = check / 'src' / Path(*prefix.split('.'))
    require(not folder.exists() and not any(p.is_symlink() for p in (folder, *folder.parents)),
            'fresh nonsymlink source root required')
    require(not any((check / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    # Reproduce into isolation only: exact metadata equality validates ownership,
    # dependencies, shard partition, row sizes, batch settings and source hashes.
    with tempfile.TemporaryDirectory(prefix='direct6-source-') as tmp:
        temporary = Path(tmp)
        accepted = emit_samples(temporary, sample, side=side, prefix=sample_prefix)
        regenerated = emit_named(temporary, side=side, sample=sample, sample_prefix=sample_prefix,
                                 prefix=named_prefix, route_batch=named_layout.get('route_batch'),
                                 map_batch=named_layout.get('map_batch'))
        require(named_layout == regenerated, 'named layout metadata mismatch')
        _verify(check, accepted)
        _verify(check, regenerated)
        targets = ['Part' + str(j) for j in regenerated['owned_parts']] + ['Root']
        sources = {}
        for target in targets:
            donor = temporary / 'src' / Path(*named_prefix.split('.')) / (target + '.agda')
            relative = 'src/' + prefix.replace('.', '/') + '/' + target + '.agda'
            sources[relative] = _direct(donor.read_text(), named_prefix=named_prefix, prefix=prefix, target=target)
            if module_imports_only:
                sources[relative] = _module_imports(sources[relative], named_prefix=named_prefix,
                                                   prefix=prefix, target=target)
            if private_imports:
                sources[relative] = _private_imports(sources[relative])
    for relative in sources:
        require(not (check / relative).exists(), 'refusing source overwrite')
    for relative, raw in sources.items():
        path = check / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    return dict(format='othello-initial-global-direct6-v1', side=side, prefix=prefix,
                sample_prefix=sample_prefix, named_prefix=named_prefix, targets=targets,
                root_target='Root', owned_parts=regenerated['owned_parts'],
                private_imports=private_imports,
                module_imports_only=module_imports_only,
                needed_parts=regenerated['needed_parts'], needed_chunks=regenerated['needed_chunks'],
                owned_rows=regenerated['owned_rows'],
                generated_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in sources.items()},
                generated_bytes=sum(map(len, sources.values())), initial_problem2_proved=False,
                optimal_initial_pair_proved=False, production_authorized=False,
                scope='direct global lookup alignment and closed sample partial coverage only; no initial theorem')
