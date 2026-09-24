"""Independent worked decisions for the UCB1 next-experiment-bound
baseline, not an override of any risk authority."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'observed_mean_reward':0.5,'total_trials_across_all_arms':100,'this_arm_trials':10,'risk_gate_passed':True}


class Ucb1NextExperimentBoundDomainTests(unittest.TestCase):
    def test_undersampled_arm_has_substantial_exploration_bonus(self):
        values=run_skill('ucb1-next-experiment-bound-baseline',BASE)['values']
        self.assertAlmostEqual(values['exploration_bonus'],0.9597051824376164)
        self.assertAlmostEqual(values['ucb_score'],1.4597051824376164)
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_well_sampled_arm_has_smaller_bonus(self):
        values=run_skill('ucb1-next-experiment-bound-baseline',{**BASE,'this_arm_trials':50})['values']
        self.assertAlmostEqual(values['exploration_bonus'],0.4291932052578695)
        self.assertAlmostEqual(values['ucb_score'],0.9291932052578695)

    def test_failed_risk_gate_blocks_regardless_of_score(self):
        values=run_skill('ucb1-next-experiment-bound-baseline',{**BASE,'risk_gate_passed':False})['values']
        self.assertAlmostEqual(values['ucb_score'],1.4597051824376164)
        self.assertEqual(values['disposition'],'EXPERIMENT_BLOCKED_BY_RISK_GATE_REGARDLESS_OF_UCB_SCORE')
        self.assertFalse(values['checks'][0]['passed'])

    def test_invalid_or_out_of_range_inputs_are_rejected(self):
        for overrides in ({'this_arm_trials':200},{'total_trials_across_all_arms':1},
                           {'risk_gate_passed':'yes'},{'this_arm_trials':True}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('ucb1-next-experiment-bound-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
