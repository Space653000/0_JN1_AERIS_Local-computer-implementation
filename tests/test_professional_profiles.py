import copy
import unittest
from unittest.mock import patch

from aeris_runtime.engineering import factory
from aeris_runtime.engineering import professional_profiles
from aeris_runtime.engineering.professional_profiles import profiles


class ProfessionalProfileTests(unittest.TestCase):
    def test_unknown_or_suffix_standards_family_fails_closed(self):
        for invalid in ('IEC 60268-99','IEC 60268-5-fake'):
            source=professional_profiles._AUTHORED.replace('IEC 60268-5',invalid,1)
            with patch.object(professional_profiles,'_AUTHORED',source):
                with self.assertRaisesRegex(ValueError,'unknown standards family'):
                    profiles()

    def test_packs_carry_authored_professional_distinctions_not_generic_scopes(self):
        expected=profiles()
        self.assertEqual(len({p['mission'] for p in expected.values()}),100)
        for role,profile in expected.items():
            with self.subTest(role=role):
                pack=factory.load_pack(role)
                self.assertEqual(pack['mission'],profile['mission'])
                self.assertEqual(pack['common_failure_modes'],profile['common_failure_modes'])
                self.assertEqual(pack['standards_metadata_references'],profile['standards_metadata_references'])
                self.assertEqual(pack['neighbor_distinctions'],profile['neighbor_distinctions'])
                self.assertTrue(pack['professional_decision_contract']['required_methods'])
        patent=factory.load_pack('R087')
        self.assertEqual(patent['standards_metadata_references'],[])
        self.assertIn('priority date',patent['common_failure_modes'][1])
        self.assertIn('FF/FB ANC',factory.load_pack('R048')['mission'])

    def test_empty_or_unrelated_skill_mapping_is_not_a_professional_contract(self):
        pack=factory.load_pack('R009')
        for skills in ([],['provenance-research']):
            modified=copy.deepcopy(pack); modified['required_skills']=skills
            self.assertTrue(factory.contract_errors(modified))
        for methods in ([],['methods/engineering/provenance-research.json']):
            modified=copy.deepcopy(pack); modified['required_methods']=methods
            self.assertTrue(factory.contract_errors(modified))


if __name__=='__main__': unittest.main()
