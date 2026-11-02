#!/usr/bin/env python3
"""UNTRUSTED, unmeasured specialization of direct sample linkage modules.

No Agda invocation occurs here. Original checker facts, IDs and maps are reused;
every generated module still requires safe checking on its original machine.
"""
import hashlib
from pathlib import Path
import re
import tempfile

from initial_global_alignment6 import _prefix
from initial_global_direct6 import _verify, emit as emit_direct
from initial_global_named6 import COMMON
from lazy_sample_parts6 import emit as emit_samples
from nat_indexed_pilot6 import HEADER
from wire_workflow6 import require


PARAMS = '''module AlignedModel (LookupStates : ℕ → State six)
  (LookupBodies : ℕ → I.IndexedCertificate ℕ)
  (sameStates : Laws.Compatible globalStates LookupStates)
  (sameBodies : Laws.Compatible globalBodies LookupBodies) where
'''
CLOSED = '''-- Closed sample coverage only; unowned state rows have no proof here.
abstract
  partial : Family.A.Partial G C ownedStates
  partial = AlignedModel.partial G C
    (Laws.self-compatible globalStates fallbackState)
    (Laws.self-compatible globalBodies I.indexedLeaf)
'''


def specialize(raw, *, prefix, target):
    """Instantiate exactly the known direct template, keeping its proof terms."""
    source = raw.decode()
    require(source.count(PARAMS) == 1, 'unexpected direct parameter block')
    before, body = source.split(PARAMS)
    if target == 'Root':
        require(body.endswith(CLOSED), 'unexpected direct closed-root template')
        body = body[:-len(CLOSED)]
        body, count = re.subn(
            r'\((Part\d+)\.AlignedModel\.partial LookupStates LookupBodies sameStates sameBodies\)',
            r'\1.partial', body)
        require(count > 0, 'root has no direct part applications')
    else:
        before += f'import {prefix}.Lookup as Lookup\n'
    lines = body.splitlines(keepends=True)
    require(all(not line.strip() or line.startswith('  ') for line in lines),
            'unexpected declaration outside parameter block')
    body = ''.join(line[2:] if line.strip() else line for line in lines)
    substitutions = dict(LookupStates='G', LookupBodies='C',
                         sameStates='Lookup.stateCompatible',
                         sameBodies='Lookup.bodyCompatible')
    body = re.sub(r'\b(?:LookupStates|LookupBodies|sameStates|sameBodies)\b',
                  lambda match: substitutions[match[0]], body)
    result = before + body
    if target == 'Root':
        result += '-- Closed sample partial coverage; this is not an initial-board theorem.\n'
    require('module AlignedModel' not in result, 'parameterized coverage module remains')
    require(result.count('partial : Family.A.Partial') == 1,
            'exactly one closed partial export required')
    require('accepted = refl' not in result and 'postulate' not in result,
            'unexpected new proof claim')
    return result.encode()


def emit(check, *, side, sample, sample_prefix, named_layout,
         prefix='Tests.InitialGlobalClosed6'):
    _prefix(prefix)
    _prefix(sample_prefix)
    require(isinstance(named_layout, dict), 'named layout required')
    named_prefix = named_layout.get('prefix')
    _prefix(named_prefix)
    for donor in (sample_prefix, named_prefix):
        require(prefix != donor and not prefix.startswith(donor + '.')
                and not donor.startswith(prefix + '.'), 'distinct source namespaces required')
    check = Path(check).absolute()
    folder = check / 'src' / Path(*prefix.split('.'))
    require(not folder.exists() and not any(p.is_symlink() for p in (folder, *folder.parents)),
            'fresh nonsymlink source root required')
    require(not any((check / '_build').glob('*/agda/src/' + prefix.replace('.', '/'))),
            'existing generated interfaces refused')
    # Reproduce and validate every donor before writing any candidate file.
    with tempfile.TemporaryDirectory(prefix='closed6-source-') as tmp:
        temporary = Path(tmp)
        samples = emit_samples(temporary, sample, side=side, prefix=sample_prefix)
        _verify(check, samples)
        _verify(check, named_layout)
        for relative in named_layout['generated_sha256']:
            p = temporary / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((check / relative).read_bytes())
        direct = emit_direct(temporary, side=side, sample=sample,
                             sample_prefix=sample_prefix, named_layout=named_layout,
                             prefix=prefix)
        sources = {relative: specialize((temporary / relative).read_bytes(),
                                       prefix=prefix, target=Path(relative).stem)
                   for relative in direct['generated_sha256']}
    lookup = (HEADER + '-- UNTRUSTED closed lookup specialization; no new game facts.\n'
              + f'module {prefix}.Lookup where\n\n' + COMMON
              + f'open import {named_prefix}.Model\n'
              + '''stateCompatible : Laws.Compatible globalStates G
stateCompatible = Laws.self-compatible globalStates fallbackState
bodyCompatible : Laws.Compatible globalBodies C
bodyCompatible = Laws.self-compatible globalBodies I.indexedLeaf
''')
    sources['src/' + prefix.replace('.', '/') + '/Lookup.agda'] = lookup.encode()
    require(all(not (check / relative).exists() for relative in sources),
            'refusing source overwrite')
    for relative, raw in sources.items():
        p = check / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(raw)
    result = dict(direct)
    result.update(format='othello-initial-global-closed6-v1',
                  targets=['Lookup', *direct['targets']], closed_lookup_specialization=True,
                  generated_sha256={n: hashlib.sha256(raw).hexdigest()
                                    for n, raw in sources.items()},
                  generated_bytes=sum(map(len, sources.values())),
                  agda_acceptance_measured=False, resource_benefit_measured=False,
                  scope='unmeasured closed sample linkage candidate; no initial-board theorem')
    return result
