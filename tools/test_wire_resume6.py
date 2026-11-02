"""Small filesystem fixtures; no Agda, systemd service, SSH or study ledger."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import assembly6
from provenance import digest_entries, source_files, source_identity
import wire_resume6 as resume


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def freeze(root):
    entries = {n: hashlib.sha256(raw).hexdigest() for n, raw in source_files(root)}
    (root/'SNAPSHOT.json').write_text(json.dumps(dict(files=entries,
        source_sha256=digest_entries(entries), git=dict(revision='fixture', dirty=False))))
    return source_identity(root)


class Fixture:
    def __init__(self, directory):
        self.study = Path(directory)/'runs'; self.previous = self.study/'previous'
        self.root = self.previous/'results/checked/check'
        self.prepared = self.previous/'results/prepared'
        self.donor = self.study/'generic/check'
        self.machine = dict(hostname='fixture-desktop', boot_id='old-boot',
            agda_path='/fixture/agda', agda_sha256='a'*64, agda_version='Agda fixture')
        write(self.previous/'tools/original.py', b'original outer source\n')
        self.outer_identity = freeze(self.previous)
        write(self.donor/'src/Generic.agda', b'module Generic where\n')
        self.donor_identity = freeze(self.donor)
        self.generic_name = '_build/2.9.0/agda/src/Generic.agdai'
        write(self.donor/self.generic_name, b'generic interface')
        write(self.root/'src/Generic.agda', b'module Generic where\n')
        self.targets, hashes = [], {}
        for index in range(4):
            name = f'src/Tests/WirePilot6/Lower/Part{index}.agda' if index < 3 else 'src/Tests/WirePilot6/Lower/Check.agda'
            raw = ('module ' + name.removeprefix('src/').removesuffix('.agda').replace('/', '.') + ' where\n').encode()
            write(self.prepared/name, raw); write(self.root/name, raw)
            hashes[name] = hashlib.sha256(raw).hexdigest()
            target = dict(path=name, kind='part' if index < 3 else 'assembly',
                root_index=0, source_bytes=len(raw), transitive_parts=min(index, 3),
                transitive_entries=min(index, 3))
            if index < 3:
                target.update(part=index, entries=1, tokens=1, compact_bytes=1,
                    dependencies=list(range(index)), imported_citations=index)
            self.targets.append(target)
        self.identity = freeze(self.root)
        self.plan = dict(format=resume.WIRE, roots=[dict(entries=3, checked_tokens=3)],
            targets=self.targets, generated_hashes=hashes, max_entries=1, max_tokens=1,
            total_generated_source_bytes=sum(t['source_bytes'] for t in self.targets))
        (self.prepared/'plan.json').write_text(json.dumps(self.plan))
        write(self.root/self.generic_name, b'generic interface')
        self.generic = assembly6.interfaces(self.donor)
        self.report = dict(format=resume.WIRE, phase='training', status='checking', accepted=False,
            check_root=str(self.root), source_sha256=self.identity['source_sha256'], machine=self.machine,
            donor_source=self.donor_identity, plan_sha256=assembly6.sha(self.prepared/'plan.json'),
            borrowed_interfaces_sha256=digest_entries(self.generic), phases=[], cpu_seconds=2.,
            initial_theorem_proved=False, production_authorized=False)
        for target in self.targets[:2]:
            before = assembly6.interfaces(self.root)
            record = self.record(target, before, self.root)
            write(self.root/self.own_name(target), ('accepted ' + target['path']).encode())
            self.report['phases'].append(dict(target=target, record=record, changed_imports=[]))
        self.pool = assembly6.interfaces(self.root)
        self.receipt_path = self.previous/'results/outer.json'
        self.report_path = self.previous/'results/checked/report.json'
        self.receipt = dict(format='othello-job-v2', label='fixture', remote_unit='othello6-fixture.service',
            root=str(self.previous), machine=self.machine['hostname'], source_sha256=self.outer_identity['source_sha256'],
            expected_source_sha256=self.outer_identity['source_sha256'], accepted=False, exit_code=1,
            stop_reason=None, finished_utc='closed', source_unchanged=True, expected_source_matches=True,
            cpu_seconds=3.)
        self.save()
        self.args = SimpleNamespace(previous_root=self.previous, previous_receipt=self.receipt_path,
            previous_report=self.report_path, prepared=self.prepared, donor=self.donor,
            study_root=self.study, output=self.study/'new/results/resume', agda='/fixture/agda',
            expected_hostname=self.machine['hostname'], expected_agda_sha256=self.machine['agda_sha256'],
            expected_previous_receipt_sha256=assembly6.sha(self.receipt_path),
            expected_previous_report_sha256=assembly6.sha(self.report_path),
            expected_previous_source_sha256=self.outer_identity['source_sha256'],
            expected_check_source_sha256=self.identity['source_sha256'],
            expected_plan_sha256=assembly6.sha(self.prepared/'plan.json'),
            expected_donor_source_sha256=self.donor_identity['source_sha256'],
            expected_generic_interfaces_sha256=digest_entries(self.generic),
            expected_prefix_interfaces_sha256=digest_entries(self.pool),
            expected_prefix_parts=2, expected_targets=4,
            kernel_cpu_budget=20., part_cpu_limit=5., assembly_cpu_limit=5.)

    def save(self):
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        self.receipt_path.write_text(json.dumps(self.receipt))
        self.report_path.write_text(json.dumps(self.report))

    def own_name(self, target):
        return '_build/2.9.0/agda/' + target['path'].removesuffix('.agda') + '.agdai'

    def record(self, target, before, root, machine=None):
        machine = machine or self.machine
        return dict(format='othello-job-v2', label=f"root0-part{target['part']}" if target['kind'] == 'part' else 'root0-assembly',
            machine=machine, root=str(root), accepted=True, exit_code=0, stop_reason=None,
            own_target_cold=True, source_unchanged=True, expected_source_matches=True,
            source_sha256=self.identity['source_sha256'], expected_source_sha256=self.identity['source_sha256'],
            executable_sha256=machine['agda_sha256'], argv=resume.command(machine, target),
            borrowed_interfaces_sha256=digest_entries(before), cpu_seconds=1., peak_rss_gib=.1,
            cpu_limit_seconds=5., rss_stop_threshold_gib=3. if target['kind'] == 'assembly' else 1.5,
            interfaces_before=len(before), interfaces_after=len(before)+1,
            cache_state=dict(interfaces_before=len(before), interfaces_after=len(before)+1), **target)

    def audit(self, report=None, pool=None, expected_parts=2, pool_hash=None):
        pool = self.pool if pool is None else pool
        return resume.audit_prefix(self.plan, report or self.report, self.generic, pool,
            machine=self.machine, source_hash=self.identity['source_sha256'], root=self.root,
            expected_parts=expected_parts, expected_targets=4,
            expected_pool_hash=pool_hash or digest_entries(pool))


class PrefixAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.f = Fixture(self.directory.name)

    def test_consecutive_prefix_authenticated_by_successor_and_final_pool(self):
        targets, own = self.f.audit()
        self.assertEqual(targets, self.f.targets)
        self.assertEqual(len(own), 2)
        tampered = dict(self.f.pool); tampered[self.f.own_name(self.f.targets[0])] = 'b'*64
        with self.assertRaisesRegex(ValueError, 'cache mismatch'):
            self.f.audit(pool=tampered)
        with self.assertRaisesRegex(ValueError, 'pool changed'):
            self.f.audit(pool_hash='c'*64)

    def test_failed_or_reordered_or_incomplete_prefix_is_rejected(self):
        for mutation in ('failed', 'changed-import', 'reordered', 'incomplete', 'warm'):
            report = copy.deepcopy(self.f.report)
            if mutation == 'failed': report['phases'][-1]['record']['accepted'] = False
            if mutation == 'changed-import': report['phases'][-1]['changed_imports'] = ['Generic']
            if mutation == 'reordered': report['phases'].reverse()
            if mutation == 'incomplete': report['phases'].pop()
            if mutation == 'warm': report['phases'][-1]['record']['own_target_cold'] = False
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.f.audit(report=report)

    def test_source_compiler_flags_and_cache_mismatch_rejected(self):
        for key, value in (('source_sha256', 'b'*64), ('executable_sha256', 'b'*64),
                           ('argv', ['/fixture/agda', '--safe']), ('borrowed_interfaces_sha256', 'b'*64)):
            report = copy.deepcopy(self.f.report); report['phases'][0]['record'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.f.audit(report=report)

    def test_unsupported_extra_and_failed_target_interfaces_rejected(self):
        for name in ('_build/Extra.agdai', self.f.own_name(self.f.targets[2])):
            extra = dict(self.f.pool); extra[name] = 'f'*64
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'unsupported extra'):
                self.f.audit(pool=extra)

    def test_duplicate_target_plan_rejected(self):
        self.f.plan['targets'][1] = self.f.plan['targets'][0]
        with self.assertRaises(ValueError): self.f.audit()


class CopyTests(unittest.TestCase):
    def test_copy2_bytes_mtime_and_private_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); donor = root/'donor'; dest = root/'cache/copied'
            donor.write_bytes(b'unchanged source'); os.utime(donor, ns=(123456789000, 987654321000))
            donor.chmod(0o444)
            with patch.object(resume.shutil, 'copy2', wraps=resume.shutil.copy2) as copier:
                resume.copy_private(donor, dest, assembly6.sha(donor), writable=True)
            copier.assert_called_once_with(donor, dest)
            self.assertEqual(dest.stat().st_mtime_ns, donor.stat().st_mtime_ns)
            self.assertNotEqual(dest.stat().st_ino, donor.stat().st_ino)
            self.assertTrue(dest.stat().st_mode & 0o200)
            dest.write_bytes(b'private rewrite'); self.assertEqual(donor.read_bytes(), b'unchanged source')

    def test_bad_digest_existing_destination_or_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); donor = root/'donor'; dest = root/'copy'
            donor.write_bytes(b'source')
            with self.assertRaises(ValueError): resume.copy_private(donor, dest, 'a'*64)
            self.assertFalse(dest.exists())
            dest.write_bytes(b'existing')
            with self.assertRaises(ValueError): resume.copy_private(donor, dest, assembly6.sha(donor))
            link = root/'link'; link.symlink_to(donor)
            with self.assertRaises(ValueError): resume.copy_private(link, root/'else', assembly6.sha(donor))


class ServiceTests(unittest.TestCase):
    def test_requires_closed_service_and_matching_exit(self):
        receipt = dict(label='fixture', remote_unit='othello6-fixture.service', exit_code=1)
        good = 'LoadState=loaded\nActiveState=failed\nSubState=failed\nMainPID=0\nControlPID=0\nExecMainStatus=1\n'
        for text, valid in ((good, True), (good.replace('MainPID=0', 'MainPID=42'), False),
                            (good.replace('ExecMainStatus=1', 'ExecMainStatus=0'), False),
                            (good.replace('ActiveState=failed', 'ActiveState=active'), False)):
            with self.subTest(text=text), patch.object(resume.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=text)):
                if valid: self.assertEqual(resume.closed_service(receipt)['MainPID'], '0')
                else:
                    with self.assertRaises(ValueError): resume.closed_service(receipt)


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.f = Fixture(self.directory.name)
        self.current_machine = dict(self.f.machine, boot_id='new-boot')
        self.calls = []
        for patcher in (patch.object(resume.socket, 'gethostname', return_value=self.f.machine['hostname']),
                        patch.object(resume.assembly6, 'machine_identity', return_value=self.current_machine),
                        patch.object(resume, 'closed_service', return_value={'MainPID': '0'}),
                        patch.object(resume, 'storage_gate', return_value={'fixture': True}),
                        patch.object(resume, 'run_job', side_effect=self.fake_job)):
            patcher.start(); self.addCleanup(patcher.stop)

    def fake_job(self, label, command, output, *, root, metadata, **kwargs):
        target = next(t for t in self.f.targets if t['path'] in command)
        self.calls.append(target['path'])
        before = assembly6.interfaces(root)
        self.assertNotIn(self.f.own_name(target), before)
        self.assertEqual(metadata['borrowed_interfaces_sha256'], digest_entries(before))
        write(root/self.f.own_name(target), ('new checked ' + target['path']).encode())
        return self.f.record(target, before, root, self.current_machine)

    def test_remaining_only_copy2_and_new_cpu_separate(self):
        old_sources = resume.file_state(self.f.root); old_pool = resume.pool_state(self.f.root)
        self.assertTrue(resume.run(self.f.args))
        report = json.loads((self.f.args.output/'report.json').read_text())
        self.assertEqual(self.calls, [t['path'] for t in self.f.targets[2:]])
        self.assertEqual(len(self.calls), len(set(self.calls)))
        self.assertEqual(report['completed_targets'], 4)
        self.assertEqual(report['new_kernel_cpu_seconds'], 2.)
        self.assertEqual(report['reused_kernel_cpu_seconds'], 2.)
        self.assertEqual(report['previous_outer_cpu_seconds'], 3.)
        self.assertFalse(report['initial_problem2_proved'])
        self.assertEqual(resume.file_state(self.f.root), old_sources)
        self.assertEqual(resume.pool_state(self.f.root), old_pool)
        fresh = self.f.args.output/'check'
        for name, item in old_sources.items():
            self.assertEqual((fresh/name).stat().st_mtime_ns, item['mtime_ns'])
            self.assertNotEqual((fresh/name).stat().st_ino, (self.f.root/name).stat().st_ino)

    def test_failure_stops_before_assembly_and_persists(self):
        with patch.object(resume, 'run_job', return_value=dict(accepted=False, cpu_seconds=.25)):
            self.assertFalse(resume.run(self.f.args))
        report = json.loads((self.f.args.output/'report.json').read_text())
        self.assertEqual(report['status'], 'check-failed')
        self.assertEqual(len(report['new_phases']), 1)
        self.assertEqual(report['completed_targets'], 2)
        self.assertEqual(report['new_kernel_cpu_seconds'], .25)
        self.assertTrue(report['previous_interfaces_unchanged'])

    def test_gate_before_each_remaining_target(self):
        with patch.object(resume, 'storage_gate', side_effect=[{}, {}, ValueError('storage gate reached')]) as gate:
            self.assertFalse(resume.run(self.f.args))
        self.assertEqual(gate.call_count, 3)
        self.assertEqual(self.calls, [self.f.targets[2]['path']])
        report = json.loads((self.f.args.output/'report.json').read_text())
        self.assertEqual(report['completed_targets'], 3)
        self.assertEqual(report['status'], 'driver-failed')

    def test_mismatched_source_compiler_and_pin_stop_before_copy(self):
        for field in ('expected_agda_sha256', 'expected_check_source_sha256', 'expected_previous_report_sha256',
                      'expected_generic_interfaces_sha256', 'expected_prefix_interfaces_sha256'):
            args = copy.copy(self.f.args); setattr(args, field, 'b'*64)
            with self.subTest(field=field), self.assertRaises(ValueError): resume.run(args)
            self.assertFalse(args.output.exists())
        self.assertEqual(self.calls, [])

    def test_cross_machine_is_rejected(self):
        with patch.object(resume.socket, 'gethostname', return_value='other-desktop'):
            with self.assertRaisesRegex(ValueError, 'cross-machine'): resume.run(self.f.args)


if __name__ == '__main__':
    unittest.main()
