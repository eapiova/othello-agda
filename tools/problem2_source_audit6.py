"""Audit the exact selected non-builtin sources of the private Problem2 package.

This is a source/provenance audit, not a replacement for the final Agda check.
No job, reservation, checker or mutation of a source archive is performed here.
"""
from __future__ import annotations

from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import re
import zipfile

from compression import zstd

FLAGS = {'--safe', '--without-K', '--cubical-compatible'}
UNSAFE = {'--allow-unsolved-metas', '--allow-incomplete-matches',
          '--no-termination-check', '--no-positivity-check', '--type-in-type',
          '--omega-in-omega', '--sized-types', '--irrelevant-projections',
          '--experimental-irrelevance', '--rewriting'}
ESCAPES = {'TERMINATING', 'NON_TERMINATING', 'NO_TERMINATION_CHECK',
           'NO_POSITIVITY_CHECK', 'NON_COVERING'}
IMPORT = re.compile(r'^\s*(?:open\s+)?import\s+([A-Za-z0-9_.]+)', re.M)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require(value, reason):
    if not value:
        raise ValueError(reason)


def code_and_pragmas(text: str) -> tuple[str, list[str]]:
    """Exclude nested comments and literal contents while retaining real pragmas."""
    fragments, pragmas = [], []
    index = 0
    begin = 0
    while index < len(text):
        if text.startswith('--', index):
            fragments.append(text[begin:index]); end = text.find('\n', index+2)
            index = len(text) if end < 0 else end
            fragments.append('\n'); begin = index
        elif text.startswith('{-#', index):
            fragments.append(text[begin:index]); end = text.find('#-}', index+3)
            require(end >= 0, 'unterminated Agda pragma')
            pragmas.append(text[index+3:end].strip())
            index = end+3; fragments.append(' '); begin = index
        elif text.startswith('{-', index):
            fragments.append(text[begin:index]); depth = 1; index += 2
            while depth:
                opening = text.find('{-', index); closing = text.find('-}', index)
                require(closing >= 0, 'unterminated nested Agda comment')
                if opening >= 0 and opening < closing:
                    depth += 1; index = opening+2
                else:
                    depth -= 1; index = closing+2
            fragments.append(' '); begin = index
        elif text[index] == '"':
            fragments.append(text[begin:index]); index += 1
            while True:
                end = text.find('"', index)
                require(end >= 0, 'unterminated Agda String literal')
                backslashes = 0; previous = end-1
                while previous >= index and text[previous] == '\\':
                    backslashes += 1; previous -= 1
                index = end+1
                if backslashes % 2 == 0:
                    break
            fragments.append(' "literal" '); begin = index
        elif text[index] == "'" and (index == 0 or
                not (text[index-1].isalnum() or text[index-1] in "_'") ):
            # A prime on an identifier is not the opening of a Char literal.
            end = text.find("'", index+1, min(len(text), index+16))
            content = text[index+1:end] if end >= 0 else ''
            if end >= 0 and (len(content) == 1 or content.startswith('\\')):
                fragments.append(text[begin:index]); fragments.append(' charLiteral ')
                index = end+1; begin = index
            else:
                index += 1
        else:
            index += 1
    fragments.append(text[begin:])
    return ''.join(fragments), pragmas


