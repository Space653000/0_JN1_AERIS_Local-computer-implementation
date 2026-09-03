import unittest
import copy

from aeris_runtime.engineering.api import get
from aeris_runtime.engineering import factory
from aeris_runtime.engineering.knowledge_registry import summary


class KnowledgeClassificationTests(unittest.TestCase):
    def test_authored_synthetic_notes_are_not_external_professional_documents(self):
        result=get('/api/v1/capabilities/knowledge')
        self.assertEqual(result['documents'],204)
        self.assertEqual(result['counts_by_source_kind']['PUBLIC_EXTERNAL'],0)
        self.assertEqual(result['counts_by_source_kind']['SYNTHETIC'],84)
        self.assertEqual(result['counts_by_source_kind']['GENERATED_DERIVATION'],42)
        self.assertEqual(result['external_retrieved_documents'],0)
        self.assertEqual(sum(result['counts_by_source_kind'].values()),result['documents'])
        for document in result['source_registry']:
            self.assertFalse(document['is_evidence'])
            self.assertEqual(len(document['sha256']),64)
            self.assertIsNone(document['retrieved_at_utc'])
            self.assertEqual(document['retrieval_state'],'NOT_RETRIEVED_EXTERNALLY')

    def test_note_tamper_and_manifest_drift_fail_closed(self):
        original=factory.read(factory.ROOT/'knowledge/engineering/manifest.json')
        corpus=copy.deepcopy(original); corpus['documents'][0]['text']='forged'
        with self.assertRaisesRegex(ValueError,'hash mismatch'): summary(corpus)
        corpus=copy.deepcopy(original); corpus['documents'].append(corpus['documents'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'): summary(corpus)
        corpus=copy.deepcopy(original); corpus['documents'][0]['id']='../../.aeris/private'
        with self.assertRaisesRegex(ValueError,'unsafe'): summary(corpus)


if __name__=='__main__': unittest.main()
