import json
from pathlib import Path
import tempfile
import unittest
import report6


class ReportTests(unittest.TestCase):
    def fixture(self, root):
        states = []
        for index, work in enumerate((100, 1000, 500)):
            states.append(dict(id=f's{index}', empties=8,
                split='held-out' if index == 2 else 'train', state='fixture-state',
                value=4, mirror={d: {'nodes': work} for d in ('lower', 'upper')}))
        data = {'states': states}
        for state in states:
            for rules in ('rules', 'fast'):
                for direction in ('lower', 'upper'):
                    label = f"bench6-{state['id']}-{rules}-{direction}"
                    job = dict(label=label, state_id=state['id'], empties=8,
                        split=state['split'], state=state['state'], threshold=4,
                        rules=rules, direction=direction,
                        native_W=state['mirror'][direction]['nodes'], source_sha256='source')
                    record = dict(format='othello-job-v2', label=label,
                        source_sha256='source', executable_sha256='agda', accepted=True,
                        cpu_seconds=9 + .001 * job['native_W'], peak_rss_gib=1,
                        exit_code=0, stop_reason=None)
                    (root/(label+'.job.json')).write_text(json.dumps(job))
                    (root/(label+'.json')).write_text(json.dumps(record))
        return data

    def test_unstarted_held_out_job_prevents_complete_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); data = self.fixture(root)
            label = 'bench6-s2-fast-upper'
            (root/(label+'.job.json')).unlink(); (root/(label+'.json')).unlink()
            result = report6.report(data, [root], [])
            self.assertEqual(result['expected_jobs'], 12)
            self.assertEqual(result['measured_jobs'], 11)
            self.assertFalse(result['measurements_complete'])
            group = result['combined_rules_direction']['fast/upper']
            self.assertFalse(group['held_out_cpu_gate_complete'])
            self.assertIsNone(group['held_out_cpu_30_percent_gate'])
            self.assertEqual(group['held_out'][0]['status'], 'unmeasured')

    def test_mixed_binaries_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); data = self.fixture(root)
            path = root/'bench6-s0-fast-upper.json'
            record = json.loads(path.read_text()); record['executable_sha256'] = 'other'
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'different Agda binaries'):
                report6.report(data, [root], [])

    def test_dataset_disagreement_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); data = self.fixture(root)
            data['states'][0]['value'] = 5
            with self.assertRaisesRegex(ValueError, 'differs from frozen dataset'):
                report6.report(data, [root], [])

    def test_search_implementations_are_not_mixed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); data = self.fixture(root)
            path = root/'bench6-s0-fast-upper.job.json'
            job = json.loads(path.read_text()); job['search_kind'] = 'boolean'
            path.write_text(json.dumps(job))
            with self.assertRaisesRegex(ValueError, 'different search implementation'):
                report6.report(data, [root], [])


if __name__ == '__main__':
    unittest.main()
