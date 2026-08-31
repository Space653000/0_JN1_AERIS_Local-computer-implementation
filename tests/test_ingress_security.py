import unittest
from unittest.mock import patch

from aeris_runtime.ingress import _assert_public_url, download_public_url
from aeris_runtime.config import MODE_FILE, set_persisted_mode


class IngressSecurityTests(unittest.TestCase):
    def tearDown(self):
        if MODE_FILE.exists():
            MODE_FILE.unlink()

    def test_loopback_is_denied(self):
        with patch("aeris_runtime.ingress.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 80))]):
            with self.assertRaises(ValueError):
                _assert_public_url("http://localhost/test")

    def test_private_lan_is_denied(self):
        with patch("aeris_runtime.ingress.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("192.168.1.10", 443))]):
            with self.assertRaises(ValueError):
                _assert_public_url("https://example.test/resource")

    def test_public_ip_is_allowed(self):
        with patch("aeris_runtime.ingress.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]):
            parsed = _assert_public_url("https://example.com/resource")
            self.assertEqual(parsed.scheme, "https")

    def test_offline_mode_blocks_external_ingress_before_network(self):
        set_persisted_mode("offline")
        with self.assertRaises(RuntimeError):
            download_public_url("https://example.com")


if __name__ == "__main__":
    unittest.main()
