import unittest
import copy
from datetime import datetime, timezone
from unittest.mock import patch

from aeris_runtime import standards_registry as standards


class StandardsEngineTests(unittest.TestCase):
    def test_unknown_edition_never_becomes_formal_compliance(self):
        record=standards.list_standards()[0]
        result=standards.assess_applicability(record,{'region':'TW','domain_tags':['speaker'],'formal_use':True})
        self.assertEqual(result['state'],'BLOCKED_METADATA')
        self.assertIn('EDITION_UNKNOWN',result['blockers'])
        self.assertFalse(result['formal_conformance_verified'])

    def metadata(self):
        # Fictional metadata fixture; no claim about any actual standards edition.
        return {'family':'SYNTHETIC-SPEAKER-STANDARD','edition':'fixture-2','status':'CURRENT',
                'applicability':{'domain_tags':['speaker'],'regions':['TW']},
                'normative_informative':'NORMATIVE','license_access':'METADATA_ONLY',
                'source_url':'https://example.invalid/synthetic-standard','source_sha256':'a'*64,
                'verified_at_utc':datetime.now(timezone.utc).isoformat(),'verification_state':'LIVE_VERIFIED'}

    def test_metadata_scope_edition_license_and_supersession_change_decisions(self):
        record=self.metadata(); context={'region':'TW','domain_tags':['speaker'],'formal_use':False}
        self.assertEqual(standards.assess_applicability(record,context)['state'],'ELIGIBLE_FOR_DOMAIN_REVIEW')
        self.assertEqual(standards.assess_applicability(record,{**context,'region':'US'})['state'],'NOT_APPLICABLE')
        self.assertEqual(standards.assess_applicability(record,{**context,'domain_tags':['patent']})['state'],'NOT_APPLICABLE')
        self.assertIn('NORMATIVE_TEXT_ACCESS_NOT_AUTHORIZED',standards.assess_applicability(record,{**context,'formal_use':True})['blockers'])
        for field,value,code in (('edition',None,'EDITION_UNKNOWN'),('superseded_by','fixture-3','SUPERSEDED_EDITION'),
                ('source_sha256','bad','SOURCE_HASH_UNKNOWN'),('verified_at_utc','2000-01-01T00:00:00Z','METADATA_VERIFICATION_STALE')):
            result=standards.assess_applicability({**record,field:value},context)
            self.assertEqual(result['state'],'BLOCKED_METADATA'); self.assertIn(code,result['blockers'])
            self.assertTrue(result['free_baseline_execution_allowed'])
            self.assertFalse(result['formal_conformance_verified'])

    def test_change_impact_targets_linked_requirements_without_rewriting_them(self):
        previous=self.metadata(); current={**previous,'edition':'fixture-3','status':'WITHDRAWN'}
        links=[{'standard_family':previous['family'],'requirement_id':'REQ-SPL','test_id':'T-SPL'},
               {'standard_family':'OTHER-FAMILY','requirement_id':'REQ-OTHER','test_id':'T-OTHER'}]
        original=copy.deepcopy(links)
        result=standards.change_impact(previous,current,links)
        self.assertEqual([r['requirement_id'] for r in result['affected_requirements']],['REQ-SPL'])
        self.assertEqual(result['affected_requirements'][0]['reason_fields'],['edition','status'])
        self.assertEqual(links,original)
        self.assertEqual(standards.change_impact(previous,previous,links)['state'],'NO_METADATA_CHANGE')
        with self.assertRaises(ValueError): standards.change_impact(previous,{'family':'OTHER'},links)

    def test_legacy_formal_entrypoint_cannot_bypass_edition_or_scope_checks(self):
        record={**self.metadata(),'standard_id':'SYNTHETIC-SPEAKER-STANDARD','edition':None}
        with patch.object(standards,'list_standards',return_value=[record]):
            with self.assertRaises(RuntimeError): standards.require_formal_use(record['standard_id'])


if __name__=='__main__': unittest.main()
