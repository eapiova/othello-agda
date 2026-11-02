"""The single approved experiment cannot lower gates for other jobs."""
import unittest
from closed_pilot_policy6 import FLAG, LABEL, RETRY_LABEL, NARROW_FLAG, NARROW_LABEL, MODULE_FLAG, MODULE_LABEL, MODULE_UPPER_LABEL, free_disk_gib, same_compiler_after_reboot


class ClosedPilotPolicy(unittest.TestCase):
    def command(self):
        return ['python3', 'tools/initial_direct_pilot6.py', '--side', 'lower',
                '--output', 'results/initial-lower-global-closed6', FLAG]

    def test_scoped_exception_and_unchanged_default(self):
        self.assertEqual(free_disk_gib(LABEL, self.command(), 290, 2.75), 80)
        self.assertEqual(free_disk_gib(RETRY_LABEL, self.command(), 280, 2.75), 80)
        self.assertEqual(free_disk_gib('other', ['python3', 'other.py'], 600, 3.5), 100)
        with self.assertRaises(ValueError):
            free_disk_gib(LABEL, self.command(), 30, 1, smoke=True)

    def test_rejects_wrong_job_command_caps_and_duplicate_flags(self):
        command = self.command()
        invalid = [('other', command, 290, 2.75), (LABEL, command, 291, 2.75),
                   (LABEL, command, 290, 3), (LABEL, command + [FLAG], 290, 2.75),
                   (LABEL, [*command[:3], 'upper', *command[4:]], 290, 2.75),
                   (LABEL, ['python3', 'other.py', *command[2:]], 290, 2.75)]
        for args in invalid:
            with self.subTest(args=args), self.assertRaises(ValueError):
                free_disk_gib(*args)

    def test_reboot_preserves_machine_binary_path_and_version_pins(self):
        old = dict(hostname='eapiova', boot_id='before', agda_path='/same/agda',
                   agda_sha256='a' * 64, agda_version='2.9.0 pinned build')
        now = dict(old, boot_id='after')
        self.assertTrue(same_compiler_after_reboot(old, now))
        for key in ('hostname', 'agda_path', 'agda_sha256', 'agda_version'):
            with self.subTest(key=key):
                self.assertFalse(same_compiler_after_reboot(old, dict(now, **{key: 'different'})))
        self.assertFalse(same_compiler_after_reboot(old, dict(now, boot_id='')))
        self.assertFalse(same_compiler_after_reboot(old, {k: v for k, v in now.items() if k != 'agda_sha256'}))

    def test_second_test_is_separately_scoped(self):
        command = self.command()
        command[command.index(FLAG)] = NARROW_FLAG
        command[command.index('--output') + 1] = 'results/initial-lower-global-narrow6'
        self.assertEqual(free_disk_gib(NARROW_LABEL, command, 280, 2.75), 80)
        for label, cmd in ((LABEL, command), (NARROW_LABEL, command + [FLAG]),
                           (NARROW_LABEL, command + [NARROW_FLAG]),
                           (NARROW_LABEL, self.command())):
            with self.subTest(label=label), self.assertRaises(ValueError):
                free_disk_gib(label, cmd, 280, 2.75)

    def test_module_import_resumption_is_separately_scoped(self):
        command = self.command()
        command[command.index(FLAG)] = MODULE_FLAG
        command[command.index('--output') + 1] = 'results/initial-lower-global-module6'
        self.assertEqual(free_disk_gib(MODULE_LABEL, command, 220, 2.75), 80)
        upper = list(command)
        upper[upper.index('--side') + 1] = 'upper'
        upper[upper.index('--output') + 1] = 'results/initial-upper-global-module6'
        self.assertEqual(free_disk_gib(MODULE_UPPER_LABEL, upper, 160, 2.75), 80)
        for label, cmd in ((NARROW_LABEL, command), (MODULE_LABEL, command + [FLAG]),
                           (MODULE_LABEL, command + [MODULE_FLAG]),
                           (MODULE_UPPER_LABEL, command), (MODULE_LABEL, upper)):
            with self.subTest(label=label), self.assertRaises(ValueError):
                free_disk_gib(label, cmd, 220, 2.75)

    def test_full_map_exception_is_bounded_and_does_not_change_other_jobs(self):
        from closed_pilot_policy6 import FULL_MAP_FLAG, FULL_MAP_PHASES, artifact_cap_gib
        for label, (phase, cpu, rss) in FULL_MAP_PHASES.items():
            cmd=['python3','tools/full_map_pilot6.py','--phase',phase,FULL_MAP_FLAG]
            self.assertEqual(free_disk_gib(label,cmd,cpu,rss),80)
            self.assertEqual(artifact_cap_gib(label,cmd,cpu,rss),12)
            for name,c,sec,mem in [(label,cmd,cpu+1,rss), (label,cmd,cpu,rss+.1),
                    ('other',cmd,cpu,rss), (label,cmd+[FULL_MAP_FLAG],cpu,rss),
                    (label,['python3','other.py',*cmd[2:]],cpu,rss)]:
                with self.subTest(label=name), self.assertRaises(ValueError):
                    free_disk_gib(name,c,sec,mem)
        self.assertEqual(artifact_cap_gib('other',['python3','other.py'],100,2),10)
