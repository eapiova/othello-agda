#!/usr/bin/env python3
"""A stopped or changed preparation cannot launch dependent proof checks."""
import unittest
from unattended_wire6 import closed_record
from unattended_wire_advance6 import predecessor, accepted_advance


class ClosedPreparationTests(unittest.TestCase):
    def test_only_complete_unchanged_preparation_can_continue(self):
        accepted=dict(accepted=True,source_unchanged=True,expected_source_matches=True,
            source_sha256='frozen',stop_reason=None,exit_code=0)
        closed_record(accepted,'frozen')
        for field,value in [('accepted',False),('source_unchanged',False),('expected_source_matches',False),
                ('source_sha256','changed'),('stop_reason','cpu'),('exit_code',1)]:
            with self.assertRaises(ValueError):closed_record(dict(accepted,**{field:value}),'frozen')

    def test_advance_requires_all_exact_accepted_predecessor_stages(self):
        record=dict(accepted=True,source_unchanged=True,expected_source_matches=True,
            source_sha256='frozen',stop_reason=None,exit_code=0)
        labels=['upper-heldout','lower-ply16','upper-ply16','lower-ply14','upper-ply14']
        report=dict(status='complete-pilot',accepted=True,initial_problem2_proved=False,
            phases=[dict(label=label,accepted=True) for label in labels])
        predecessor(record,report,'frozen','report','report')
        for change in ({'accepted':False},{'status':'checking'}, {'phases':report['phases'][:-1]},
                       {'initial_problem2_proved':True}):
            with self.assertRaises(ValueError):predecessor(record,dict(report,**change),'frozen','report','report')
        with self.assertRaises(ValueError):predecessor(record,report,'frozen','changed','report')

    def test_cut_pilot_requires_both_exact_accepted_earlier_bounds(self):
        record=dict(accepted=True,source_unchanged=True,expected_source_matches=True,
            source_sha256='frozen',stop_reason=None,exit_code=0)
        report=dict(format='othello-unattended-wire-advance6-v1', status='complete-earlier-roots',
            accepted=True,line_ply=12,initial_problem2_proved=False,production_authorized=False,
            phases=[dict(label=d+'-ply12',accepted=True) for d in ('lower','upper')])
        accepted_advance(record,report,'frozen','report','report')
        for change in ({'accepted':False},{'line_ply':10},{'production_authorized':True},
                       {'phases':report['phases'][:-1]}, {'initial_problem2_proved':True}):
            with self.assertRaises(ValueError):
                accepted_advance(record,dict(report,**change),'frozen','report','report')
        with self.assertRaises(ValueError):
            accepted_advance(record,report,'frozen','changed','report')


if __name__=='__main__':unittest.main()
