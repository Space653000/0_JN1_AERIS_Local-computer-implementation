"""Independent worked decisions for the Friis free-space RF link-budget
baseline, not a protocol certification or real-environment RF
measurement claim."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'tx_power_dbm':4,'tx_gain_dbi':0,'rx_gain_dbi':0,'frequency_hz':2400000000,'distance_m':10,'rx_sensitivity_dbm':-90}


class RfLinkBudgetFriisDomainTests(unittest.TestCase):
    def test_nominal_link_closes_with_margin(self):
        values=run_skill('rf-link-budget-friis-baseline',BASE)['values']
        self.assertAlmostEqual(values['free_space_path_loss_db'],60.0520080561155)
        self.assertAlmostEqual(values['received_power_dbm'],-56.0520080561155)
        self.assertTrue(values['link_closes'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_long_range_link_fails_to_close(self):
        values=run_skill('rf-link-budget-friis-baseline',{**BASE,'distance_m':5000})['values']
        self.assertFalse(values['link_closes'])
        self.assertEqual(values['disposition'],'LINK_DOES_NOT_CLOSE_AT_THIS_DISTANCE')

    def test_doubling_distance_adds_about_6db_of_path_loss(self):
        base=run_skill('rf-link-budget-friis-baseline',BASE)['values']
        doubled=run_skill('rf-link-budget-friis-baseline',{**BASE,'distance_m':20})['values']
        self.assertAlmostEqual(doubled['free_space_path_loss_db']-base['free_space_path_loss_db'],20*0.3010299956639812,places=5)

    def test_invalid_or_nonfinite_inputs_are_rejected(self):
        for overrides in ({'frequency_hz':0},{'distance_m':-1},{'tx_power_dbm':True},{'frequency_hz':float('nan')}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('rf-link-budget-friis-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
