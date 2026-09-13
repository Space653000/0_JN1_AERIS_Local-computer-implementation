import unittest

from aeris_runtime.engineering import challenges, l3_award
from tests.engineering_test_support import isolated_engineering_state


class L3AwardTests(unittest.TestCase):
    def test_ai_prepares_packet_and_only_human_grant_awards_l3(self):
        with isolated_engineering_state():
            result = challenges.run('SPEAKER_FR', prepare_qualifications=True)
            run_id = result['run_id']
            self.assertEqual(l3_award.pending_review_packets(), [])
            self.assertEqual(l3_award.role_l3_status(result['role_id'])['l3_awarded_skills'], [])

            packet = l3_award.prepare_review(run_id)
            self.assertEqual(packet['role_id'], result['role_id'])
            self.assertEqual(packet['skill_id'], result['skill_id'])
            self.assertEqual(packet['ai_summary']['stage_decisions'], ['DESIGN_REVISION_REQUIRED', 'BOUNDED_REVIEW_ACCEPT'])
            pending = l3_award.pending_review_packets()
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]['packet_sha256'], packet['packet_sha256'])

            # Still not awarded until a Human explicitly decides.
            self.assertEqual(l3_award.role_l3_status(result['role_id'])['l3_awarded_skills'], [])

            with self.assertRaises(ValueError):
                l3_award.human_decide(packet['packet_sha256'], '', 'GRANT')
            with self.assertRaises(ValueError):
                l3_award.human_decide(packet['packet_sha256'], 'Chief Engineer', 'AUTO_GRANT')

            entry = l3_award.human_decide(packet['packet_sha256'], 'Chief Engineer', 'GRANT', note='reviewed manually')
            self.assertEqual(entry['actor'], 'Chief Engineer')
            self.assertEqual(entry['event_type'], 'L3_AWARD_GRANTED')

            # A decided packet drops out of the pending queue and cannot be re-decided.
            self.assertEqual(l3_award.pending_review_packets(), [])
            with self.assertRaises(ValueError):
                l3_award.human_decide(packet['packet_sha256'], 'Chief Engineer', 'REJECT')

            status = l3_award.role_l3_status(result['role_id'])
            self.assertEqual(status['l3_awarded_skills'], [result['skill_id']])

            # The original challenge receipt's self-report is untouched -- still False.
            self.assertFalse(challenges.status(run_id)['valid'] is False)
            record_check = challenges.status(run_id)
            self.assertTrue(record_check['valid'])
            self.assertFalse(record_check['role_l3_awarded'])

            self.assertTrue(l3_award.verify_ledger()['valid'])

            revoked = l3_award.human_revoke(packet['packet_sha256'], 'Chief Engineer', note='evidence concern')
            self.assertEqual(revoked['event_type'], 'L3_AWARD_REVOKED')
            self.assertEqual(l3_award.role_l3_status(result['role_id'])['l3_awarded_skills'], [])
            with self.assertRaises(ValueError):
                l3_award.human_revoke(packet['packet_sha256'], 'Chief Engineer')

    def test_reject_leaves_role_unawarded_and_cannot_be_regranted(self):
        with isolated_engineering_state():
            result = challenges.run('TWS_FIT', prepare_qualifications=True)
            packet = l3_award.prepare_review(result['run_id'])
            l3_award.human_decide(packet['packet_sha256'], 'Chief Engineer', 'REJECT')
            self.assertEqual(l3_award.role_l3_status(result['role_id'])['l3_awarded_skills'], [])
            with self.assertRaises(ValueError):
                l3_award.human_decide(packet['packet_sha256'], 'Chief Engineer', 'GRANT')

    def test_cannot_prepare_from_tampered_challenge_receipt(self):
        with isolated_engineering_state():
            from aeris_runtime import evidence
            from aeris_runtime.engineering import factory
            result = challenges.run('ARRAY_DOA', prepare_qualifications=True)
            path = evidence.bundle_dir(result['run_id']) / 'processed/challenge.json'
            record = factory.read(path)
            factory.write(path, {**record, 'role_l3_awarded': True})
            evidence.seal_bundle(result['run_id'], 'tamper for negative test')
            with self.assertRaises(ValueError):
                l3_award.prepare_review(result['run_id'])


if __name__ == '__main__':
    unittest.main()
