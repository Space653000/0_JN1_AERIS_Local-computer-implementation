import unittest
from aeris_runtime.privacy import CloudEgressDenied, CloudRequestPolicy, assert_cloud_safe

class PrivacyTests(unittest.TestCase):
    def test_public_research_without_local_context_is_allowed(self): assert_cloud_safe(CloudRequestPolicy(workload="public_research"))
    def test_memory_attachment_is_denied(self):
        with self.assertRaises(CloudEgressDenied): assert_cloud_safe(CloudRequestPolicy(workload="public_research",attach_memory=True))
    def test_private_engineering_cloud_is_denied(self):
        with self.assertRaises(CloudEgressDenied): assert_cloud_safe(CloudRequestPolicy(workload="private_engineering"))

if __name__=="__main__": unittest.main()
