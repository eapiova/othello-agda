"""Source/ownership guards; these tests never execute Agda."""
from pathlib import Path
import re
import tempfile
import unittest

from initial_global_direct6 import emit as emit_direct
from initial_global_named6 import emit as emit_named
from initial_global_narrow6 import emit, narrow_part
from lazy_sample_parts6 import emit as emit_samples
from test_initial_global_alignment6 import fixture, PREFIX


class GlobalNarrow(unittest.TestCase):
    def prepare(self, check, side):
        data = fixture()
        emit_samples(check, data, side=side, prefix=PREFIX)
        layout = emit_named(check, side=side, sample=data, sample_prefix=PREFIX,
                            route_batch=4, map_batch=4)
        return data, layout

    def test_exact_dependencies_preserved_and_no_checker_facts_added(self):
        for side in ('lower', 'upper'):
            with tempfile.TemporaryDirectory() as tmp:
                check = Path(tmp)
                data, layout = self.prepare(check, side)
                emit_direct(check, side=side, sample=data, sample_prefix=PREFIX,
                            named_layout=layout)
                old = {p: p.read_bytes() for p in check.rglob('*.agda')}
                result = emit(check, side=side, sample=data, sample_prefix=PREFIX,
                              named_layout=layout)
                for case in data['cases']:
                    j = case['part']
                    source = (check / f'src/Tests/InitialGlobalNarrow6/Part{j}.agda').read_text()
                    imported = {int(n) for line in source.splitlines() if ' using (' in line
                                for n in re.findall(r'stateAligned(\d+)', line)}
                    self.assertEqual(imported, set(case['dependencies']))
                    self.assertIn('partial = P.linked LookupStates LookupBodies demandAligned', source)
                    self.assertNotRegex(source, r'Routes\d+\.AlignedModel\.stateAligned')
                for shard in layout['shards']:
                    text = (check / ('src/Tests/InitialGlobalNarrow6/' + shard['target'] + '.agda')).read_text()
                    for j in shard['needed_parts']:
                        self.assertIn(f'stateAligned{j} = Checked.AlignedModel.stateAligned{j}', text)
                    self.assertNotIn('refl', text)
                original_root = (check / 'src/Tests/InitialGlobalDirect6/Root.agda').read_text()
                new_root = (check / 'src/Tests/InitialGlobalNarrow6/Root.agda').read_text()
                self.assertEqual(original_root.replace('Tests.InitialGlobalDirect6',
                                                       'Tests.InitialGlobalNarrow6'), new_root)
                self.assertTrue(all(p.read_bytes() == raw for p, raw in old.items()))
                self.assertFalse(result['generator_certifies_acceptance'])
                self.assertFalse(result['resource_benefit_measured'])
                self.assertFalse(result['initial_problem2_proved'])
                with self.assertRaises(ValueError):
                    emit(check, side=side, sample=data, sample_prefix=PREFIX, named_layout=layout)

    def test_route_ownership_mismatch_missing_import_and_donor_corruption(self):
        raw = b'import Tests.Checked.Routes0 as Routes0\nx = Routes0.AlignedModel.stateAligned2 G same\n'
        kwargs = dict(prefix='Tests.Narrow', named_prefix='Tests.Checked',
                      owners={2: 'Routes0'}, dependencies=[2])
        with self.assertRaises(ValueError):
            narrow_part(raw, **dict(kwargs, owners={2: 'Routes1'}))
        with self.assertRaises(ValueError):
            narrow_part(raw, **dict(kwargs, dependencies=[2, 3]))
        with self.assertRaises(ValueError):
            narrow_part(raw.split(b'\n', 1)[1], **kwargs)
        with tempfile.TemporaryDirectory() as tmp:
            check = Path(tmp)
            data, layout = self.prepare(check, 'lower')
            path = check / 'src/Tests/InitialGlobalNamed6/Model.agda'
            path.write_bytes(path.read_bytes() + b'\n-- changed\n')
            with self.assertRaises(ValueError):
                emit(check, side='lower', sample=data, sample_prefix=PREFIX, named_layout=layout)
            self.assertFalse((check / 'src/Tests/InitialGlobalNarrow6').exists())
