from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from readonly_dependencies6 import command, namespace_view, NAMESPACE_LAUNCHER
from initial_shards_resume6 import argv

class BorrowedDependencies(unittest.TestCase):
    def test_only_private_check_root_is_writable(self):
        with tempfile.TemporaryDirectory() as tmp, patch('readonly_dependencies6.shutil.which',return_value='/usr/bin/bwrap'):
            root=Path(tmp);check=root/'check';donor=root/'donor';check.mkdir();donor.mkdir()
            machine=dict(agda_path='/pinned/agda');target='Tests.New.Part0'
            actual=command(machine,target,check,donor)
            self.assertEqual(actual[1:8],['--ro-bind','/','/','--bind',str(check),str(check),'--proc'])
            inner=actual[actual.index('--')+1:];baseline=argv(machine,target);baseline[4:4]=['-i',str(donor/'src')]
            self.assertEqual(inner,baseline)
            self.assertIn('--safe',inner);self.assertIn('--save-metas',inner)
            self.assertEqual(actual.count('--bind'),1)
            with self.assertRaises(ValueError):command(machine,target,donor,donor)
            with self.assertRaises(ValueError):command(machine,target,donor/'child',donor)

    def test_missing_sandbox_fails_closed(self):
        with patch('readonly_dependencies6.shutil.which',return_value=None),self.assertRaises(ValueError):
            command(dict(agda_path='/agda'),'Tests.New','/a','/b')

    def test_namespace_view_keeps_original_paths_and_rejects_unsafe_masks(self):
        with tempfile.TemporaryDirectory() as tmp, patch('readonly_dependencies6.shutil.which',return_value='/usr/bin/bwrap'):
            root=Path(tmp);check=root/'check';donor=root/'donor';other=root/'upper'
            check.mkdir();donor.mkdir();source=other/'src';ns=source/'Tests/Upper';ns.mkdir(parents=True)
            original=command(dict(agda_path='/pinned/agda'),'Tests.Joint',check,donor)
            original[original.index('--')+5:original.index('--')+5]=['-i',str(source)]
            import json
            result=namespace_view(original,source,['Tests.Upper'])
            self.assertEqual(result[:3],['python3','-c',NAMESPACE_LAUNCHER])
            self.assertEqual(json.loads(result[3]),original)
            self.assertEqual(json.loads(result[5]),[str(ns)])
            self.assertEqual(result[4],str(source))
            for bad in ([],['Prelude'],['Tests.Upper','Tests.Upper'],['Tests.Upper.Child'],['Tests.Missing'],['Tests...']):
                with self.subTest(prefixes=bad),self.assertRaises(ValueError):
                    namespace_view(original,source,bad)
            with self.assertRaises(ValueError):namespace_view(original,check/'src',['Tests.Upper'])
            with self.assertRaises(ValueError):namespace_view(original,source.parent,['Tests.Upper'])
            ns.rmdir();ns.symlink_to(donor,target_is_directory=True)
            with self.assertRaises(ValueError):namespace_view(original,source,['Tests.Upper'])
