import unittest
from aeris_runtime.privacy import (
    CloudEgressDenied,
    CloudRequestPolicy,
    assert_cloud_safe,
    assert_public_query_content_safe,
    public_query_risk_reasons,
)


class PrivacyTests(unittest.TestCase):
    def test_public_research_without_local_context_is_allowed(self):
        assert_cloud_safe(CloudRequestPolicy(workload="public_research"))

    def test_memory_attachment_is_denied(self):
        with self.assertRaises(CloudEgressDenied):
            assert_cloud_safe(CloudRequestPolicy(workload="public_research", attach_memory=True))

    def test_private_engineering_cloud_is_denied(self):
        with self.assertRaises(CloudEgressDenied):
            assert_cloud_safe(CloudRequestPolicy(workload="private_engineering"))

    def test_secret_like_public_query_is_denied(self):
        with self.assertRaises(CloudEgressDenied):
            assert_public_query_content_safe("api_key=super-secret-value-123456")

    def test_confidential_marker_is_denied(self):
        with self.assertRaises(CloudEgressDenied):
            assert_public_query_content_safe("客戶機密：請分析這段資料")

    def test_normal_public_query_has_no_risk_reason(self):
        self.assertEqual(public_query_risk_reasons("What is the public IEC publication status?"), [])


if __name__ == "__main__":
    unittest.main()
