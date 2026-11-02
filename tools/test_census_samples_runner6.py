"""Regression: census JSON handling must not intercept metadata subprocesses."""
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import canonical_census6 as base
import census_samples6 as samples
from run_job import atomic_json


class RunnerTests(unittest.TestCase):
    def test_service_status_is_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            atomic_json(root/'build.json', dict(scope='runner fixture only'))
            args = SimpleNamespace(max_states=100, sample_cap=50, sample_count=8,
                output=root/'report.json', samples_output=root/'data.json', build=root)
            calls = []
            def original(command, **kwargs):
                calls.append(command)
                payload = ('ActiveState=inactive\n' if command[0]=='metadata' else
                    json.dumps(dict(complete=True, samples=[], statistics={}, unique_dag_nodes=1)))
                return subprocess.CompletedProcess(command, 0, payload, '')
            saved_validator = base.checked_build
            def coordinator(arguments, *, build_validator, execute_native):
                self.assertIs(build_validator, samples.checked_build)
                self.assertIs(base.checked_build, saved_validator)
                self.assertIs(subprocess.run, original)
                self.assertEqual(subprocess.run(['metadata']).stdout, 'ActiveState=inactive\n')
                result = execute_native(['native','frontier','--emit-states','0'])
                counts = json.loads(result.stdout)
                self.assertNotIn('samples', counts)
                atomic_json(arguments.output, dict(command=['native','frontier'], counts=counts))
            with patch.object(subprocess, 'run', original), patch.object(base, 'run', coordinator):
                samples.run(args)
            self.assertEqual(calls[0], ['metadata'])
            self.assertEqual(calls[1][1], 'sample')
            self.assertEqual(json.loads(args.samples_output.read_text())['samples'], [])
            self.assertEqual(json.loads(args.output.read_text())['format'], 'othello-census-samples6-run-v1')
            self.assertIs(base.checked_build, saved_validator)


if __name__ == '__main__': unittest.main()
