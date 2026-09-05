"""Independent quadratic-root oracles for ideal sealed-box alignment."""
import copy
import math
import unittest
from aeris_runtime.engineering import sealed_alignment
from aeris_runtime.engineering import sealed_alignment_review
from aeris_runtime.engineering import role_acceptance, domain_review
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE={'model':'IDEAL_SEALED_SMALL_SIGNAL','fs_hz':50,'fs_lower_hz':50,'fs_upper_hz':50,
      'qts':0.4,'qts_lower':0.4,'qts_upper':0.4,'vas_m3':0.02,'vas_lower_m3':0.02,'vas_upper_m3':0.02,
      'box_m3':0.01,'box_lower_m3':0.01,'box_upper_m3':0.01,
      'maximum_f3_hz':100,'minimum_qtc':0.5,'maximum_qtc':1,
      'maximum_box_m3':0.025,'largest_dimension_m':0.3,'analysis_max_hz':150,
      'sound_speed_lower_m_s':340,'maximum_dimension_wavelength_ratio':0.2}


class SealedAlignmentTests(unittest.TestCase):
    def test_f3_is_not_fc_except_at_butterworth_alignment(self):
        result=sealed_alignment.analyze(BASE)
        self.assertAlmostEqual(result['fc_hz'],86.60254037844386)
        self.assertAlmostEqual(result['qtc'],0.6928203230275509)
        self.assertAlmostEqual(result['f3_hz'],88.42515249302765)
        self.assertNotAlmostEqual(result['f3_hz'],result['fc_hz'])
        p={**BASE,'qts':0.5,'qts_lower':0.5,'qts_upper':0.5,'vas_m3':0.01,'vas_lower_m3':0.01,'vas_upper_m3':0.01}
        result=sealed_alignment.analyze(p)
        self.assertAlmostEqual(result['f3_hz'],50*math.sqrt(2))
        self.assertAlmostEqual(result['f3_hz'],result['fc_hz'])

    def test_f3_interval_includes_interior_minimum_not_only_corners(self):
        p={**BASE,'box_lower_m3':0.005,'box_upper_m3':0.02}
        result=sealed_alignment.analyze(p)
        self.assertAlmostEqual(result['f3_interval_hz'][0],88.38834764831844)
        self.assertAlmostEqual(result['f3_interval_hz'][1],93.07258378308104)
        self.assertLess(result['f3_interval_hz'][0],92.46208640350551)

    def test_lower_analysis_frequency_cannot_hide_geometry_invalidity(self):
        invalid={**BASE,'largest_dimension_m':1}
        self.assertEqual(sealed_alignment.analyze(invalid)['disposition'],'DESIGN_REVISION_REQUIRED')
        lower={**invalid,'analysis_max_hz':10}
        result=sealed_alignment.analyze(lower)
        self.assertTrue(result['checks'][4]['passed'])
        self.assertFalse(result['checks'][3]['passed'])
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_parameter_uncertainty_and_box_policy_are_not_physical_acceptance(self):
        p={**BASE,'box_lower_m3':0.005,'box_upper_m3':0.02,'maximum_f3_hz':90,'maximum_box_m3':0.015}
        result=sealed_alignment.analyze(p)
        self.assertFalse(result['checks'][0]['passed'])
        self.assertFalse(result['checks'][2]['passed'])
        self.assertFalse(result['excursion_verified'])
        self.assertFalse(result['physical_measurement_verified'])

    def test_wrong_model_nonfinite_and_inconsistent_bounds_rejected(self):
        for patch in ({'model':'VENTED'},{'box_lower_m3':0},{'qts_lower':0.5},
                      {'fs_hz':float('nan')},{'vas_m3':True},{'minimum_qtc':2,'maximum_qtc':1}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):sealed_alignment.analyze({**BASE,**patch})

    def test_independent_reviewer_checks_extrema_and_false_domain_assertions(self):
        for parameters in (BASE,{**BASE,'box_lower_m3':0.005,'box_upper_m3':0.02},
                {**BASE,'qts':0.01,'qts_lower':0.01,'qts_upper':0.01},
                {**BASE,'qts':5,'qts_lower':5,'qts_upper':5},
                {**BASE,'largest_dimension_m':1,'analysis_max_hz':10}):
            with self.subTest(parameters=parameters):
                value=sealed_alignment.analyze(parameters)
                self.assertEqual(sealed_alignment_review.review(parameters,value)['decision'],'BOUNDED_REVIEW_ACCEPT')
        value=sealed_alignment.analyze(BASE)
        for field,wrong in (('f3_hz',value['fc_hz']),('excursion_verified',True),
                ('ported_alignment_verified',True),('physical_measurement_verified',True),
                ('required_analysis_max_hz',10),('model_assumptions',[]),('counter_hypotheses',[])):
            with self.subTest(field=field):
                candidate={**value,field:wrong}
                self.assertEqual(sealed_alignment_review.review(BASE,candidate)['decision'],'CHANGES_REQUIRED')
        p={**BASE,'box_lower_m3':0.005,'box_upper_m3':0.02}
        value=sealed_alignment.analyze(p);value['f3_interval_hz'][0]=92.46208640350551
        self.assertEqual(sealed_alignment_review.review(p,value)['decision'],'CHANGES_REQUIRED')
        value=sealed_alignment.analyze(BASE);value['checks'][0]['passed']=False
        self.assertEqual(sealed_alignment_review.review(BASE,value)['decision'],'CHANGES_REQUIRED')
        value=sealed_alignment.analyze(BASE);value['checks'][0]['actual']=1000
        self.assertEqual(sealed_alignment_review.review(BASE,value)['decision'],'CHANGES_REQUIRED')
        value=sealed_alignment.analyze(BASE);value['checks'][0]['limit']=101
        self.assertEqual(sealed_alignment_review.review(BASE,value)['decision'],'CHANGES_REQUIRED')

    def test_distinct_sealed_suites_route_to_lumped_reviewer_and_reproduce(self):
        with isolated_engineering_state():
            runner=role_acceptance.RoleAcceptanceFactory()
            for role,skill in (
                    ('R009','speaker-sealed-alignment-baseline'),
                    ('R021','speaker-sealed-lumped-domain-review')):
                result=runner.evaluate(role,skill)
                self.assertTrue(result['execution_passed'],result)
                self.assertEqual(result['case_count'],14)
                self.assertEqual(result['level'],'L2')
                self.assertFalse(result['role_l3_accepted'])
            rejected=run_role('R009','speaker-sealed-alignment-baseline',
                {**BASE,'largest_dimension_m':1,'analysis_max_hz':10},
                objective='Reject artificial frequency reduction hiding spatial invalidity',source_kind='SYNTHETIC')
            self.assertEqual(rejected['review']['decision'],'DESIGN_REVISION_REQUIRED')
            accepted=run_role('R009','speaker-sealed-alignment-baseline',BASE,
                objective='Check bounded ideal sealed alignment without measured claims',source_kind='SYNTHETIC')
            self.assertEqual(accepted['review']['decision'],'BOUNDED_REVIEW_ACCEPT')
            self.assertEqual([r['role_id'] for r in accepted['pod']['reviewers']],['R021'])
            self.assertTrue(domain_review.review_status(accepted['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(accepted['evidence_run_id'])['result'],'PASS')


if __name__=='__main__':unittest.main()
