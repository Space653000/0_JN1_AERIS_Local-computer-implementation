import copy
import unittest
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aeris_runtime.skills_runtime import run_skill
from aeris_runtime import audit, evidence, taskstate, verification, workflow, reproduction
from aeris_runtime.config import ROOT


BASE={
    'leak_pole_hz':20.0,'bass_reference_hz':100.0,'max_leak_loss_db':3.0,
    'feedback_crossover_hz':100.0,'feedback_delay_ms':0.5,'plant_phase_lag_deg':90.0,
    'min_phase_margin_deg':45.0,'ff_wind_rms_pa':0.001,'max_ff_wind_rms_pa':0.003,
    'call_speech_rms_pa':0.02,'call_ambient_rms_pa':0.001,'min_call_snr_db':20.0,
    'driver_peak_excursion_mm':0.3,'safe_peak_excursion_mm':0.5,
    'occlusion_boost_db':3.0,'max_occlusion_boost_db':6.0,
}


class TwsDomainTests(unittest.TestCase):
    def test_hybrid_anc_fit_call_and_excursion_are_distinct_decisions(self):
        result=run_skill('tws-fit-anc-call-baseline',BASE)
        values=result['values']
        self.assertEqual(values['anc_topology_candidate'],'HYBRID')
        self.assertAlmostEqual(values['phase_margin_deg'],72.0)
        self.assertAlmostEqual(values['leak_loss_db'],0.1703333929878)
        self.assertAlmostEqual(values['call_snr_db'],23.0102999566398)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertFalse(result['physical_measurement_verified'])

    def test_feedback_boundary_and_delay_violation_change_topology(self):
        boundary=run_skill('tws-fit-anc-call-baseline',{**BASE,'feedback_delay_ms':1.25})['values']
        self.assertEqual(boundary['phase_margin_deg'],45.0)
        self.assertEqual(boundary['anc_topology_candidate'],'HYBRID')
        delayed=run_skill('tws-fit-anc-call-baseline',{**BASE,'feedback_delay_ms':3.0})['values']
        self.assertEqual(delayed['phase_margin_deg'],-18.0)
        self.assertEqual(delayed['anc_topology_candidate'],'FF_ONLY')
        self.assertIn('LOWER_CROSSOVER_OR_LATENCY_AND_REMEASURE_LOOP',delayed['required_revisions'])

    def test_same_call_snr_from_wind_or_ambient_requires_different_anc_action(self):
        windy=run_skill('tws-fit-anc-call-baseline',{**BASE,'ff_wind_rms_pa':0.01})['values']
        ambient=run_skill('tws-fit-anc-call-baseline',{**BASE,'call_ambient_rms_pa':0.01})['values']
        self.assertAlmostEqual(windy['call_snr_db'],ambient['call_snr_db'])
        self.assertEqual(windy['anc_topology_candidate'],'FB_ONLY')
        self.assertEqual(ambient['anc_topology_candidate'],'HYBRID')
        self.assertIn('DISABLE_OR_LIMIT_WIND_EXPOSED_FEEDFORWARD_PATH',windy['required_revisions'])
        self.assertNotIn('DISABLE_OR_LIMIT_WIND_EXPOSED_FEEDFORWARD_PATH',ambient['required_revisions'])

    def test_fit_excursion_and_occlusion_revisions_are_not_interchangeable(self):
        for field,value,expected in (
            ('leak_pole_hz',200.0,'RECHECK_TIP_SEAL_BEFORE_BASS_EQ'),
            ('driver_peak_excursion_mm',0.6,'LIMIT_BASS_DRIVE_OR_REVISE_RECEIVER'),
            ('occlusion_boost_db',8.0,'REVISE_VENT_OR_SIDETONE_WITH_SEAL_RETEST')):
            result=run_skill('tws-fit-anc-call-baseline',{**BASE,field:value})['values']
            self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')
            self.assertEqual(result['required_revisions'],[expected])
        self.assertEqual(run_skill('tws-fit-anc-call-baseline',BASE)['values']['required_revisions'],[])

    def test_negative_units_nonfinite_and_self_asserted_measurement_rejected(self):
        for params in ({**BASE,'feedback_delay_s':0.0005},{**BASE,'physical_measurement_verified':True},
                       {**BASE,'call_ambient_rms_pa':0},{**BASE,'leak_pole_hz':-1},
                       {**BASE,'feedback_delay_ms':float('nan')},{**BASE,'feedback_delay_ms':True}):
            with self.subTest(params=params),self.assertRaises(ValueError):
                run_skill('tws-fit-anc-call-baseline',params)

    def test_repeated_output_is_deterministic_and_both_anc_paths_can_be_rejected(self):
        params={**BASE,'ff_wind_rms_pa':0.01,'feedback_delay_ms':3.0}
        first=run_skill('tws-fit-anc-call-baseline',params)
        self.assertEqual(first,run_skill('tws-fit-anc-call-baseline',copy.deepcopy(params)))
        self.assertEqual(first['values']['anc_topology_candidate'],'PASSIVE')
        self.assertFalse(first['professional_tool_verified'])

    def test_domain_workflow_seals_rejected_design_and_replays_without_false_verification(self):
        temp_root=ROOT/'.aeris/test-temp'; temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory,ExitStack() as stack:
            root=Path(directory)
            for module,name,value in (
                (taskstate,'TASK_ROOT',root/'tasks'),(evidence,'EVIDENCE_ROOT',root/'evidence'),
                (verification,'VERIFICATION_ROOT',root/'verification'),(workflow,'WORKFLOW_ROOT',root/'workflows'),
                (reproduction,'REPRO_ROOT',root/'reproduction'),(audit,'AUDIT_DIR',root/'audit'),
                (audit,'AUDIT_FILE',root/'audit/audit.jsonl'),(audit,'LEDGER_PATH',root/'audit/audit.jsonl'),
                (audit,'LOCK_FILE',root/'audit/.lock')):
                stack.enter_context(patch.object(module,name,value))
            params={**BASE,'leak_pole_hz':200.0}
            created=workflow.create_engineering_workflow('Synthetic TWS seal challenge','R048',risk='R1',
                         skill_id='tws-fit-anc-call-baseline',skill_params=params)
            result=workflow.execute_workflow(created['workflow_id'],'R048')
            self.assertEqual(result['state'],'EVIDENCED')
            self.assertEqual(result['execution']['skill_result']['values']['disposition'],'DESIGN_REVISION_REQUIRED')
            self.assertEqual(result['next_gate'],'G2_DOMAIN_REVIEW')
            run=result['execution']['run_id']
            self.assertTrue(evidence.validate_bundle(run)['valid'])
            self.assertEqual(reproduction.reproduce_run(run)['result'],'PASS')
            # Post-seal input mutation is caught before any purported replay.
            (evidence.bundle_dir(run)/'raw/engineering-input.json').write_text('{}',encoding='utf-8')
            self.assertEqual(reproduction.reproduce_run(run)['result'],'FAIL')


if __name__=='__main__': unittest.main()
