#!/usr/bin/env python3
"""UNTRUSTED narrow route imports over existing checked alignment functions.

No Agda execution occurs here. This candidate preserves direct linkage terms,
introducing eta-free aliases so using-lists can select top-level route functions.
Its acceptance and resource benefit must both be measured separately.
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


def narrow_part(raw, *, prefix, named_prefix, owners, dependencies):
    source = raw.decode()
    references = re.findall(r'\b(Routes\d+)\.AlignedModel\.stateAligned(\d+)\b', source)
    require(references, 'missing direct route references')
    selected = {}
    for route, number in references:
        j = int(number)
        require(owners.get(j) == route, 'route ownership mismatch')
        selected.setdefault(route, set()).add(j)
    require({int(j) for _, j in references} == set(dependencies),
            'direct route references differ from exact dependencies')
    for route, ids in selected.items():
        original = f'import {named_prefix}.{route} as {route}\n'
        require(source.count(original) == 1, 'unexpected route import template')
        using = '; '.join('stateAligned' + str(j) for j in sorted(ids))
        source = source.replace(original,
            f'import {prefix}.{route} as {route} using ({using})\n')
    source, count = re.subn(r'\b(Routes\d+)\.AlignedModel\.(stateAligned\d+)\b',
                            r'\1.\2', source)
    require(count == len(references), 'route application rewrite differs')
    require(not re.search(r'import ' + re.escape(named_prefix) + r'\.Routes\d+\b', source),
            'broad named route import remains')
    return source.encode(), {k: sorted(v) for k, v in selected.items()}


def emit(check, *, side, sample, sample_prefix, named_layout,
         prefix='Tests.InitialGlobalNarrow6'):
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
    with tempfile.TemporaryDirectory(prefix='narrow6-source-') as tmp:
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
        owners = {j: shard['target'] for shard in named_layout['shards']
                  for j in shard['needed_parts']}
        cases = {case['part']: case for case in sample['cases']}
        sources, imports = {}, {}
        for relative in direct['generated_sha256']:
            raw = (temporary / relative).read_bytes()
            name = Path(relative).stem
            if name != 'Root':
                j = int(name.removeprefix('Part'))
                raw, imports[name] = narrow_part(raw, prefix=prefix,
                    named_prefix=named_prefix, owners=owners,
                    dependencies=cases[j]['dependencies'])
            sources[relative] = raw
    route_targets = []
    for shard in named_layout['shards']:
        name, ids = shard['target'], shard['needed_parts']
        body = (COMMON + f'open import {named_prefix}.Model using (globalStates)\n'
                + f'import {named_prefix}.{name} as Checked\n')
        body += ''.join(f'import {sample_prefix}.StateData{j} as S{j}\n' for j in ids)
        for j in ids:
            n = sample['states'][j]['rows']
            body += f'''stateAligned{j} : (LookupStates : ℕ → State six) →
  Laws.Compatible globalStates LookupStates →
  Laws.Aligned (M.rows {200*j} {n} (Lazy.states {n} S{j}.text)) LookupStates
stateAligned{j} = Checked.AlignedModel.stateAligned{j}
'''
        relative = 'src/' + prefix.replace('.', '/') + '/' + name + '.agda'
        sources[relative] = (HEADER + '-- UNTRUSTED aliases of existing checked routes.\n'
            + f'module {prefix}.{name} where\n\n' + body).encode()
        route_targets.append(name)
    require(all(not (check / p).exists() for p in sources), 'refusing source overwrite')
    for relative, raw in sources.items():
        p = check / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as stream:
            stream.write(raw)
    result = dict(direct)
    result.update(format='othello-initial-global-narrow6-v1',
        targets=[*route_targets, *direct['targets']], selected_imports=imports,
        generated_sha256={n: hashlib.sha256(b).hexdigest() for n, b in sources.items()},
        generated_bytes=sum(map(len, sources.values())),
        generator_certifies_acceptance=False, resource_benefit_measured=False,
        scope='unmeasured aliases and narrow imports for the same sample partial coverage; no initial theorem')
    return result
