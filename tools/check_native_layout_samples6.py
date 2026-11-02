#!/usr/bin/env python3
"""Compare bounded native samples with complete independently replayed wires.

No native result is an Agda premise. Full wires are retained only for small
fixtures; large initial sampling happens separately after this validation.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import random
import subprocess
from types import SimpleNamespace

import compact_shared6 as compact
import census_wire6 as wire
import global_assembly6 as assembly
import global_shared6 as shared
import native_layout_samples6 as sample
import ref
from run_job import atomic_json, utc
import test_census_wire6 as replay
import test_wire_layout6 as fixtures
import wire_layout6 as layout


def run(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    builds = {}
    for pinned in (False, True):
        line = Path('certificates/six-line.json') if pinned else None
        for kind, module in (('layout', layout), ('sample', sample)):
            label = kind + ('-pinned' if pinned else '-unpinned')
            folder = out / label
            with contextlib.redirect_stdout(io.StringIO()):
                built = module.build(SimpleNamespace(output=folder, line=line))
            module.checked_build(folder)
            builds[label] = dict(path=str(folder), build_sha256=wire.solve6.sha256(folder / 'build.json'))
    rng = random.Random(2026101007)
    late = []
    for _ in range(6):
        s = ref.initial(6)
        for _ in range(80):
            children = ref.successors(s)
            if not children:
                break
            if s.cells.count(0) <= 4:
                late.append(s)
                break
            s = rng.choice(children)
    passed = ref.State(6, tuple(map(int, '210222' + '2' * 30)), ref.BLACK)
    late.append(passed)
    line = json.loads(Path('certificates/six-line.json').read_text())
    # A pinned bound near the end of the recorded 16--20 line exercises hints.
    line_root = wire.line_pins6.plan(line)['pins']
    cases = []
    for index, s in enumerate(late):
        ref.value.cache_clear()
        value = ref.value(s)
        for side in ('lower', 'upper'):
            for delta in (0, 1 if side == 'lower' else -1):
                cases.append(dict(position=''.join(map(str, s.cells)), turn=s.turn,
                    direction=side, threshold=value + delta,
                    holds=(delta == 0), pinned=False, fixture=index))
    for side in ('lower', 'upper'):
        item = line_root[side][-1]
        s = replay.decode_state(item['state'])
        cases.append(dict(position=''.join(map(str, s.cells)), turn=s.turn, direction=side,
            threshold=4, holds=True, pinned=True, fixture='pinned-line'))
    rows_replayed = 0
    receipts = []
    for index, case in enumerate(cases):
        suffix = '-pinned' if case['pinned'] else '-unpinned'
        baseline = Path(builds['layout' + suffix]['path']) / 'census'
        binary = Path(builds['sample' + suffix]['path']) / 'census'
        path = out / ('fixture' + str(index) + '.wire')
        argv = fixtures.command(baseline, case, path, max_entries=2, inline_limit=1)
        done = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        atomic_json(out / ('fixture' + str(index) + '-baseline.json'),
            dict(case=case, argv=argv, exit_code=done.returncode, stdout=done.stdout, stderr=done.stderr))
        if not -36 <= case['threshold'] <= 36:
            assert not case['holds'] and done.returncode != 0 and not path.exists()
            receipts.append(dict(case=case, invalid_threshold_rejected=True, stderr=done.stderr))
            continue
        expected = json.loads(done.stdout)
        assert expected['root_holds'] == case['holds']
        parts = expected['layout_parts']
        selected = sorted({min(max(parts - 1, 0), k * max(parts - 1, 0) // 15) for k in range(16)})
        sampled_path = out / ('fixture' + str(index) + '.sample.jsonl')
        command = fixtures.command(binary, case, None, max_entries=2, inline_limit=1)
        command += ['--sample-parts', ','.join(map(str, selected)), '--sample-output', str(sampled_path),
            '--sample-record-cap', '100000', '--sample-output-limit-mib', '1']
        actual = subprocess.run(command, capture_output=True, text=True, timeout=10)
        atomic_json(out / ('fixture' + str(index) + '-sample.json'),
            dict(case=case, argv=command, exit_code=actual.returncode,
                stdout=actual.stdout, stderr=actual.stderr))
        counts = json.loads(actual.stdout)
        for key, value in expected.items():
            if key.startswith('layout_') and key not in ('layout_peak_bytes', 'layout_total_peak_bytes'):
                assert counts[key] == value, (index, key, counts[key], value)
        if not case['holds']:
            assert done.returncode != 0 and actual.returncode != 0 and not counts['layout_complete']
            if sampled_path.exists():
                try:
                    sample.decode_samples(sampled_path)
                except ValueError:
                    pass
                else:
                    raise AssertionError('false bound acquired a complete sample')
            receipts.append(dict(case=case, false_bound_rejected=True))
            continue
        assert done.returncode == actual.returncode == 0 and counts['layout_complete'], actual.stderr
        decoded = sample.decode_samples(sampled_path)
        entries = [dict(state=k, certificate=t, references=sorted(rs)) for k, t, rs in wire.records(path)]
        partitions, owners = assembly.partition(entries, max_entries=2, max_tokens=32000)
        assert len(partitions) == parts
        ranks = {e['state']: j * 200 + row for j, part in enumerate(partitions) for row, e in enumerate(part)}
        for j, chunk in decoded['states'].items():
            assert chunk == dict(rows=len(partitions[j]),
                text=''.join(compact.pack_state(e['state']) for e in partitions[j]))
        for c in decoded['cases']:
            expected_bodies = []
            expected_refs = []
            for e in partitions[c['part']]:
                # Citation order follows the compact payload, not a sorted set.
                packed = compact.pack_certificate(e['certificate'])
                scalar = replay.decode_state(e['state'])
                ordered = []

                def parse(offset, s):
                    token = e['certificate'][offset]
                    offset += 1
                    if token == 'L':
                        return offset
                    if token == 'K':
                        ordered.append(ranks[wire.line_pins6.encode_state(s)])
                        return offset
                    if token == 'P':
                        return parse(offset, ref.successors(s)[0])
                    end = e['certificate'].index(';', offset)
                    n = int(e['certificate'][offset:end])
                    offset = end + 1
                    if token == 'R':
                        ordered.append(ranks[wire.line_pins6.encode_state(replay.symmetry.transform(s, n))])
                        return offset
                    children = ref.successors(s)
                    if token == 'C':
                        return parse(offset, children[n])
                    assert token == 'F' and n == len(children)
                    for child in children:
                        offset = parse(offset, child)
                    return offset

                assert parse(0, scalar) == len(e['certificate'])
                expected_bodies.append(sample.convert_body(packed, ordered)[0])
                expected_refs.extend(ordered)
            assert c['body_text'] == ''.join(expected_bodies)
            assert c['references'] == expected_refs
        root = ref.State(6, tuple(map(int, case['position'])), case['turn'])
        assert shared.replay_many([(replay.decode_state(e['state']), e['certificate']) for e in entries],
            [root], case['direction'], case['threshold'])
        rows_replayed += len(entries)
        receipts.append(dict(case=case, selected=selected, records=len(entries),
            sample_sha256=wire.solve6.sha256(sampled_path), wire_sha256=wire.solve6.sha256(path)))
    # Real native fail-closed guards complement the Python artifact tests.
    good = next(c for c in cases if c['holds'] and not c['pinned'])
    binary = Path(builds['sample-unpinned']['path']) / 'census'
    negative = []
    for name, options in (
            ('record-cap', ['--sample-record-cap', '1']),
            ('missing-part', ['--sample-parts', '39999']),
            ('body-fuel', ['--wire-body-fuel', '1']),
            ('protected-path', [])):
        path = out / (name + '.partial')
        if name == 'protected-path':
            path.write_bytes(b'unchanged protected artifact')
        command = fixtures.command(binary, good, None, max_entries=2, inline_limit=1)
        command += ['--sample-output', str(path), '--sample-parts', '0',
            '--sample-record-cap', '100000', '--sample-output-limit-mib', '1']
        for key, value in zip(options[::2], options[1::2]):
            if key in command:
                command[command.index(key) + 1] = value
            else:
                command += [key, value]
        done = subprocess.run(command, capture_output=True, text=True, timeout=10)
        counts = json.loads(done.stdout)
        assert done.returncode != 0 and not counts['layout_complete']
        if name == 'protected-path':
            assert path.read_bytes() == b'unchanged protected artifact'
        if path.exists():
            try:
                sample.decode_samples(path)
            except ValueError:
                pass
            else:
                raise AssertionError('bounded negative acquired a complete sample')
        negative.append(dict(name=name, argv=command, exit_code=done.returncode, counts=counts))
    for label, built in builds.items():
        module = sample if label.startswith('sample') else layout
        module.checked_build(Path(built['path']))
    result = dict(format='othello-native-layout-sample-fixtures6-v1', accepted=True, finished_utc=utc(),
        builds=builds, cases=receipts, fixture_cases=len(cases), scalar_replayed_rows=rows_replayed,
        native_negative_fixtures=negative,
        exact_partition_counters=True, exact_numeric_bodies_and_state_chunks=True,
        initial_problem2_proved=False, optimal_initial_pair_proved=False, production_authorized=False)
    atomic_json(out / 'report.json', result)
    print(json.dumps(dict(accepted=True, fixture_cases=len(cases), scalar_replayed_rows=rows_replayed)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
