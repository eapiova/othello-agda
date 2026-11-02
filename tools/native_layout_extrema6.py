#!/usr/bin/env python3
"""Untrusted reversible layout counters identifying actual extreme part IDs.

The sampler, solver, game rules, line pins and TT remain unchanged. New fields
only remember the first owner index attaining an existing layout maximum.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import native_layout_samples6 as sample
from run_job import atomic_json, utc

FORMAT = 'othello-native-layout-extrema6-build-v1'
decode_samples = sample.decode_samples
convert_body = sample.convert_body


def generated_source(raw, pins=None):
    original = sample.generated_source(raw, pins)
    patches = [
        ('static uint64_t layout_import_sum,layout_import_max,layout_direct_sum,layout_direct_max;',
         'static uint64_t layout_import_sum,layout_import_max,layout_direct_sum,layout_direct_max;\n'
         'static size_t extrema_import_part,extrema_direct_part,extrema_tokens_part;'),
        ('if(imports>layout_import_max)layout_import_max=imports;',
         'if(imports>layout_import_max){layout_import_max=imports;extrema_import_part=index;}'),
        ('if(direct>layout_direct_max)layout_direct_max=direct;',
         'if(direct>layout_direct_max){layout_direct_max=direct;extrema_direct_part=index;}'),
        ('if(layout_part_tokens>layout_max_part_tokens)layout_max_part_tokens=layout_part_tokens;',
         'if(layout_part_tokens>layout_max_part_tokens){layout_max_part_tokens=layout_part_tokens;extrema_tokens_part=index;}'),
        ('  layout_release();',
         r'''  printf(",\"layout_imported_citations_max_part\":%zu,\"layout_direct_dependencies_max_part\":%zu,\"layout_max_part_tokens_part\":%zu",extrema_import_part,extrema_direct_part,extrema_tokens_part);
  layout_release();'''),
    ]
    source = original
    for old, new in patches:
        sample.require(source.count(old) == 1, 'unexpected extrema instrumentation: ' + old[:80])
        source = source.replace(old, new, 1)
    restored = source
    for old, new in reversed(patches):
        sample.require(restored.count(new) == 1, 'ambiguous extrema delta')
        restored = restored.replace(new, old, 1)
    sample.require(restored == original, 'extrema delta changes unrelated native bytes')
    return source


def instrumentation_hashes():
    return dict(sample.instrumentation_hashes(), **{Path(__file__).name: sample.layout.wire.solve6.sha256(Path(__file__))})


def build(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    line = json.loads(args.line.read_text()) if args.line else None
    pins = sample.layout.wire.line_pins6.plan(line)['pins'] if line else None
    source = output / 'census.c'
    source.write_text(generated_source(sample.layout.wire.solve6.SOURCE.read_text(), pins))
    compiler = Path(shutil.which('cc')).resolve(strict=True)
    binary = output / 'census'
    command = [str(compiler), *sample.layout.wire.solve6.FLAGS, str(source), '-o', str(binary)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=30)
    sample.require(done.returncode == 0, done.stderr)
    sha = sample.layout.wire.solve6.sha256
    report = dict(format=FORMAT, status='complete', created_utc=utc(),
        reference_source_sha256=sha(sample.layout.wire.solve6.SOURCE), source_sha256=sha(source),
        binary=str(binary), binary_sha256=sha(binary), compiler=str(compiler), compiler_sha256=sha(compiler),
        flags=list(sample.layout.wire.solve6.FLAGS), command=command, compile_stderr=done.stderr,
        pins=pins, line_sha256=sha(args.line) if args.line else None,
        instrumentation_sha256=instrumentation_hashes(), solver_rules_tt_bytes_unchanged=True,
        compact_memo=True, initial_problem2_proved=False, optimal_pair_proved=False,
        production_authorized=False, scope='existing native sample plus first extrema indices only')
    atomic_json(output / 'build.json', report)
    return report


def checked_build(path):
    path = path.resolve()
    report = json.loads((path / 'build.json').read_text())
    sha = sample.layout.wire.solve6.sha256
    binary, compiler = Path(report['binary']), Path(report['compiler'])
    expected = generated_source(sample.layout.wire.solve6.SOURCE.read_text(), report.get('pins')).encode()
    sample.require(report.get('format') == FORMAT and report.get('status') == 'complete'
        and report.get('solver_rules_tt_bytes_unchanged') is True and report.get('compact_memo') is True
        and binary == path / 'census' and report.get('reference_source_sha256') == sha(sample.layout.wire.solve6.SOURCE)
        and report.get('source_sha256') == hashlib.sha256(expected).hexdigest()
        and (path / 'census.c').read_bytes() == expected and report.get('binary_sha256') == sha(binary)
        and report.get('compiler_sha256') == sha(compiler)
        and report.get('flags') == list(sample.layout.wire.solve6.FLAGS)
        and report.get('command') == [str(compiler), *sample.layout.wire.solve6.FLAGS, str(path / 'census.c'), '-o', str(binary)]
        and report.get('instrumentation_sha256') == instrumentation_hashes()
        and all(report.get(k) is False for k in ('initial_problem2_proved', 'optimal_pair_proved', 'production_authorized')),
        'extrema build provenance changed')
    return report, binary


def extrema(counts):
    sample.require(counts.get('complete') and counts.get('layout_complete')
                   and not counts.get('layout_censored') and not counts.get('count_overflow'),
                   'complete uncensored layout required')
    parts = sample.integer(counts['layout_parts'], 1, 40000, 'layout parts')
    ids = []
    for field in ('layout_imported_citations_max_part', 'layout_direct_dependencies_max_part',
                  'layout_max_part_tokens_part'):
        ids.append(sample.integer(counts[field], 0, parts - 1, field))
    return sorted(set(ids))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--line', type=Path)
    result = build(parser.parse_args())
    print(json.dumps(dict(status='complete', binary_sha256=result['binary_sha256'])))


if __name__ == '__main__':
    main()
