import unittest

from aeris_runtime.providers import ProviderError, assert_private_local_endpoint


class LocalEndpointPolicyTests(unittest.TestCase):
    def test_loopback_accepts_localhost_and_loopback_ip(self):
        assert_private_local_endpoint("http://localhost:11434", "loopback")
        assert_private_local_endpoint("http://127.0.0.1:11434", "loopback")
        assert_private_local_endpoint("http://[::1]:11434", "loopback")

    def test_loopback_rejects_private_lan(self):
        with self.assertRaises(ProviderError):
            assert_private_local_endpoint("http://192.168.1.20:11434", "loopback")

    def test_trusted_lan_accepts_literal_rfc1918_and_ula(self):
        assert_private_local_endpoint("http://10.0.0.8:11434", "trusted_lan")
        assert_private_local_endpoint("http://172.16.5.9:11434", "trusted_lan")
        assert_private_local_endpoint("http://192.168.10.7:11434", "trusted_lan")
        assert_private_local_endpoint("http://[fd00::10]:11434", "trusted_lan")

    def test_public_ip_is_never_private_provider(self):
        for scope in ("loopback", "trusted_lan"):
            with self.subTest(scope=scope):
                with self.assertRaises(ProviderError):
                    assert_private_local_endpoint("https://8.8.8.8:11434", scope)

    def test_arbitrary_hostname_is_denied_even_in_trusted_lan(self):
        with self.assertRaises(ProviderError):
            assert_private_local_endpoint("http://ollama.internal.example:11434", "trusted_lan")

    def test_embedded_credentials_are_denied(self):
        with self.assertRaises(ProviderError):
            assert_private_local_endpoint("http://user:pass@127.0.0.1:11434", "loopback")

    def test_invalid_scope_is_denied(self):
        with self.assertRaises(ProviderError):
            assert_private_local_endpoint("http://127.0.0.1:11434", "anything")


if __name__ == "__main__":
    unittest.main()
