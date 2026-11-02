import gzip
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import compact_logs6
from compact_logs6 import archive


class WarningArchiveTests(unittest.TestCase):
    def test_exact_original_bytes_are_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'accepted.log';raw=b'repeated warning\n'*300
            path.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
            row=archive(path,digest)
            self.assertFalse(path.exists())
            packed=path.with_suffix('.log.gz').read_bytes()
            self.assertEqual(gzip.decompress(packed),raw)
            self.assertEqual(row['original_sha256'],digest)
            self.assertEqual(row['archive_sha256'],hashlib.sha256(packed).hexdigest())

    def test_mismatch_never_removes_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'accepted.log';path.write_bytes(b'changed')
            with self.assertRaises(ValueError):archive(path,'0'*64)
            self.assertEqual(path.read_bytes(),b'changed')
            self.assertFalse(path.with_suffix('.log.gz').exists())

    def test_completed_audit_uses_log_filenames_and_keeps_failed_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            previous=Path(directory)/'previous';previous.mkdir()
            records=previous/'records';records.mkdir()
            raw=b'accepted warning\n'*30
            (records/'good.log').write_bytes(raw)
            (records/'failed.log').write_bytes(b'failure evidence')
            final=dict(status='collector-failed',completed_groups=list(range(10)),
                       source_sha256='source')
            (previous/'final.json').write_text(json.dumps(final))
            audit=dict(final_sha256=compact_logs6.assembly6.sha(previous/'final.json'),
                       collector_interfaces={'proof.agdai':'unchanged'},
                       records={'good':{'accepted':True},'failed':{'accepted':False}},
                       log_hashes={'good.log':hashlib.sha256(raw).hexdigest()})
            (previous/'phase-records.json').write_text(json.dumps(audit))
            output=Path(directory)/'receipt.json'
            with patch.object(compact_logs6,'source_identity',return_value={'source_sha256':'source'}), \
                 patch.object(compact_logs6.assembly6,'interfaces',return_value=audit['collector_interfaces']):
                compact_logs6.run(SimpleNamespace(previous=previous,output=output))
            receipt=json.loads(output.read_text())
            self.assertEqual(len(receipt['records']),1)
            self.assertTrue(receipt['donor_interfaces_unchanged'])
            self.assertEqual(gzip.decompress((records/'good.log.gz').read_bytes()),raw)
            self.assertEqual((records/'failed.log').read_bytes(),b'failure evidence')

    def test_packed_checkpoint_uses_label_keys_without_changing_interfaces(self):
        with tempfile.TemporaryDirectory() as directory:
            previous=Path(directory)/'previous';previous.mkdir()
            records=previous/'records';records.mkdir()
            raw=b'accepted warning\n'*30
            (records/'good.log').write_bytes(raw)
            final=dict(status='artifact-budget-stopped',accepted=False,
                       completed_groups=list(range(6)),source_sha256='source',
                       phases=[{'accepted':True} for _ in range(173)])
            (previous/'packed.json').write_text(json.dumps(final))
            pool={f'proof{i}.agdai':'unchanged' for i in range(205)}
            audit=dict(final_interfaces=pool,records={'good':{'accepted':True}},
                       log_hashes={'good':hashlib.sha256(raw).hexdigest()})
            (previous/'phase-records.json').write_text(json.dumps(audit))
            output=Path(directory)/'receipt.json'
            with patch.object(compact_logs6,'source_identity',return_value={'source_sha256':'source'}), \
                 patch.object(compact_logs6.assembly6,'interfaces',return_value=pool):
                compact_logs6.run(SimpleNamespace(previous=previous,output=output))
            self.assertEqual(gzip.decompress((records/'good.log.gz').read_bytes()),raw)
            self.assertTrue(json.loads(output.read_text())['donor_interfaces_unchanged'])

    def test_continuation_archives_only_new_accepted_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            previous=Path(directory)/'continued';previous.mkdir()
            records=previous/'records';records.mkdir()
            raw=b'accepted continuation warning\n'*30
            phases=[dict(label=f'old{i}',accepted=True) for i in range(173)]
            phases += [dict(label=f'new{i}',accepted=True) for i in range(100)]
            phases.append(dict(label='collector',accepted=False))
            for i in range(100):(records/f'new{i}.log').write_bytes(raw)
            (records/'collector.log').write_bytes(b'heap failure evidence')
            final=dict(status='collector-failed',accepted=False,
                       completed_groups=list(range(10)),checked_sample_upper_roots=100,
                       source_sha256='source',resumed_from=str(Path(directory)/'prefix'),
                       prefix_sources_unchanged=True,prefix_interface_hashes_unchanged=True,
                       phases=phases)
            (previous/'packed.json').write_text(json.dumps(final))
            pool={f'proof{i}.agdai':'unchanged' for i in range(305)}
            audit=dict(final_interfaces=pool,
                       records={p['label']:{'accepted':p['accepted']} for p in phases},
                       log_hashes={f'new{i}':hashlib.sha256(raw).hexdigest() for i in range(100)})
            (previous/'phase-records.json').write_text(json.dumps(audit))
            output=Path(directory)/'receipt.json'
            with patch.object(compact_logs6,'source_identity',return_value={'source_sha256':'source'}), \
                 patch.object(compact_logs6.assembly6,'interfaces',return_value=pool):
                compact_logs6.run(SimpleNamespace(previous=previous,output=output))
            receipt=json.loads(output.read_text())
            self.assertEqual(len(receipt['records']),100)
            self.assertTrue(receipt['continuation_only'])
            self.assertEqual(gzip.decompress((records/'new99.log.gz').read_bytes()),raw)
            self.assertEqual((records/'collector.log').read_bytes(),b'heap failure evidence')
            self.assertFalse((records/'old0.log.gz').exists())


if __name__=='__main__':unittest.main()
