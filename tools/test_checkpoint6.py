#!/usr/bin/env python3
"""Small supervised checkpoint tests. No initial solve and no proof claims."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import ref
import solve6
import frontier6
from test_native6 import reachable


class CheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = solve6.build()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=solve6.BUILD, prefix='checkpoint-test-')
        self.base = Path(self.directory.name)
        self.state = reachable(35, 6)
        self.config = dict(tt_bits=10, small=0)

    def tearDown(self):
        self.directory.cleanup()
        ref.value.cache_clear()

    def test_exact_scalar_and_reuse(self):
        states = [reachable(seed, 6) for seed in range(4)]
        states += [ref.State(6, tuple(map(int, '210222' + '2' * 30)), ref.BLACK)]
        values = []
        for i, state in enumerate(states):
            expected = ref.value(state); values.append(expected)
            path = self.base / str(i)
            cold = solve6.query('solve', state, save_tt=path, **self.config)
            warm = solve6.query('solve', state, load_tt=path, **self.config)
            self.assertEqual((cold['value'], warm['value']), (expected, expected))
            self.assertEqual(cold['checkpoint']['created']['cache_sha256'],
                             warm['checkpoint']['loaded']['cache_sha256'])
            for direction in ('lower', 'upper'):
                self.assertTrue(solve6.bounds(state, direction, expected, load_tt=path, **self.config))
        self.assertTrue(any(v > 0 for v in values)); self.assertTrue(any(v < 0 for v in values))

    def test_frontier_and_study_snapshot(self):
        expected = ref.value(self.state)
        path = self.base / 'study.tt'
        records = list(frontier6.study(self.state, threshold=expected, frontier_grid='32,34',
            max_states=1000, max_nodes=100000, max_memory_mb=32, max_cpu_seconds=2,
            save_tt=path, **self.config))
        self.assertTrue(records[0]['complete'])
        self.assertEqual(records[0]['checkpoint']['created']['stage'], 'after-exact-before-frontier')
        self.assertTrue(all(r['checkpoint']['created']['cache_sha256'] ==
                            records[0]['checkpoint']['created']['cache_sha256'] for r in records))
        options = dict(threshold=expected, frontier_discs=34, max_states=1000,
                       max_nodes=100000, max_memory_mb=32, emit_states=True, **self.config)
        cold = frontier6.query(self.state, **options)
        first = frontier6.query(self.state, load_tt=path, **options)
        again = frontier6.query(self.state, load_tt=path, **options)
        for key in ('complete', 'tree_nodes_S', 'unique_dag_nodes', 'frontier_distinct_L',
                    'hint_occurrences_H', 'dag_edges', 'dedup_hits', 'states'):
            self.assertEqual(cold[key], first[key]); self.assertEqual(first[key], again[key])
        for key in ('nodes', 'native_calls', 'tt_hits', 'tt_collisions'):
            self.assertEqual(first[key], again[key])

    def test_rejections(self):
        path = self.base / 'good.tt'
        solve6.query('solve', self.state, save_tt=path, **self.config)
        with self.assertRaises(ValueError):
            solve6.query('solve', self.state, save_tt=path, **self.config)
        with self.assertRaises(ValueError):
            solve6.query('moves', self.state, load_tt=path, **self.config)
        with self.assertRaises(ValueError):
            solve6.query('solve', self.state, load_tt=Path('/tmp/outside-results'), **self.config)
        with self.assertRaises(ValueError):
            solve6.query('solve', self.state, load_tt=path, tt_bits=12, small=0)
        sidecar = Path(str(path) + '.json'); original = sidecar.read_text()
        manifest = json.loads(original); manifest['build']['source_sha256'] = 'wrong'
        sidecar.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            solve6.query('solve', self.state, load_tt=path, **self.config)
        sidecar.write_text(original)
        data = path.read_bytes()
        for name, damaged in (('header', b'X' + data[1:]), ('short', data[:-1]),
                              ('long', data + b'X'), ('body', data[:-1] + bytes([data[-1] ^ 1]))):
            bad = self.base / name; bad.write_bytes(damaged)
            Path(str(bad) + '.json').write_text(original)
            with self.assertRaises(ValueError):
                solve6.query('solve', self.state, load_tt=bad, **self.config)
            if name != 'body':
                result = subprocess.run([str(self.binary), 'solve', '--position',
                    solve6.position012(self.state), '--tt-bits', '10', '--small', '0',
                    '--load-tt', str(bad)], capture_output=True)
                self.assertEqual(result.returncode, 2)
        result = subprocess.run([str(self.binary), 'solve', '--tt-bits', '12', '--small', '0',
                                 '--load-tt', str(path)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        result = subprocess.run([str(self.binary), 'moves', '--load-tt', str(path)], capture_output=True)
        self.assertEqual(result.returncode, 2)

    def test_large_node_cap_validation(self):
        terminal = ref.State(6, (2,) * 36, ref.BLACK)
        result = frontier6.query(terminal, threshold=36, max_nodes=3000000000,
                                 max_states=1, max_memory_mb=32, **self.config)
        self.assertTrue(result['complete'])
        self.assertEqual(result['request']['max-nodes'], 3000000000)
        self.assertLess(result['nodes'], 10)
        for cap in ('-1', '0', '+3', ' 3', '3 ', '3junk', '3.0', '',
                    '1000000000001', '18446744073709551616'):
            result = subprocess.run([str(self.binary), 'frontier', '--position', '2' * 36,
                                     '--max-nodes', cap], capture_output=True)
            self.assertEqual(result.returncode, 2, cap)

    def test_aborted_prefix_cache_remains_sound(self):
        expected = ref.value(self.state)
        path = self.base / 'aborted.tt'
        result = frontier6.query(self.state, threshold=expected, frontier_discs=36,
            max_states=1000, max_nodes=1, max_memory_mb=32, save_tt=path, **self.config)
        self.assertTrue(result['oracle_aborted'])
        self.assertEqual(solve6.solve(self.state, load_tt=path, **self.config), expected)
        # Exercise the store guard directly, including a previously valid slot.
        harness = self.base / 'guard.c'
        harness.write_text('#define main native_main\n#include "' + str(solve6.SOURCE) +
            '"\n#undef main\nint main(void) { tt=calloc(1,sizeof(Bucket)); tt_mask=0; '
            'tt_store(1,2,34,7,7,64); Bucket before=tt[0]; oracle_aborted=1; '
            'tt_store(1,2,34,0,0,1); tt_store(4,8,33,0,0,1); '
            'return memcmp(&before,tt,sizeof(Bucket)) != 0; }\n')
        binary = self.base / 'guard'
        subprocess.run([json.loads((solve6.BUILD / 'build.json').read_text())['compiler'],
                        '-O2', '-std=c11', str(harness), '-o', str(binary)], check=True, timeout=30)
        subprocess.run([str(binary)], check=True, timeout=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
