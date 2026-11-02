import unittest
from warning_assembly6 import negative_rejected
from warning_cost6 import predict


class WarningAssemblyGuards(unittest.TestCase):
    def test_actual_new_agda_unequal_terms_format_is_recognized(self):
        text='''file.agda:37.14-29: error: [UnequalTerms]
The terms
  true
and
  false
are not equal at type Bool
when checking that the expression refl {x = true} has type
checkShardBy keyed6 Fast.fastGame6 black (upperGoal 4)
upperTransport6 imports entries
≡ true
'''
        record=dict(accepted=False,exit_code=42,stop_reason=None)
        self.assertTrue(negative_rejected(record,[],[],text))
        self.assertFalse(negative_rejected(record,['changed.agdai'],[],text))
        self.assertFalse(negative_rejected(record,[],['unexpected.agdai'],text))
        self.assertFalse(negative_rejected(dict(record,stop_reason='cpu-limit'),[],[],text))
        self.assertFalse(negative_rejected(dict(record,accepted=True,exit_code=0),[],[],text))
        self.assertFalse(negative_rejected(record,[],[],text.replace('false','true')))
        self.assertFalse(negative_rejected(record,[],[],text.replace('checkShardBy','unrelated')))
        self.assertFalse(negative_rejected(record,[],[],'error: [NotInScope]'))

    def test_prediction_refuses_any_measured_heldout_part(self):
        report=dict(completed_groups=list(range(9)),phases=[dict(label='group9-part0')])
        with self.assertRaises(ValueError):predict({},report)


if __name__=='__main__':unittest.main()
