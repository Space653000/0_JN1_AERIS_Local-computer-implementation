import json
import unittest
from unittest.mock import patch

from tests import test_role_acceptance as fixtures
from aeris_runtime.engineering import role_acceptance,domain_review


class ReviewerRoutingTests(unittest.TestCase):
    setUp=fixtures.RoleAcceptanceTests.setUp
    def test_qualification_scope_independence_and_seal_control_reviewer_selection(self):
        runner=role_acceptance.RoleAcceptanceFactory(self.root/'qualification')
        context={'product':'','transducer':'Speaker','lifecycle':'EVT','risk':'R1','source_kind':'SYNTHETIC'}
        request={**context,'needed_skills':['speaker-power-distortion-baseline']}
        with patch.object(role_acceptance,'STATE',self.root/'qualification'):
            self.assertFalse(domain_review.select_reviewers(request,['R016'])['complete'])
            nonlinear=runner.evaluate('R010')
            self.assertFalse(domain_review.select_reviewers(request,['R016'])['complete'])
            runner.evaluate('R075')
            result=domain_review.select_reviewers(request,['R016'])
            self.assertTrue(result['complete'])
            self.assertEqual({r['role_id'] for r in result['reviewers']},{'R010','R075'})
            self.assertFalse(domain_review.select_reviewers(request,['R010'])['complete'])
            self.assertFalse(domain_review.select_reviewers({**request,'conflicted_role_ids':['R075']},['R016'])['complete'])
            self.assertFalse(domain_review.select_reviewers({**request,'lifecycle':'MP'},['R016'])['complete'])
            # A different role's intact bundle cannot qualify this seat.
            (self.root/'qualification/R075.json').write_text(json.dumps({'run_id':nonlinear['run_id']}),encoding='utf-8')
            self.assertFalse(domain_review.select_reviewers(request,['R016'])['complete'])
