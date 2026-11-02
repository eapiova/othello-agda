#!/usr/bin/env python3
"""Independent small layout fixtures; full initial measurements run elsewhere.

The default unit suite makes one small native build. The --build runner is for
tracked desktop validation against the existing 72 scalar/reference cases.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import canonical_census6 as base
import census_wire6 as wire
import compact_shared6 as compact
from generate6 import encode_state
import global_assembly6 as assembly
import global_shared6 as shared
import ref
from run_job import atomic_json, utc
import test_canonical_census6 as scalar
import test_census_wire6 as replay
import wire_layout6 as layout
import wire_pilot6 as pilot


def settings(**updates):
    values = dict(counts_only=True, layout_limit_mib=512, max_entries=200,
        max_tokens=32000, max_records=200000000, inline_limit=256,
        record_limit=1048576, body_fuel=80)
    values.update(updates)
    return SimpleNamespace(**values)


def command(binary, case, path=None, **limits):
    # Reuse only the bounded native invocation, not its expected export counts.
    argv = replay.command(binary, case, Path('unused'))[:-4]
    argv[1] = 'layout'
    argv += layout.native_options(settings(**limits))
    if path is not None:
        argv += ['--wire-output', str(path), '--wire-limit-mib', '1']
    return argv


def python_counts(path, max_entries=200, max_tokens=32000):
    """Independent Python partition and exact set closure, on small fixtures."""
    entries = [dict(state=k, certificate=t, references=sorted(r)) for k, t, r in wire.records(path)]
    parts, owners = assembly.partition(entries, max_tokens=max_tokens, max_entries=max_entries)
    targets = []
    ancestors = []
    for index, part in enumerate(parts):
        deps = sorted({owners[r] for e in part for r in e['references'] if owners[r] != index})
        closure = set(deps)
        for dep in deps:
            closure.update(ancestors[dep])
        ancestors.append(closure)
        targets.append(dict(kind='part', entries=len(part), tokens=sum(assembly.tokens(e['certificate']) for e in part),
            compact_bytes=len(compact.encode((e['state'], e['certificate']) for e in part).encode()),
            dependencies=deps, imported_citations=len({r for e in part for r in e['references'] if owners[r] != index}),
            transitive_parts=len(closure), transitive_entries=sum(len(parts[j]) for j in closure)))
    if not parts:
        raise ValueError('empty fixture')
    root_part = owners[entries[-1]['state']]
    closure = ancestors[root_part] | {root_part}
    targets.append(dict(kind='assembly', transitive_parts=len(closure),
        transitive_entries=sum(len(parts[j]) for j in closure)))
    return layout.plan_counts(dict(targets=targets), path.stat().st_size)


def assert_counts(native, expected):
    assert native['layout_complete'] and not native['layout_censored'], native
    for key, value in expected.items():
        assert native[key] == value, (key, native[key], value)
    assert native['wire_records'] == native['layout_records']
    assert native['wire_tokens'] == native['layout_tokens']
    assert native['wire_bytes'] == native['layout_source_wire_bytes']
    assert native['layout_peak_bytes'] <= native['layout_limit_bytes'] <= 512 * 1024**2
    assert all(native[k] is False for k in ('initial_problem2_proved', 'optimal_pair_proved', 'production_authorized'))


def emit_fixture(path, native, case, output, *, max_entries=200, max_tokens=32000):
    """A real wire_pilot6.emit invocation; no kernel claim is made."""
    report = output.with_suffix('.native.json')
    raw = path.read_bytes()
    report.write_text(json.dumps(dict(format='othello-census-wire6-run-v1',
        status='complete-untrusted-wire', wire_complete=True, native_complete=True,
        donor_unchanged=True, table_unchanged=True, wire_output_sha256=hashlib.sha256(raw).hexdigest(),
        root_key=('w' if case['turn'] == ref.WHITE else 'b') + case['position'],
        request=dict(direction=case['direction'], threshold=4), counts=native)))
    with contextlib.redirect_stdout(io.StringIO()):
        pilot.emit(SimpleNamespace(wire=path, report=report, output=output, max_records=20000,
            max_entries=max_entries, max_tokens=max_tokens, max_source_bytes=1048576,
            max_total_source_bytes=33554432))
    plan = json.loads((output / 'plan.json').read_text())
    expected = layout.plan_counts(plan, len(raw))
    assert_counts(native, expected)
    return expected


def run(args):
    """Tracked desktop API: build/reference_build/output, optional pinned=True.

    The unpinned runner validates all 72 old reference cases, pass/D4 images,
    losing pins, limits and a real Python emit plan. The pinned runner checks
    late supplied-line roots across both directions and all eight D4 images.
    """
    built, binary = layout.checked_build(args.build)
    directory = args.output.parent / (args.output.stem + '-fixtures')
    directory.mkdir(parents=True, exist_ok=False)
    pinned = getattr(args, 'pinned', False)
    cases = []
    reference = None
    if pinned:
        if not built.get('pins'):
            raise ValueError('pinned fixture runner requires pins')
        for direction, rows in built['pins'].items():
            for row in rows:
                root = replay.decode_state(row['state'])
                if root.cells.count(0) > 6:
                    continue
                for tag in range(8):
                    s = root._replace(cells=scalar.image(root.cells, tag))
                    cases.append(dict(position=''.join(map(str, s.cells)), turn=s.turn,
                        direction=direction, threshold=4, holds=True))
        if len(cases) < 32 or {c['direction'] for c in cases} != {'lower', 'upper'}:
            raise ValueError('insufficient pinned late-root coverage')
    else:
        if built.get('pins'):
            raise ValueError('reference fixture runner requires unpinned build')
        _, reference = base.checked_build(args.reference_build)
        source_report = directory / 'scalar.json'
        with contextlib.redirect_stdout(io.StringIO()):
            scalar.run(SimpleNamespace(build=args.reference_build, output=source_report, reference_build=None))
        cases = json.loads(source_report.read_text())['late_cases']
        assert len(cases) == 72
        root = ref.State(6, tuple(map(int, '210222' + '2' * 30)), ref.BLACK)
        for tag in range(8):
            s = root._replace(cells=scalar.image(root.cells, tag))
            cases.append(dict(position=''.join(map(str, s.cells)), turn=s.turn,
                direction='lower', threshold=4, holds=True))
    completed = rejected = rows_replayed = real_plans = 0
    for index, case in enumerate(cases):
        path = directory / f'{index}.wire'
        argv = command(binary, case, path, max_entries=1, inline_limit=2)
        done = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        native = json.loads(done.stdout)
        if reference is not None:
            baseline_argv = replay.command(reference, case, path)[:-4]
            baseline_argv[1] = 'frontier'
            baseline = subprocess.run(baseline_argv, capture_output=True, text=True, timeout=10)
            assert baseline.returncode == 0, baseline.stderr
            comparison = json.loads(baseline.stdout)
            for field in ('complete', 'root_validated', 'root_holds', 'tree_nodes_S', 'unique_dag_nodes',
                          'dag_edges', 'dedup_hits', 'count_overflow'):
                assert native[field] == comparison[field], field
        if not case['holds']:
            assert done.returncode != 0 and not native['layout_complete'] and native['layout_censored'] and not path.exists()
            rejected += 1
            continue
        assert done.returncode == 0, done.stderr
        assert_counts(native, python_counts(path, max_entries=1))
        proofs = [(replay.decode_state(k), t) for k, t, _ in wire.records(path)]
        root = ref.State(6, tuple(map(int, case['position'])), case['turn'])
        assert shared.replay_many(proofs, [root], case['direction'], case['threshold'])
        rows_replayed += len(proofs)
        pure = subprocess.run(command(binary, case, max_entries=1, inline_limit=2), capture_output=True, text=True, timeout=10)
        assert pure.returncode == 0, pure.stderr
        assert_counts(json.loads(pure.stdout), python_counts(path, max_entries=1))
        if case['threshold'] == 4:
            emit_fixture(path, native, case, directory / f'plan-{index}', max_entries=1)
            real_plans += 1
        completed += 1
    negatives = 0
    good = next(c for c in cases if c['holds'] and c['threshold'] == 4)
    for options in (dict(body_fuel=1), dict(record_limit=16), dict(max_tokens=1)):
        result = subprocess.run(command(binary, good, **options), capture_output=True, text=True, timeout=10)
        counts = json.loads(result.stdout)
        # A terminal root may fit fuel/token=1; require actual nonterminal case.
        if counts['layout_complete']:
            continue
        assert result.returncode != 0 and counts['layout_censored']
        negatives += 1
    argv = command(binary, good)
    for flag, value in (('--max-states', '1'), ('--max-nodes', '1')):
        argv[argv.index(flag) + 1] = value
    result = subprocess.run(argv, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0 and not json.loads(result.stdout)['layout_complete']
    negatives += 1
    losing_pin = False
    if not pinned:
        bad = None
        for case in cases[:72]:
            if not case['holds'] or case['threshold'] != case['scalar_value']:
                continue
            s = scalar.canonical(ref.State(6, tuple(map(int, case['position'])), case['turn']))
            if s.turn != (ref.WHITE if case['direction'] == 'lower' else ref.BLACK) or not ref.placements(s):
                continue
            for selected, child in enumerate(ref.successors(s)):
                value = ref.value(child)
                if value < case['threshold'] if case['direction'] == 'lower' else value > case['threshold']:
                    bad = (dict(case, position=''.join(map(str, s.cells))),
                        {case['direction']: [dict(state=encode_state(s), selected_index=selected)]})
                    break
            if bad:
                break
        assert bad, 'missing losing legal pin fixture'
        source = directory / 'losing-pin.c'
        source.write_text(layout.generated_source(wire.solve6.SOURCE.read_text(), bad[1]))
        losing = directory / 'losing-pin'
        compile_result = subprocess.run([built['compiler'], *wire.solve6.FLAGS, str(source), '-o', str(losing)],
            capture_output=True, text=True, timeout=30)
        assert compile_result.returncode == 0, compile_result.stderr
        result = subprocess.run(command(losing, bad[0]), capture_output=True, text=True, timeout=10)
        counts = json.loads(result.stdout)
        assert result.returncode != 0 and counts['root_holds'] and not counts['complete'] and not counts['layout_complete']
        losing_pin = True
    assert real_plans and completed and negatives
    assert layout.checked_build(args.build)[0] == built
    report = dict(format='othello-wire-layout6-tests-v1', accepted=True, created_utc=utc(),
        build_sha256=wire.solve6.sha256(args.build / 'build.json'), pinned=pinned,
        reference_counter_cases=72 if not pinned else 0, completed_layouts=completed,
        false_bounds_rejected=rejected, records_replayed=rows_replayed,
        real_python_emit_plans=real_plans, counts_only_matches_fixture_wire=True,
        losing_pin_rejected=losing_pin, bounded_negative_cases=negatives,
        independent_partition_closure=True, initial_problem2_proved=False,
        optimal_pair_proved=False, production_authorized=False,
        scope='small fixtures only; no full initial layout measurement or Agda premise')
    atomic_json(args.output, report)
    print(json.dumps(report))
    return report


class LayoutTests(unittest.TestCase):
    def test_explicit_counts_only_and_limits(self):
        for changes in (dict(counts_only=False), dict(layout_limit_mib=513), dict(max_entries=201),
                        dict(max_tokens=32001), dict(record_limit=15), dict(body_fuel=0),
                        dict(max_records=0), dict(inline_limit=0)):
            with self.assertRaises(ValueError):
                layout.native_options(settings(**changes))

    def test_grammar_and_set_closure(self):
        # Identity and D4 each cost one Agda token; citation payload bytes are
        # separate. Repeated citation states count once per importing part.
        self.assertEqual(assembly.tokens(compact.unpack_certificate('F2KR7')), 3)
        targets = [dict(kind='part', entries=2, tokens=3, compact_bytes=30,
                       dependencies=[], imported_citations=0, transitive_parts=0, transitive_entries=0),
                   dict(kind='part', entries=1, tokens=1, compact_bytes=15,
                       dependencies=[0], imported_citations=2, transitive_parts=1, transitive_entries=2),
                   dict(kind='assembly', transitive_parts=2, transitive_entries=3)]
        counts = layout.plan_counts(dict(targets=targets), 100)
        self.assertEqual(counts['layout_imported_citations_sum'], 2)
        self.assertEqual(counts['layout_direct_dependencies_sum'], 1)
        self.assertEqual(counts['layout_assembly_transitive_entries'], 3)
        self.assertEqual(counts['layout_source_wire_bytes'], 100)
        self.assertEqual(counts['layout_compact_bytes'], 45)

    def test_generator_is_separate_and_preserves_original(self):
        original = wire.solve6.SOURCE.read_text()
        cut = layout.cuts.generated_source(original)
        result = layout.generated_source(original)
        self.assertIn('explicit --counts-only required', result)
        self.assertIn('wire_indegree[i]&=WIRE_CUT', result)
        self.assertIn('LAYOUT_ASSIGNED', result)
        self.assertIn('layout_stop()', result)
        self.assertEqual(layout.cuts.generated_source(original), cut)
        self.assertEqual(wire.solve6.SOURCE.read_text(), original)
        with self.assertRaises(ValueError):
            layout.generated_source(original.replace('static int integer(', 'static int changed_integer('))

    def test_native_small_wire_and_real_emit(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / 'results'
            directory.mkdir()
            build = directory / 'build'
            with contextlib.redirect_stdout(io.StringIO()):
                layout.build(SimpleNamespace(output=build, line=None))
            built, binary = layout.checked_build(build)
            root = ref.State(6, tuple(map(int, '210222' + '2' * 30)), ref.BLACK)
            root = root._replace(cells=scalar.image(root.cells, 2))
            case = dict(position=''.join(map(str, root.cells)), turn=root.turn, direction='lower', threshold=4)
            path = directory / 'fixture.wire'
            done = subprocess.run(command(binary, case, path, max_entries=1, inline_limit=2),
                capture_output=True, text=True, timeout=5)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            native = json.loads(done.stdout)
            expected = emit_fixture(path, native, case, directory / 'prepared', max_entries=1)
            assert_counts(native, python_counts(path, max_entries=1))
            pure = subprocess.run(command(binary, case, max_entries=1, inline_limit=2),
                capture_output=True, text=True, timeout=5)
            self.assertEqual(pure.returncode, 0, pure.stderr)
            assert_counts(json.loads(pure.stdout), expected)
            for options in (dict(body_fuel=1), dict(record_limit=16), dict(max_tokens=1), dict(max_records=1)):
                bad = subprocess.run(command(binary, case, **options), capture_output=True, text=True, timeout=5)
                self.assertNotEqual(bad.returncode, 0)
                self.assertFalse(json.loads(bad.stdout)['layout_complete'])
                self.assertTrue(json.loads(bad.stdout)['layout_censored'])
            argv = command(binary, case)
            argv[argv.index('--max-memory-mb') + 1] = '1'
            argv[argv.index('--max-states') + 1] = '24000'
            bad = subprocess.run(argv, capture_output=True, text=True, timeout=5)
            self.assertNotEqual(bad.returncode, 0)
            # The solver can reject its allocation bound before emitting a
            # layout receipt. Either result is a closed failure, never success.
            if bad.stdout.strip():
                self.assertFalse(json.loads(bad.stdout)['layout_complete'])
            else:
                self.assertIn('memory', bad.stderr.lower())
            for argv in ([str(binary), 'layout'], [str(binary), 'layout', '--counts-only', '--layout-limit-mib', '513']):
                bad = subprocess.run(argv, capture_output=True, text=True, timeout=5)
                self.assertNotEqual(bad.returncode, 0)
            protected = directory / 'protected.wire'
            protected.write_bytes(b'unchanged')
            bad = subprocess.run(command(binary, case, protected), capture_output=True, text=True, timeout=5)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse(json.loads(bad.stdout)['layout_complete'])
            self.assertEqual(protected.read_bytes(), b'unchanged')
            altered = dict(built, flags=['-O0'])
            (build / 'build.json').write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                layout.checked_build(build)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path)
    p.add_argument('--reference-build', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--pinned', action='store_true')
    args = p.parse_args()
    if args.build is None:
        unittest.main(argv=['test_wire_layout6'])
    elif args.output is None or (not args.pinned and args.reference_build is None):
        p.error('tracked fixture runner requires output and unpinned reference-build')
    else:
        run(args)
