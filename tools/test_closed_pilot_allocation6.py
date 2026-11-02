import os
from pathlib import Path
import shutil
import tempfile
import unittest
from closed_pilot_allocation6 import candidate

class OriginalProtection(unittest.TestCase):
    def test_either_original_inode_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.write_bytes(b'accepted immutable bytes')
            shutil.copy2(a, b)
            self.assertTrue(candidate(a, b, set()))
            for p in (a, b):
                s = p.stat()
                self.assertFalse(candidate(a, b, {(s.st_dev, s.st_ino)}))
            os.link(b, Path(tmp) / 'c')
            self.assertFalse(candidate(b, a, set()))

    def test_metadata_difference_is_not_shared(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.write_bytes(b'bytes'); shutil.copy2(a, b)
            b.chmod(0o400)
            self.assertFalse(candidate(a, b, set()))
