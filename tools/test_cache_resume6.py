"""A compiler rewriting its cache must never change an accepted donor."""
from pathlib import Path
import tempfile
import unittest

from assembly6 import sha
from cache_resume6 import copy_interface, selected_interfaces


class CacheIsolationTests(unittest.TestCase):
    def test_destination_rewrite_does_not_change_donor(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);donor=root/'donor.agdai';dest=root/'cache/target.agdai'
            donor.write_bytes(b'accepted-interface');digest=sha(donor)
            copy_interface(donor,dest,digest)
            dest.write_bytes(b'recompiled-interface')
            self.assertEqual(donor.read_bytes(),b'accepted-interface')
            self.assertEqual(sha(donor),digest)
            with self.assertRaises(ValueError):copy_interface(donor,dest,digest)

    def test_changed_donor_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);donor=root/'donor.agdai';dest=root/'target.agdai'
            donor.write_bytes(b'accepted');digest=sha(donor);donor.write_bytes(b'changed')
            with self.assertRaises(ValueError):copy_interface(donor,dest,digest)
            self.assertFalse(dest.exists())

    def test_only_current_group_is_borrowed_until_collection(self):
        pool={'/Game/Core.agdai':'a','/Tests/Unattended6/Group0/Part0.agdai':'b',
              '/Tests/Unattended6/Group1/Part0.agdai':'c'}
        self.assertEqual(set(selected_interfaces(pool,0)),{'/Game/Core.agdai','/Tests/Unattended6/Group0/Part0.agdai'})
        self.assertEqual(selected_interfaces(pool),pool)


if __name__=='__main__':unittest.main()
