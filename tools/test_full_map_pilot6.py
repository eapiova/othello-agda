"""Fail-closed resource/provenance tests; no solve or Agda process is launched."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import full_map_pilot6 as pilot


class FullMapPilot(unittest.TestCase):
    def test_storage_is_allocated_total_and_preserves_floor(self):
        with patch.object(pilot.subprocess,'check_output',return_value=str(11*pilot.GIB)+'\t/runs'), \
             patch.object(pilot.shutil,'disk_usage') as usage:
            usage.return_value.free=90*pilot.GIB
            self.assertEqual(pilot.storage(Path('/runs/job'))['artifact_cap_bytes'],12*pilot.GIB)
            with self.assertRaises(ValueError):pilot.storage(Path('/runs/job'),pilot.GIB)
            usage.return_value.free=79*pilot.GIB
            with self.assertRaises(ValueError):pilot.storage(Path('/runs/job'))

    def test_export_is_explicitly_lower_and_bounded(self):
        cmd=pilot.native_command()
        for key,value in [('--direction','lower'),('--native-cpu','900'),('--wire-limit-mib','512'),
                          ('--max-entries','200'),('--max-tokens','32000')]:
            self.assertEqual(cmd[cmd.index(key)+1],value)
        self.assertIn('--counts-only',cmd)
        self.assertNotIn('--save-tt',cmd)

    def test_closed_phase_rejects_failed_or_changed_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'results/full-map-pilot6';out.mkdir(parents=True)
            receipt=dict(accepted=True,exit_code=0,stop_reason=None,source_unchanged=True,
                expected_source_matches=True,machine='eapiova',source_sha256='pinned')
            file=root/'results/phase.json'
            for change in [{},dict(accepted=False),dict(source_unchanged=False),dict(machine='other')]:
                file.write_text(json.dumps(dict(receipt,**change)))
                with patch.object(pilot,'source_identity',return_value=dict(source_sha256='pinned')):
                    if change:
                        with self.assertRaises(ValueError):pilot.closed_phase(out,'phase')
                    else:self.assertTrue(pilot.closed_phase(out,'phase')['accepted'])
            file.write_text(json.dumps(receipt))
            with patch.object(pilot,'source_identity',return_value=dict(source_sha256='changed')):
                with self.assertRaises(ValueError):pilot.closed_phase(out,'phase')
