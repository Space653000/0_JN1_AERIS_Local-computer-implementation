"""Fictitious standards only; no invented real edition/source verification."""
import copy
import hashlib
import json
import unittest
from aeris_runtime.engineering import standard_metadata
from aeris_runtime.engineering import standard_metadata_review


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


META={'family':'SYNTHETIC-SPEAKER-STANDARD','edition':'fixture-2','status':'CURRENT','superseded_by':None,
      'regions':['TW'],'domain_tags':['speaker'],'normative_informative':'NORMATIVE',
      'license_access':'METADATA_ONLY','requirement_ids':['REQ-SPL']}
RECORD={'metadata':META,'source':{'record_id':'SYN-NEW','publisher':'Synthetic fixture publisher',
        'url':'https://example.invalid/fixture-metadata','retrieved_at':'2026-08-01T00:00:00Z',
        'source_kind':'SYNTHETIC','content_sha256':digest(META)}}
BASE={'as_of':'2026-09-01T00:00:00Z','freshness_days':180,'intended_use':'METADATA_ONLY',
      'region':'TW','domain_tags':['speaker'],'requirements':[{'id':'REQ-SPL','family':META['family'],'region':'TW','domain_tags':['speaker']}],
      'previous':copy.deepcopy(RECORD),'current':copy.deepcopy(RECORD)}
BASE['previous']['source']['record_id']='SYN-PREVIOUS'
BASE['previous']['source']['retrieved_at']='2024-01-01T00:00:00Z'


