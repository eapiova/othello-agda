"""The screen must reject incomplete populations and never grant production GO."""
import copy
import unittest

import initial_layout_gate6 as gate


def fixture():
    counts = dict(direction='lower',threshold=4,frontier_discs=36,complete=True,
        root_validated=True,root_holds=True,wire_complete=True,layout_complete=True,
        layout_counts_only=True,count_overflow=False,oracle_aborted=False,layout_censored=False,
        layout_tokens=100000,layout_records=2000,layout_imported_citations_sum=100,
        layout_transitive_entries_sum=8000,layout_parts=10,layout_max_entries=200,
        wire_records=2000,wire_tokens=100000,wire_bytes=12345,layout_source_wire_bytes=12345,
        layout_transitive_parts_sum=40,layout_direct_dependencies_sum=20,
        layout_assembly_transitive_parts=10,layout_assembly_transitive_entries=2000,
        layout_peak_bytes=100,layout_limit_bytes=512*2**20,layout_compact_bytes=10000)
    native = dict(format='othello-wire-layout6-run-v1',status='complete-untrusted-layout',
        root_key='initial',counts_only=True,native_complete=True,layout_complete=True,
        layout_counts_censored=False,exit_code=0,donor_unchanged=True,table_unchanged=True,
        incomplete_count_extrapolated=False,initial_problem2_proved=False,
        optimal_pair_proved=False,production_authorized=False,
        request=dict(position='initial',turn='black',direction='lower',threshold=4,**{'frontier-discs':36}),
        build=dict(pins={'lower':[1]},line_sha256='a'*64,solver_rules_tt_bytes_unchanged=True),counts=counts)
    model = dict(feature_names=gate.FEATURES,coefficients=[1.,2.,3.,4.,5.])
    calibration = dict(format='othello-wire-workflow6-v1',accepted_pilot_audit=True,
        production_authorized=False,line_sha256='a'*64,models=dict(lower=model,upper=model))
    driver = dict(format='othello-unattended-layout6-v1',initial_problem2_proved=False,
        optimal_pair_proved=False,production_authorized=False,
        phases=[dict(label='initial-lower',accepted=True,layout_complete=True,
        record=dict(accepted=True,exit_code=0,stop_reason=None,counts_only=True,proof_premise=False,
                    source_unchanged=True,expected_source_matches=True))])
    return calibration,native,driver


class GateTests(unittest.TestCase):
    def test_all_five_features_and_no_go_even_for_small_success(self):
        calibration,native,driver = fixture()
        result = gate.evaluate(calibration,dict(lower=native),driver)
        self.assertAlmostEqual(result['nominal_measured_direction_part_cpu_hours'],(100+4+.3+32+50)/3600)
        self.assertFalse(result['production_authorized'])
        self.assertFalse(result['full_both_bounds_measured'])
        self.assertEqual(result['components'][0]['direct_data_only_scenario_entry_upper_count'],4000)

    def test_censored_counts_wrong_root_or_line_are_rejected(self):
        for key,value in [('layout_complete',False),('native_complete',False),
                          ('layout_counts_censored',True),('root_key','descendant')]:
            calibration,native,driver = fixture(); native[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                gate.evaluate(calibration,dict(lower=native),driver)
        calibration,native,driver = fixture();native['build']['line_sha256']='b'*64
        with self.assertRaises(ValueError):gate.evaluate(calibration,dict(lower=native),driver)

    def test_failed_measurement_and_impossible_closure_are_rejected(self):
        calibration,native,driver = fixture();driver['phases'][0]['record']['accepted']=False
        with self.assertRaises(ValueError):gate.evaluate(calibration,dict(lower=native),driver)
        calibration,native,driver = fixture();native['counts']['layout_transitive_parts_sum']=46
        with self.assertRaises(ValueError):gate.evaluate(calibration,dict(lower=native),driver)
        calibration,native,driver = fixture();driver['phases'] *= 2
        with self.assertRaises(ValueError):gate.evaluate(calibration,dict(lower=native),driver)
        calibration,native,driver = fixture();driver['production_authorized']=True
        with self.assertRaises(ValueError):gate.evaluate(calibration,dict(lower=native),driver)

    def test_model_failure_stays_statistical_and_does_not_claim_proof(self):
        calibration,native,driver = fixture();calibration['models']['lower']['coefficients'][3]=2e9
        result=gate.evaluate(calibration,dict(lower=native),driver)
        self.assertEqual(result['recommendation'],'NO_GO_CURRENT_WIRE_DEPENDENCIES')
        self.assertFalse(result['initial_problem2_proved'])
        self.assertFalse(result['actual_parallel_schedule_validated'])
        self.assertTrue(result['limitations'])


if __name__ == '__main__':unittest.main()
