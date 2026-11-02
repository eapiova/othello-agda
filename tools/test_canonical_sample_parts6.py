"""Canonical name sharing must preserve every state and every row assertion."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from canonical_sample_parts6 import emit_canonical
from lazy_sample_parts6 import emit
from new_row_bridge6 import emit as emit_bridge
from test_new_row_bridge6 import fixture


class CanonicalSamples(unittest.TestCase):
    def sample(self):
        full, sample = fixture()
        # The original fixture selects only its final row and its one citation.
        sample['states'] = {j: s for j, s in sample['states'].items()}
        return full, sample

    def test_only_state_definitions_change_and_hash_manifest_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            full, sample = self.sample()
            before = copy.deepcopy((full, sample))
            plain = emit(root/'plain', sample, side='lower', prefix='Tests.CanonicalFixture')
            shared = emit_canonical(root/'shared', sample, full, prefix='Tests.CanonicalFixture')
            self.assertEqual((full, sample), before)
            self.assertFalse(shared['agda_checked'])
            self.assertFalse(shared['initial_problem2_proved'])
            self.assertFalse(shared['production_authorized'])
            self.assertEqual(set(shared['generated_sha256']), {
                n for n in plain['generated_sha256'] if '/StateData' not in n})
            self.assertEqual(shared['emitted_state_chunks'], 0)
            self.assertEqual(shared['reused_state_modules'], 2)
            for name, digest in shared['generated_sha256'].items():
                raw = (root/'shared'/name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                restored=raw
                for j in (1,2):
                    restored=restored.replace(('import Tests.FixtureFull.StateData'+str(j)+' as S').encode(),
                        ('import Tests.CanonicalFixture.StateData'+str(j)+' as S').encode())
                self.assertEqual(restored, (root/'plain'/name).read_bytes())
            self.assertEqual(shared['canonical_state_exports'], {1:'Tests.FixtureFull.StateData1',2:'Tests.FixtureFull.StateData2'})
            bridge=emit_bridge(root/'results/bridge',full,sample,part=2,row_prefix='Tests.CanonicalFixture',
                prefix='Tests.CanonicalBridgeFixture',state_exports=shared['canonical_state_exports'])
            batch=(root/'results/bridge/src/Tests/CanonicalBridgeFixture/Batch0.agda').read_text()
            self.assertIn('import Tests.FixtureFull.StateData1 as S1',batch)
            self.assertNotIn('import Tests.CanonicalFixture.StateData',batch)
            self.assertEqual(bridge['new_boolean_rows'],0)

    def test_wrong_hash_epoch_count_module_and_existing_cache_are_refused(self):
        changes = [lambda f,s:f.update(complete=False), lambda f,s:f.update(wire_sha256='b'*64),
                   lambda f,s:f['chunks'][1].update(text_sha256='0'*64),
                   lambda f,s:f['chunks'][1].update(rows=199),
                   lambda f,s:f['chunks'][1].update(module='Bad; import Other'),
                   lambda f,s:f['chunks'][1].update(module='Tests.CanonicalFixture.StateData1')]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                full, sample = self.sample();change(full,sample)
                target = Path(tmp)/'check'
                with self.assertRaises((ValueError,KeyError)):
                    emit_canonical(target,sample,full,prefix='Tests.CanonicalFixture')
                self.assertFalse(target.exists())
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'accepted';target.mkdir()
            cache = target/'Part.agdai';cache.write_bytes(b'accepted cache')
            full,sample=self.sample()
            with self.assertRaises(ValueError):emit_canonical(target,sample,full)
            self.assertEqual(cache.read_bytes(),b'accepted cache')

if __name__ == '__main__':
    unittest.main()
