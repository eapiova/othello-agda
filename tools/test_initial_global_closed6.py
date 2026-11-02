"""Source-integrity checks only; these never establish Agda acceptance."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from initial_global_closed6 import emit, specialize
from initial_global_direct6 import emit as emit_direct
from initial_global_named6 import emit as emit_named
from lazy_sample_parts6 import emit as emit_samples
from test_initial_global_alignment6 import fixture, PREFIX


class GlobalClosed(unittest.TestCase):
    def prepare(self, check, side='lower'):
        data = fixture()
        emit_samples(check, data, side=side, prefix=PREFIX)
        layout = emit_named(check, side=side, sample=data, sample_prefix=PREFIX)
        return data, layout

    def test_specialization_reuses_exact_maps_checker_facts_and_joins(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data, layout = self.prepare(check, side)
                emit_direct(check, side=side, sample=data, sample_prefix=PREFIX,
                            named_layout=layout)
                accepted = {p: p.read_bytes() for p in check.rglob('*.agda')}
                result = emit(check, side=side, sample=data, sample_prefix=PREFIX,
                              named_layout=layout)
                self.assertEqual(result['targets'], ['Lookup', *layout['targets'][-17:]])
                self.assertEqual(result['owned_parts'], layout['owned_parts'])
                self.assertEqual(result['needed_parts'], layout['needed_parts'])
                for target in result['targets']:
                    p = check / 'src/Tests/InitialGlobalClosed6' / (target + '.agda')
                    source = p.read_text()
                    self.assertIn('--safe --without-K --cubical-compatible', source)
                    self.assertNotIn('module AlignedModel', source)
                    self.assertNotIn('postulate', source)
                    self.assertNotIn('accepted = refl', source)
                    if target.startswith('Part'):
                        self.assertIn('partial = P.linked G C demandAligned', source)
                        self.assertIn('Lookup.stateCompatible', source)
                        self.assertIn('Lookup.bodyCompatible', source)
                        original = (check / 'src/Tests/InitialGlobalDirect6' /
                                    (target + '.agda')).read_text()
                        # The original route declaration and its complete proof are unchanged.
                        route = original.split('bodyRoute :')[1].split('module AlignedModel')[0]
                        self.assertIn('bodyRoute :' + route, source)
                    if target == 'Root':
                        self.assertEqual(source.count('.partial'), 16)
                        self.assertEqual(source.count('Family.A.join'), 15)
                        self.assertIn('partial : Family.A.Partial G C ownedStates', source)
                self.assertTrue(all(p.read_bytes() == raw for p, raw in accepted.items()))
                for relative, h in result['generated_sha256'].items():
                    self.assertEqual(hashlib.sha256((check / relative).read_bytes()).hexdigest(), h)
                for flag in ('agda_acceptance_measured', 'resource_benefit_measured',
                             'initial_problem2_proved', 'optimal_initial_pair_proved',
                             'production_authorized'):
                    self.assertIs(result[flag], False)

    def test_rejects_donor_corruption_existing_outputs_and_bad_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            data, layout = self.prepare(check)
            kwargs = dict(side='lower', sample=data, sample_prefix=PREFIX,
                          named_layout=layout)
            p = check / 'src/Tests/InitialGlobalNamed6/Model.agda'
            original = p.read_bytes()
            p.write_bytes(original + b'\n-- changed\n')
            with self.assertRaises(ValueError):
                emit(check, **kwargs)
            self.assertFalse((check / 'src/Tests/InitialGlobalClosed6').exists())
            p.write_bytes(original)
            emit(check, **kwargs)
            with self.assertRaises(ValueError):
                emit(check, **kwargs)
            for raw in (b'', b'module Unexpected where\n'):
                with self.assertRaises(ValueError):
                    specialize(raw, prefix='Tests.Unexpected', target='Root')
