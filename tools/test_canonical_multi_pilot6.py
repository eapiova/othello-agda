import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import canonical_multi_pilot6 as multi


def fixture():
    spec=dict(scope=multi.SCOPE,cpu_max_seconds=600,hard_memory_gib=12,
        artifact_cap_gib=12,free_disk_gib=60,repeated_boolean_rows=800,
        new_distinct_game_rows=0,joint_owned_rows=1000,temporary_disk_floor_exception=True,
        one_heavy_job=True,native_search_allowed=False,production_authorized=False,
        parts=multi.PARTS,training=multi.TRAIN,held_out=multi.HELD,
        sample_sha256=multi.SAMPLE_SHA,full_manifest_sha256=multi.canonical.FULL_MANIFEST_SHA)
    raw=(json.dumps(spec,sort_keys=True)+'\n').encode()
    approval={k:v for k,v in spec.items() if k not in ('parts','training','held_out','sample_sha256','full_manifest_sha256')}
    approval.update(approved=True,answer=multi.ANSWER,plan_sha256=hashlib.sha256(raw).hexdigest(),question_item='new-human-question:0')
    return spec,raw,approval


class MultiPilotAdmission(unittest.TestCase):
    def test_exact_new_scope_required(self):
        spec,raw,a=fixture();self.assertEqual(multi.approved(raw,a),spec)
        changes=[dict(answer='Sì, solo il test con soglia 60 GiB'),
                 dict(scope=multi.canonical.SCOPE60),dict(repeated_boolean_rows=200),
                 dict(temporary_disk_floor_exception=False),dict(cpu_max_seconds=601),
                 dict(hard_memory_gib=13),dict(artifact_cap_gib=13),dict(free_disk_gib=80),
                 dict(native_search_allowed=True),dict(production_authorized=True),
                 dict(joint_owned_rows=800),dict(one_heavy_job=False),dict(question_item=''),
                 dict(approved=False),dict(plan_sha256='0'*64)]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ValueError):
                multi.approved(raw,{**a,**change})

    def test_even_rehashed_wrong_plan_refused(self):
        spec,raw,a=fixture()
        for change in [dict(parts=[380,17924,21836]),dict(held_out=[29329]),
                       dict(training=[380,17924,21836]),dict(sample_sha256='0'*64),
                       dict(full_manifest_sha256='0'*64),dict(free_disk_gib=80),
                       dict(repeated_boolean_rows=True),dict(native_search_allowed=0)]:
            s={**spec,**change};r=json.dumps(s).encode();b={**a,**change,'plan_sha256':hashlib.sha256(r).hexdigest()}
            with self.subTest(change=change),self.assertRaises(ValueError):multi.approved(r,b)

    def test_readonly_checker_layout_extra_roots_and_heap(self):
        base=['/usr/bin/bwrap','--ro-bind','/','/','--bind','/private','/private','--',
              '/agda','--no-libraries','-i','src','-i','/donor/src','--safe','--without-K',
              '--cubical-compatible','target.agda','+RTS','-M10G','-RTS']
        with patch.object(multi.canonical,'_command',return_value=list(base)) as called:
            result=multi.checker_command({},'X.Y','/private',dependencies=[Path('/new-rows'),Path('/old-proof')],heap='-M10G')
        called.assert_called_once_with({},'X.Y','/private',heap='-M10G')
        i=result.index('--')+1
        self.assertEqual(result[i:i+8],['/agda','--no-libraries','-i','src','-i','/new-rows/src','-i','/old-proof/src'])
        self.assertEqual(result[:i],base[:base.index('--')+1])
        for flag in ('--safe','--without-K','--cubical-compatible','-M10G'):self.assertIn(flag,result)

    def test_semantic_join_reuses_old_200_without_regeneration(self):
        layout={'layouts':[{'part':j,'rows':200,'row_layout':{'prefix':'Tests.R'+str(j)},
                            'bridge_layout':{'prefix':'Tests.B'+str(j)}} for j in multi.PARTS]}
        units=multi._units(layout)
        self.assertEqual([u['part'] for u in units],multi.PARTS+[34176])
        self.assertEqual(sum(u['rows'] for u in units),1000)
        self.assertEqual(units[-1]['row_prefix'],multi.canonical.ROW_PREFIX)
        self.assertEqual(units[-1]['bridge_prefix'],multi.canonical.BRIDGE_PREFIX)
        self.assertNotIn(34176,multi.PARTS)


if __name__=='__main__':unittest.main()
