import unittest
from unittest.mock import patch
from aeris_runtime.config import ROOT
from aeris_runtime.deployment_admission import admit


class DeploymentAdmissionTests(unittest.TestCase):
    def test_local_install_fails_closed_even_with_ci_flag(self):
        with self.assertRaisesRegex(ValueError,'forbids runtime'):
            admit(ROOT,ci_smoke=True,environment={})

    def test_normal_install_not_authorized_by_candidate(self):
        with self.assertRaisesRegex(ValueError,'forbids runtime'):
            admit(ROOT,environment={})

    def test_mixed_pointer_blocks_before_ci_exception(self):
        with patch('aeris_runtime.deployment_admission.validate',side_effect=ValueError('mixed Core')):
            with self.assertRaisesRegex(ValueError,'mixed Core'):
                admit(ROOT,ci_smoke=True,environment={'GITHUB_ACTIONS':'true'})
