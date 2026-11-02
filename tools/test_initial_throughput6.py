"""Fail-closed import closure for bounded private throughput workers."""
from pathlib import Path
import tempfile
import unittest

from initial_throughput6 import closure


class ClosureTests(unittest.TestCase):
    def source(self, root, module, text):
        p = root / 'src' / (module.replace('.', '/') + '.agda')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def test_transitive_cycles_and_unrelated_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.source(root, 'Tests.Slice', 'open import Prelude\nimport Tests.Data as D\n')
            self.source(root, 'Prelude', 'open import Agda.Builtin.Nat\nimport Agda.Primitive\n')
            self.source(root, 'Tests.Data', 'import Prelude\nimport Tests.Slice\n')
            self.source(root, 'Tests.Unrelated', 'import Tests.Missing\n')
            self.assertEqual(closure(root, 'Tests.Slice'), {'src/Tests/Slice.agda',
                'src/Prelude.agda', 'src/Tests/Data.agda', 'othello.agda-lib'})

    def test_missing_symlink_shadowed_builtin_and_invalid_target(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = self.source(root, 'Tests.Slice', 'import Tests.Missing\n')
            with self.assertRaises(ValueError): closure(root, 'Tests.Slice')
            target.write_text('import Agda.Builtin.Nat\n')
            self.source(root, 'Agda.Builtin.Nat', '')
            with self.assertRaises(ValueError): closure(root, 'Tests.Slice')
            target.write_text('import Tests.Alias\n')
            (target.parent / 'Alias.agda').symlink_to(target)
            with self.assertRaises(ValueError): closure(root, 'Tests.Slice')
            with self.assertRaises(ValueError): closure(root, '../Slice')


if __name__ == '__main__': unittest.main()
