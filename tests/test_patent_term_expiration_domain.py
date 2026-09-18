"""Independent worked decisions for the US utility patent term
expiration baseline, not a PTA/PTE calculation or legal opinion."""
import unittest
from aeris_runtime.skills_runtime import run_skill

BASE={'filing_date_iso':'2010-05-15','term_years':20,'claimed_expiration_date_iso':'2030-05-15'}


class PatentTermExpirationDomainTests(unittest.TestCase):
    def test_claimed_matches_20_year_baseline(self):
        values=run_skill('patent-term-expiration-baseline',BASE)['values']
        self.assertEqual(values['baseline_expiration_date_iso'],'2030-05-15')
        self.assertTrue(values['matches_baseline'])
        self.assertEqual(values['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_leap_day_filing_falls_back_to_feb_28(self):
        values=run_skill('patent-term-expiration-baseline',
            {'filing_date_iso':'2000-02-29','term_years':19,'claimed_expiration_date_iso':'2019-02-28'})['values']
        self.assertEqual(values['baseline_expiration_date_iso'],'2019-02-28')
        self.assertTrue(values['matches_baseline'])

    def test_deviating_claim_is_flagged_for_reconciliation(self):
        values=run_skill('patent-term-expiration-baseline',{**BASE,'claimed_expiration_date_iso':'2032-01-01'})['values']
        self.assertEqual(values['difference_days'],596)
        self.assertFalse(values['matches_baseline'])
        self.assertEqual(values['disposition'],'CLAIMED_EXPIRATION_DEVIATES_FROM_STATUTORY_BASELINE')

    def test_invalid_or_malformed_dates_are_rejected(self):
        for overrides in ({'filing_date_iso':'not-a-date'},{'claimed_expiration_date_iso':'2030-13-99'},{'term_years':0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run_skill('patent-term-expiration-baseline',{**BASE,**overrides})


if __name__=='__main__': unittest.main()