class StandardMetadataTests(unittest.TestCase):
    def test_refresh_cannot_relabel_existing_previous_source_as_new(self):
        initial=copy.deepcopy(BASE);initial['current']['source']['record_id']='SYN-OLD'
        initial['current']['source']['retrieved_at']='2025-01-01T00:00:00Z'
        initial['previous']['source']['retrieved_at']='2026-08-01T00:00:00Z'
        revised=copy.deepcopy(initial);revised['current']['source']=copy.deepcopy(initial['previous']['source'])
        with self.assertRaises(ValueError):standard_metadata.validate_revision(initial,revised)

    def test_company_refresh_origin_is_bound_to_same_attempt_and_content(self):
        from tests.engineering_test_support import isolated_engineering_state
        from aeris_runtime.engineering import challenges,factory
        from aeris_runtime import evidence
        with isolated_engineering_state():
            first=challenges.run('STANDARDS_PROVENANCE',prepare_qualifications=True)
            second=challenges.run('STANDARDS_PROVENANCE')
            self.assertTrue(challenges.status(second['run_id'])['valid'])
            self.assertFalse(second['stages'][1]['report']['numerical_result']['values']['live_verified'])
            path=evidence.bundle_dir(second['run_id'])/'processed/challenge.json';original=factory.read(path)
            for receipt in (first['revision_origin'],None,{**second['revision_origin'],'preserved_metadata_sha256':'0'*64}):
                factory.write(path,{**original,'revision_origin':receipt});evidence.seal_bundle(second['run_id'],'test metadata origin corruption')
                self.assertFalse(challenges.status(second['run_id'])['valid'])
            factory.write(path,original);evidence.seal_bundle(second['run_id'],'restore metadata origin')
            with self.assertRaises(ValueError):
                challenges._standard_origin(second['inputs'],first['stages'][0]['report'],second['run_id'])

    def test_qualified_standards_workflow_reproduces_without_live_source_claim(self):
        from tests.engineering_test_support import isolated_engineering_state
        from aeris_runtime.engineering.role_acceptance import RoleAcceptanceFactory
        from aeris_runtime.engineering.orchestration import run_role
        from aeris_runtime.engineering.domain_review import review_status
        from aeris_runtime import reproduction
        with isolated_engineering_state():
            for role in ('R089','R090'):
                result=RoleAcceptanceFactory().evaluate(role)
                self.assertTrue(result['execution_passed'],result)
                self.assertEqual(result['level'],'L2')
            report=run_role('R089','standards-metadata-applicability-baseline',BASE,
                objective='Supplied standard metadata applicability',source_kind='SYNTHETIC',context={'product':'Metadata review'})
            self.assertEqual(report['review']['decision'],'BOUNDED_REVIEW_ACCEPT',report['review'])
            self.assertEqual([r['role_id'] for r in report['pod']['reviewers']],['R090'])
            self.assertFalse(report['numerical_result']['values']['live_verified'])
            self.assertTrue(review_status(report['review']['review_run_id'])['valid'])
            self.assertEqual(reproduction.reproduce_run(report['evidence_run_id'])['result'],'PASS')

    def test_independent_review_challenges_edition_scope_and_false_certification(self):
        candidate=standard_metadata.analyze(BASE)
        self.assertEqual(standard_metadata_review.review(BASE,candidate)['decision'],'BOUNDED_REVIEW_ACCEPT')
        for field,value in (('live_verified',True),('source_authenticity_verified',True),
                            ('formal_conformance_verified',True),('edition','invented-edition'),
                            ('unresolved',[]),('next_discriminating_experiment','AUTO_CERTIFY')):
            with self.subTest(field=field):
                self.assertEqual(standard_metadata_review.review(BASE,{**candidate,field:value})['decision'],'CHANGES_REQUIRED')

    def test_real_discovery_registry_unknowns_remain_unknown(self):
        from aeris_runtime.standards_registry import list_standards
        entry=list_standards()[0]
        record=standard_metadata.from_registry(entry,['REQ-SPL'])
        p=copy.deepcopy(BASE);p['previous']=copy.deepcopy(record);p['current']=record
        p['requirements'][0]['family']=record['metadata']['family']
        result=standard_metadata.analyze(p)
        self.assertEqual(record['source']['source_kind'],'REGISTRY_UNVERIFIED')
        self.assertIn('EDITION_UNKNOWN',result['metadata_blockers'])
        self.assertIn('SOURCE_RETRIEVAL_UNKNOWN',result['metadata_blockers'])
        self.assertFalse(result['live_verified'])

    def test_informative_classification_neither_grants_access_nor_normative_use(self):
        for access in ('METADATA_ONLY','PUBLIC_FULL_TEXT'):
            p=copy.deepcopy(BASE);p['intended_use']='NORMATIVE_USE'
            for record in (p['previous'],p['current']):
                record['metadata']['normative_informative']='INFORMATIVE';record['metadata']['license_access']=access
                record['source']['content_sha256']=digest(record['metadata'])
            result=standard_metadata.analyze(p)
            self.assertIn('CLASSIFICATION_INCOMPATIBLE_WITH_NORMATIVE_USE',result['license_blockers'])
            self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')
            if access=='METADATA_ONLY':self.assertIn('NORMATIVE_TEXT_ACCESS_UNCONFIRMED',result['license_blockers'])

    def test_refresh_revision_preserves_semantics_and_previous_snapshot(self):
        initial=copy.deepcopy(BASE);initial['current']['source']['retrieved_at']='2025-01-01T00:00:00Z'
        initial['current']['source']['record_id']='SYN-OLD'
        standard_metadata.validate_revision(initial,BASE)
        for field,value in (('as_of','2027-01-01T00:00:00Z'),('freshness_days',365)):
            with self.subTest(field=field),self.assertRaises(ValueError):
                standard_metadata.validate_revision(initial,{**copy.deepcopy(BASE),field:value})
        p=copy.deepcopy(BASE);p['current']['metadata']['edition']='fixture-3';p['current']['source']['content_sha256']=digest(p['current']['metadata'])
        with self.assertRaises(ValueError):standard_metadata.validate_revision(initial,p)
        p=copy.deepcopy(BASE);p['current']['source']['record_id']='SYN-OLD'
        with self.assertRaises(ValueError):standard_metadata.validate_revision(initial,p)

    def test_missing_independently_required_mapping_cannot_be_metadata_ready(self):
        p=copy.deepcopy(BASE)
        for record in (p['previous'],p['current']):
            record['metadata']['requirement_ids']=[];record['source']['content_sha256']=digest(record['metadata'])
        result=standard_metadata.analyze(p)
        self.assertIn('REQUIRED_REQUIREMENT_MAPPING_MISSING',result['metadata_blockers'])
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')

    def test_cross_family_mapping_is_rejected(self):
        p=copy.deepcopy(BASE);p['requirements'][0]['family']='SYNTHETIC-OTHER'
        with self.assertRaises(ValueError):standard_metadata.analyze(p)

    def test_supplied_current_metadata_never_becomes_live_verification(self):
        result=standard_metadata.analyze(BASE)
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')
        self.assertFalse(result['live_verified'])
        self.assertFalse(result['formal_conformance_verified'])
        self.assertFalse(result['source_authenticity_verified'])

    def test_same_content_refresh_improves_only_freshness(self):
        p=copy.deepcopy(BASE);p['current']['source']['retrieved_at']='2025-01-01T00:00:00Z'
        old=standard_metadata.analyze(p)
        self.assertIn('SOURCE_STALE',old['metadata_blockers'])
        p['current']['source']['retrieved_at']='2026-08-01T00:00:00Z'
        result=standard_metadata.analyze(p)
        self.assertEqual(result['semantic_changes'],[])
        self.assertEqual(result['impacted_requirement_ids'],[])
        self.assertEqual(result['disposition'],'BOUNDED_BASELINE_ACCEPT')

    def test_edition_change_and_removed_scope_still_need_review_after_refresh(self):
        p=copy.deepcopy(BASE);p['current']['metadata']['edition']='fixture-3';p['current']['metadata']['regions']=['US']
        p['current']['metadata']['requirement_ids']=[]
        p['current']['source']['content_sha256']=digest(p['current']['metadata'])
        result=standard_metadata.analyze(p)
        self.assertIn('REQ-SPL',result['impacted_requirement_ids'])
        self.assertEqual(result['disposition'],'DESIGN_REVISION_REQUIRED')
        self.assertEqual(result['applicability'],'NOT_APPLICABLE')

    def test_unknown_scope_is_not_an_exclusion_and_normative_license_is_separate(self):
        p=copy.deepcopy(BASE);p['current']['metadata']['regions']=[];p['current']['source']['content_sha256']=digest(p['current']['metadata'])
        self.assertEqual(standard_metadata.analyze(p)['applicability'],'UNKNOWN')
        p=copy.deepcopy(BASE);p['intended_use']='NORMATIVE_USE'
        result=standard_metadata.analyze(p)
        self.assertIn('NORMATIVE_TEXT_ACCESS_UNCONFIRMED',result['license_blockers'])
        self.assertTrue(result['free_baseline_execution_allowed'])

    def test_bad_hash_future_date_and_fabricated_real_synthetic_family_rejected(self):
        variants=[]
        p=copy.deepcopy(BASE);p['current']['source']['content_sha256']='0'*64;variants.append(p)
        p=copy.deepcopy(BASE);p['current']['source']['retrieved_at']='2027-01-01T00:00:00Z';variants.append(p)
        p=copy.deepcopy(BASE);p['current']['metadata']['family']='IEC 60268-5';p['current']['source']['content_sha256']=digest(p['current']['metadata']);variants.append(p)
        for p in variants:
            with self.subTest(p=p),self.assertRaises(ValueError):standard_metadata.analyze(p)


if __name__=='__main__':unittest.main()