def audit(manifest_path: Path, p1_root: Path, p1_files: dict[str, str]) -> dict:
    """Verify selected-source hashes, graph closure and zero forbidden constructs.

    Call only inside an accounted bounded job after acquiring the source/donor
    locks required by that job. The returned report never claims Agda success.
    """
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    require(manifest['package_source_integrity_verified'] is True,
            'selected-source package was not integrity verified')
    core_path = Path(manifest['core_archive']); graph_path = Path(manifest['source_graph'])
    require(sha(core_path) == manifest['core_archive_sha256'], 'core source archive changed')
    require(sha(graph_path) == manifest['source_graph_sha256'], 'source graph changed')
    graph_raw = zstd.decompress(graph_path.read_bytes())
    require(hashlib.sha256(graph_raw).hexdigest() == manifest['source_graph_decoded_sha256'],
            'decoded source graph changed')
    graph = json.loads(graph_raw); selected = graph['selected_modules']
    require(len(selected) == manifest['selected_module_count'] == 4128,
            'selected source cardinality differs')
    builtins = set(manifest['builtin_modules_from_pinned_Agda'])
    require(all(module.startswith('Agda.') for module in builtins), 'unrecognized external module')
    require(len(p1_files) == 23 and all(sha(Path(p1_root)/name) == pin
            for name, pin in p1_files.items()), 'tagged P1 differs')
    inventories, byte_count, provider_counts = {}, 0, {}
    with ExitStack() as stack:
        archives = {'core': stack.enter_context(zipfile.ZipFile(core_path))}
        archive_paths = {'core': core_path}
        for provider, package in manifest['large_archive_references'].items():
            path = Path(package['archive'])
            require(sha(path) == package['archive_sha256'], provider+' archive changed')
            archives[provider] = stack.enter_context(zipfile.ZipFile(path))
            archive_paths[provider] = path
        for provider, archive in archives.items():
            names = archive.namelist()
            require(len(names) == len(set(names)), provider+' archive has duplicate entries')
        for module, entry in sorted(selected.items()):
            provider = entry['provider']; raw = archives[provider].read(entry['entry'])
            require(len(raw) == entry['size'] and hashlib.sha256(raw).hexdigest() == entry['sha256'],
                    module+' source differs from the selected dependency graph')
            byte_count += len(raw); provider_counts[provider] = provider_counts.get(provider, 0)+1
            code, pragmas = code_and_pragmas(raw.decode('utf-8'))
            options = {flag for pragma in pragmas if pragma.startswith('OPTIONS ')
                       for flag in pragma.split()[1:]}
            require(FLAGS <= options, module+' omits required safe flags')
            require(not (UNSAFE & options), module+' declares an unsafe option')
            require(not any(pragma.split()[0] in ESCAPES for pragma in pragmas if pragma.split()),
                    module+' declares a proof escape')
            require(re.search(r'\bpostulate\b', code) is None, module+' contains a postulate')
            require('{!' not in code and '!}' not in code
                    and re.search(r'(?<![\w\'])\?(?![\w\'])', code) is None,
                    module+' contains an explicit proof hole')
            imports = IMPORT.findall(code)
            require(imports == graph['dependency_edges'][module], module+' import graph differs')
            require(all(dependency in selected or dependency in builtins for dependency in imports),
                    module+' has an unrecorded external dependency')
            inventories[module] = entry['sha256']
        # Detect movement while reading, rather than trusting only the initial pin.
        for provider, path in archive_paths.items():
            pin = manifest['core_archive_sha256'] if provider == 'core' else \
                manifest['large_archive_references'][provider]['archive_sha256']
            require(sha(path) == pin, provider+' changed during source audit')
    require(sha(core_path) == manifest['core_archive_sha256'] and
            sha(graph_path) == manifest['source_graph_sha256'], 'package changed during audit')
    require(all(sha(Path(p1_root)/name) == pin for name, pin in p1_files.items()),
            'tagged P1 changed during source audit')
    return dict(format='othello-selected-problem2-source-audit-v1',
        source_audit_passed=True, manifest=str(manifest_path), manifest_sha256=sha(manifest_path),
        selected_modules=len(selected), selected_source_bytes=byte_count,
        provider_module_counts=provider_counts, required_flags=sorted(FLAGS),
        forbidden_constructs_found=0, source_postulates_found=0,
        explicit_source_holes_found=0, proof_escapes_found=0,
        source_inventory_sha256=hashlib.sha256(json.dumps(inventories,
            sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        external_modules=sorted(builtins), external_scope='Agda builtins from the pinned compiler',
        dependency_graph_closed=True, tagged_P1_files_unchanged=23,
        agda_check_performed_by_this_audit=False, Problem2_checked=False,
        mathematical_objective_complete=False)
