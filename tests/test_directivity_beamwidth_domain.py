"""Independent worked decisions for the directivity beamwidth baseline,
not a full 3D directivity index or vertical-plane measurement."""
import unittest
from aeris_runtime.skills_runtime import run_skill

_ANGLES=[-180,-170,-160,-150,-140,-130,-120,-110,-100,-90,-80,-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180]
_LEVELS=[69.3,69.8,70.3,70.8,71.3,71.8,72.3,72.8,73.3,73.8,77.2,80.2,82.8,85.0,86.8,88.2,89.2,89.8,90.0,89.8,89.2,88.2,86.8,85.0,82.8,80.2,77.2,73.8,73.3,72.8,72.3,71.8,71.3,70.8,70.3,69.8,69.3]
BASE={'angles_deg':_ANGLES,'levels_db':_LEVELS,'on_axis_reference_db':90,'threshold_db':6,'maximum_acceptable_beamwidth_deg':120}


class DirectivityBeamwidthDomainTests(unittest.TestCase):
    def test_symmetric_pattern_matches_independent_worked_calculation(self):
        values=run_skill('directivity-beamwidth-baseline',BASE)['values']
        self.assertAlmostEqual(values['negative_crossing_deg'],-54.54545454545454)
        self.assertAlmostEqual(values['positive_crossing_deg'],54.54545454545454)
        self.assertAlmostEqual(values['beamwidth_deg'],109.09090909090908)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_beamwidth_exceeds_tight_coverage_target(self):
        values=run_skill('directivity-beamwidth-baseline',{**BASE,'maximum_acceptable_beamwidth_deg':50})['values']
        self.assertAlmostEqual(values['beamwidth_deg'],109.09090909090908)
        self.assertFalse(values['within_target'])
        self.assertEqual(values['disposition'],'BEAMWIDTH_EXCEEDS_TARGET')

    def test_flat_pattern_with_no_crossing_is_rejected(self):
        with self.assertRaises(ValueError):
            run_skill('directivity-beamwidth-baseline',
                {'angles_deg':[-90,-45,0,45,90],'levels_db':[90,90,90,90,90],
                 'on_axis_reference_db':90,'threshold_db':6,'maximum_acceptable_beamwidth_deg':120})

    def test_invalid_or_mismatched_inputs_are_rejected(self):
        for overrides in ({'levels_db':[90,89,88]},{'threshold_db':0},{'angles_deg':[0,10]}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('directivity-beamwidth-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
