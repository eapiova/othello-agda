"""AI-assisted small regression checks for benchmark analysis (no Agda runs)."""
import json
from pathlib import Path
import tempfile
import unittest

import bench6


def observation(w, cpu, status='accepted', split='train', label='sample'):
    return dict(native_W=w, cpu_seconds=cpu, status=status, split=split,
                label=label, rules='fast', direction='lower', empties=8,
                peak_rss_gib=0.9, rss_lower_gib=0.9)


class CpuModelTests(unittest.TestCase):
    def test_nonzero_intercept_and_slope(self):
        fit = bench6.fit_cpu([observation(w, 9 + 0.002*w) for w in (10, 100, 1000, 10000)])
        self.assertTrue(fit['identifiable'])
        self.assertAlmostEqual(fit['intercept_cpu_seconds'], 9, places=6)
        self.assertAlmostEqual(fit['cK_cpu_seconds_per_node'], .002, places=8)

    def test_censored_lower_bound_influences_fit(self):
        exact = [observation(w, 9 + .002*w) for w in (100, 1000, 10000)]
        fit = bench6.fit_cpu(exact + [observation(10000, 60, 'cpu-limit')])
        predicted = fit['intercept_cpu_seconds'] + fit['cK_cpu_seconds_per_node']*10000
        self.assertGreater(predicted, 29)
        self.assertEqual(fit['censored_count'], 1)
        self.assertEqual(fit['completion_lower_bounds'], [{'native_W': 10000, 'cpu_seconds': 60}])
        # A bound is a one-sided loss: a compatible low bound does not alter fit.
        compatible = bench6.fit_cpu(exact + [observation(10000, 20, 'rss-threshold')])
        self.assertAlmostEqual(compatible['intercept_cpu_seconds'], 9, places=6)
        self.assertAlmostEqual(compatible['cK_cpu_seconds_per_node'], .002, places=8)

    def test_sparse_unidentifiable(self):
        for rows in ([], [observation(100, 9)], [observation(100, 9), observation(100, 10)],
                     [observation(100, 15, 'timeout')]):
            fit = bench6.fit_cpu(rows)
            self.assertFalse(fit['identifiable'])
            self.assertIsNone(fit['intercept_cpu_seconds'])
            self.assertIsNone(fit['cK_cpu_seconds_per_node'])

    def test_held_out_retention_and_gate(self):
        rows = [observation(w, 9 + .002*w) for w in (100, 1000, 10000)]
        rows += [observation(200, 9.4, split='held-out', label='ok'),
                 observation(300, 12, 'timeout', 'held-out', 'timeout'),
                 observation(400, 1, 'check-failed', 'held-out', 'bad'),
                 dict(observation(500, 0, 'unmeasured', 'held-out', 'pending'))]
        group = bench6.summarize_group(rows)
        held = group['held_out']
        self.assertEqual([r['status'] for r in held], ['accepted', 'timeout', 'check-failed', 'unmeasured'])
        self.assertAlmostEqual(held[0]['cpu_prediction_over_actual'], 1, places=6)
        self.assertTrue(held[0]['cpu_within_30_percent'])
        self.assertIn('observed_completion_cpu_lower_bound', held[1])
        self.assertNotIn('observed_completion_cpu_lower_bound', held[2])
        self.assertIsNone(group['held_out_cpu_30_percent_gate'])
        self.assertFalse(group['held_out_cpu_gate_complete'])
        self.assertFalse(group['rss_envelope']['extrapolation_guaranteed'])
        poor = bench6.summarize_group(rows[:3] + [observation(200, 100, split='held-out')])
        self.assertFalse(poor['held_out_cpu_30_percent_gate'])

    def test_analyze_retains_failures_and_rejects_source_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job = root / 'job.json'
            record = root / 'record.json'
            job.write_text(json.dumps(dict(label='bad', source_sha256='frozen', native_W=100,
                                          rules='fast', direction='lower', empties=8, split='held-out')))
            measurement = dict(label='bad', source_sha256='frozen', cpu_seconds=2,
                               peak_rss_gib=.4, exit_code=1, accepted=False, stop_reason=None)
            record.write_text(json.dumps(measurement))
            analysis = bench6.analyze([job], [record])
            held = analysis['groups']['fast/lower/8']['held_out'][0]
            self.assertEqual(held['status'], 'check-failed')
            self.assertNotIn('observed_completion_cpu_lower_bound', held)
            measurement['source_sha256'] = 'different'
            record.write_text(json.dumps(measurement))
            with self.assertRaisesRegex(ValueError, 'source differs'):
                bench6.analyze([job], [record])


if __name__ == '__main__':
    unittest.main()
