#!/usr/bin/env python3
"""Bounded subprocess tests; total test-work CPU is well below 60 seconds."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from run_job import LOCK_FD_ENV, LOCK_ROOT_ENV, build_lock, build_lock_path, run_job
from study6 import Ledger

TOOLS = Path(__file__).resolve().parent


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / 'root'
        self.root.mkdir()
        (self.root / 'source.txt').write_text('fixed source\n')
        self.output = self.base / 'results'
        self.records = []

    def tearDown(self):
        print('test measured CPU seconds:', sum(r['cpu_seconds'] for r in self.records))
        self.temp.cleanup()

    def run_python(self, code, **caps):
        defaults = dict(timeout=3, cpu_limit=2, rss_limit_gib=.25, log_limit_mib=.1)
        defaults.update(caps)
        result = run_job('job', [sys.executable, '-c', code], self.output,
                         root=self.root, **defaults)
        self.records.append(result)
        return result

    def assert_pids_gone(self):
        for pid in (self.output / 'job.log').read_text().split():
            if pid.isdigit():
                with self.assertRaises(ProcessLookupError):
                    os.kill(int(pid), 0)

    def test_cpu_child_group_stopped_and_exact_accounting(self):
        child = 'import os; print(os.getpid(), flush=True);\nwhile True: pass'
        code = ('import subprocess,sys\n'
                f'children=[subprocess.Popen([sys.executable,"-c",{child!r}]) for _ in range(3)]\n'
                '[p.wait() for p in children]')
        result = self.run_python(code, cpu_limit=.3)
        self.assertEqual(result['stop_reason'], 'cpu-limit')
        self.assertGreater(result['cpu_seconds'], .1)
        self.assertAlmostEqual(result['cpu_seconds'], result['rusage']['user_seconds'] + result['rusage']['system_seconds'])
        self.assertFalse(result['accepted'])
        self.assert_pids_gone()

    def test_child_memory_is_counted(self):
        child = 'import os,time; print(os.getpid(),flush=True); x=bytearray(100*1024*1024); time.sleep(5)'
        result = self.run_python(f'import subprocess,sys; subprocess.run([sys.executable,"-c",{child!r}])',
                                 rss_limit_gib=.04)
        self.assertEqual(result['stop_reason'], 'rss-threshold')
        self.assertGreater(result['peak_tree_rss_kib'], 40*1024)
        self.assert_pids_gone()

    def test_timeout_and_log_cap(self):
        child = 'import os,time;print(os.getpid(),flush=True);time.sleep(10)'
        result = self.run_python(f'import subprocess,sys;subprocess.run([sys.executable,"-c",{child!r}])', timeout=.15)
        self.assertEqual(result['stop_reason'], 'timeout')
        self.assertLess(result['wall_seconds'], 2)
        self.assert_pids_gone()
        result = self.run_python('import os\nwhile True: os.write(1,b"x"*65536)', log_limit_mib=.01)
        self.assertEqual(result['stop_reason'], 'log-size')
        self.assertLessEqual((self.output / 'job.log').stat().st_size, int(.01*1024**2))

    def test_final_cpu_includes_transient_children(self):
        child = 'import time\ns=time.process_time()\nwhile time.process_time()-s<.08: pass'
        result = self.run_python(f'import subprocess,sys\nfor _ in range(3): subprocess.run([sys.executable,"-c",{child!r}])')
        self.assertTrue(result['accepted'])
        self.assertGreater(result['cpu_seconds'], .24)
        self.assertIn('executable_sha256', result)

    def test_changed_source_rejected(self):
        result = self.run_python('from pathlib import Path;Path("source.txt").write_text("changed")')
        self.assertEqual(result['exit_code'], 0)
        self.assertFalse(result['source_unchanged'])
        self.assertFalse(result['accepted'])
        result = self.run_python('pass', expected_source_sha256='wrong')
        self.assertFalse(result['expected_source_matches'])
        self.assertFalse(result['accepted'])

    def test_caps_positive(self):
        for value in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(argparse.ArgumentTypeError):
                self.run_python('pass', timeout=value)

    def test_reservation_race_and_final_accounting(self):
        path = self.base / 'ledger.json'
        ledger = Ledger(path)
        with self.assertRaises(ValueError):
            ledger.reserve('native', 1)
        ledger.init()
        command = [sys.executable, str(TOOLS / 'study6.py'), '--ledger', str(path), 'reserve', 'native', '14400']
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        results = [(p.communicate(timeout=5), p.returncode) for p in (first, second)]
        self.assertEqual(sorted(code for _, code in results), [0, 2])
        entry = json.loads(next(output[0] for output, code in results if code == 0))
        self.assertEqual(ledger.status()['reserved_cpu_seconds'], 14400)
        record = self.run_python('sum(range(100000))', reservation_id=entry['reservation_id'])
        charged = ledger.finish(entry['reservation_id'], self.output / 'job.json')
        self.assertAlmostEqual(charged['actual_cpu_seconds'], record['cpu_seconds'])
        self.assertEqual(ledger.status()['reserved_cpu_seconds'], 0)
        self.assertLess(abs(ledger.status()['charged_cpu_seconds'] - record['cpu_seconds']), 1e-6)
        self.assertEqual(ledger.finish(entry['reservation_id'], self.output / 'job.json'), charged)
        outstanding = ledger.reserve('kernel', 100)
        self.assertEqual(Ledger(path).status()['outstanding'][outstanding['reservation_id']], outstanding)
        with self.assertRaises(ValueError):
            ledger.reserve('kernel', 43200)
        ledger.reassign('assembly', 'native', 100)
        self.assertEqual(ledger.status()['categories']['native']['allocation_cpu_seconds'], 14500)

    def test_global_budget_after_reassignment(self):
        ledger = Ledger(self.base / 'ledger.json')
        ledger.init()
        for category, seconds in [('native',14400),('kernel',43200),('compiled',14400),('assembly',14400)]:
            ledger.reserve(category, seconds)
        self.assertEqual(ledger.status()['available_cpu_seconds'], 0)
        with self.assertRaisesRegex(ValueError, 'global'):
            ledger.reserve('native', .001)

    def test_extension_preserves_usage_and_is_idempotent(self):
        ledger = Ledger(self.base / 'ledger.json')
        ledger.init()
        entry = ledger.reserve('native', 14400)
        record = self.run_python('pass', reservation_id=entry['reservation_id'])
        ledger.finish(entry['reservation_id'], self.output / 'job.json')
        pending = ledger.reserve('kernel', 100)
        ledger.reassign('compiled', 'native', 100)
        before = ledger.status()
        extended = ledger.extend('more-compute', {'native': 3600, 'assembly': 7200},
                                 'User authorized more compute; bounded next stage.')
        self.assertEqual(extended['total_cpu_seconds'], 86400 + 10800)
        self.assertEqual(extended['available_cpu_seconds'], before['available_cpu_seconds'] + 10800)
        self.assertEqual(extended['charged_cpu_seconds'], before['charged_cpu_seconds'])
        self.assertEqual(extended['outstanding'][pending['reservation_id']], pending)
        self.assertEqual(extended['categories']['native']['allocation_cpu_seconds'], 18100)
        self.assertEqual(ledger.extend('more-compute', {'native': 3600, 'assembly': 7200},
                         'User authorized more compute; bounded next stage.'), extended)
        with self.assertRaisesRegex(ValueError, 'already used'):
            ledger.extend('more-compute', {'native': 7200}, 'Different grant')
        ledger.reserve('native', 18000)
        self.assertAlmostEqual(ledger.status()['charged_cpu_seconds'], record['cpu_seconds'], places=6)

    def test_unrecorded_limit_edit_rejected(self):
        path = self.base / 'ledger.json'
        Ledger(path).init()
        state = json.loads(path.read_text())
        state['total_cpu_us'] += 3600 * 1000000
        state['allocations_us']['native'] += 3600 * 1000000
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'unrecorded budget grant'):
            Ledger(path).status()

    def test_lock_matches_canonical_build_and_isolates_roots(self):
        other = self.base / 'other'
        other.mkdir()
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(build_lock_path(alias), build_lock_path(self.root))
        self.assertNotEqual(build_lock_path(other), build_lock_path(self.root))
        code = ('from pathlib import Path;from run_job import build_lock;import sys;'
                'ctx=build_lock(Path(sys.argv[1]));ctx.__enter__();print("acquired",flush=True)')
        env = dict(os.environ, PYTHONPATH=str(TOOLS))
        with build_lock(self.root):
            held = subprocess.Popen([sys.executable, '-c', code, str(alias)], stdout=subprocess.PIPE, env=env)
            free = subprocess.run([sys.executable, '-c', code, str(other)], capture_output=True, env=env, timeout=3)
            self.assertEqual(free.stdout.strip(), b'acquired')
            time.sleep(.1)
            self.assertIsNone(held.poll())
        self.assertEqual(held.communicate(timeout=3)[0].strip(), b'acquired')
        script = (TOOLS.parent / 'scripts/check.sh').read_text()
        self.assertIn('$task_build/.study6.lock', script)
        self.assertNotIn('/tmp/othello-agda', script)

    def test_nested_runner_inherits_lock_and_accounts_cpu_once(self):
        inner_output = self.base / 'inner-results'
        competitor = ('from pathlib import Path;from run_job import build_lock;'
                      f'\nwith build_lock(Path({str(self.root)!r})): print("acquired",flush=True)')
        burn = 'import time\ns=time.process_time()\nwhile time.process_time()-s<.12: pass'
        code = (f'import sys,os,subprocess\nsys.path.insert(0,{str(TOOLS)!r})\n'
                'from run_job import run_job,LOCK_FD_ENV,LOCK_ROOT_ENV\n'
                'env=os.environ.copy();env.pop(LOCK_FD_ENV,None);env.pop(LOCK_ROOT_ENV,None)\n'
                f'env["PYTHONPATH"]={str(TOOLS)!r}\n'
                f'p=subprocess.Popen([sys.executable,"-c",{competitor!r}],env=env,stdout=subprocess.PIPE)\n'
                'try:\n'
                f' r=run_job("inner",[sys.executable,"-c",{burn!r}],{str(inner_output)!r},root={str(self.root)!r},timeout=2,cpu_limit=1,rss_limit_gib=.25,log_limit_mib=.1)\n'
                ' assert r["accepted"],r\n assert p.poll() is None,"competitor entered held lock"\n'
                'finally:\n p.terminate();p.communicate(timeout=2)\n')
        # Exercise the preparation-lock API used by measure.py as well.
        with build_lock(self.root) as yielded:
            self.assertIsNone(yielded)
            result = run_job('job', [sys.executable, '-c', code], self.output,
                             root=self.root, locked=True, timeout=4, cpu_limit=2,
                             rss_limit_gib=.25, log_limit_mib=.1)
            self.records.append(result)
            self.assertTrue(result['accepted'], (self.output / 'job.log').read_text())
            inner = json.loads((inner_output / 'inner.json').read_text())
            self.assertGreater(inner['cpu_seconds'], .12)
            self.assertGreaterEqual(result['cpu_seconds'], inner['cpu_seconds'])
            self.assertLess(result['cpu_seconds'], inner['cpu_seconds'] + .5)
            env = dict(os.environ, PYTHONPATH=str(TOOLS))
            probe = subprocess.Popen([sys.executable, '-c', competitor], env=env,
                                     stdout=subprocess.PIPE)
            try:
                time.sleep(.1)
                self.assertIsNone(probe.poll(), 'inner runner released ancestor lock')
            finally:
                probe.terminate()
                probe.communicate(timeout=2)

    def test_wrong_root_inherited_fd_cannot_bypass_lock(self):
        other = self.base / 'other'
        other.mkdir()
        code = ('from pathlib import Path;from run_job import build_lock;'
                f'\nwith build_lock(Path({str(other)!r})): print("acquired",flush=True)')
        # Claiming the other root in env cannot make a root descriptor match it.
        with build_lock(self.root), build_lock_path(self.root).open('a') as fd:
            env = dict(os.environ, PYTHONPATH=str(TOOLS),
                       **{LOCK_ROOT_ENV: str(other), LOCK_FD_ENV: str(fd.fileno())})
            with build_lock(other):
                probe = subprocess.Popen([sys.executable, '-c', code], env=env,
                                         pass_fds=(fd.fileno(),), stdout=subprocess.PIPE)
                try:
                    time.sleep(.15)
                    self.assertIsNone(probe.poll())
                except BaseException:
                    probe.kill(); probe.communicate(timeout=2)
                    raise
            self.assertEqual(probe.communicate(timeout=2)[0].strip(), b'acquired')

    def test_nested_runner_timeout_stops_separate_session(self):
        code = (f'import sys\nsys.path.insert(0,{str(TOOLS)!r})\nfrom run_job import run_job\n'
                f'run_job("inner",[sys.executable,"-c","import time;time.sleep(10)"],{str(self.base / "inner-results")!r},'
                f'root={str(self.root)!r},timeout=12,cpu_limit=1,rss_limit_gib=.25,log_limit_mib=.1)')
        result = self.run_python(code, timeout=.3)
        self.assertEqual(result['stop_reason'], 'timeout')
        self.assertLess(result['wall_seconds'], 2)

    def test_nested_session_cpu_and_memory_caps_cover_descendants(self):
        def nested(child):
            return (f'import sys\nsys.path.insert(0,{str(TOOLS)!r})\nfrom run_job import run_job\n'
                    f'run_job("inner",[sys.executable,"-c",{child!r}],{str(self.base / "inner-results")!r},'
                    f'root={str(self.root)!r},timeout=10,cpu_limit=1,rss_limit_gib=.5,log_limit_mib=.1)')
        result = self.run_python(nested('while True: pass'), cpu_limit=.3)
        self.assertEqual(result['stop_reason'], 'cpu-limit')
        self.assertLess(result['cpu_seconds'], 1.5)
        result = self.run_python(nested('import time;x=bytearray(150*1024*1024);time.sleep(5)'),
                                 rss_limit_gib=.09)
        self.assertEqual(result['stop_reason'], 'rss-threshold')
        self.assertGreater(result['peak_tree_rss_kib'], 90*1024)


if __name__ == '__main__':
    unittest.main()
