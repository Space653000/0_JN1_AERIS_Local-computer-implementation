"""Single-owner login: credential storage, verification, and session
lifecycle for the local control plane."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.patcher = patch.object(auth, "CREDENTIALS_PATH", self.tmp / "auth_credentials.json")
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(auth._sessions.clear)
        self.addCleanup(auth._failed_attempts.clear)

    def test_no_credentials_configured_by_default(self):
        self.assertFalse(auth.has_credentials())
        self.assertFalse(auth.verify_credentials("owner", "whatever12"))

    def test_set_and_verify_credentials_roundtrip(self):
        auth.set_credentials("owner", "correct-horse-battery")
        self.assertTrue(auth.has_credentials())
        self.assertTrue(auth.verify_credentials("owner", "correct-horse-battery"))
        self.assertFalse(auth.verify_credentials("owner", "wrong-password"))
        self.assertFalse(auth.verify_credentials("someone-else", "correct-horse-battery"))

    def test_password_is_never_stored_in_plaintext(self):
        auth.set_credentials("owner", "correct-horse-battery")
        raw = auth.CREDENTIALS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("correct-horse-battery", raw)

    def test_short_password_rejected(self):
        with self.assertRaises(ValueError):
            auth.set_credentials("owner", "short")

    def test_empty_username_rejected(self):
        with self.assertRaises(ValueError):
            auth.set_credentials("   ", "longenoughpassword")

    def test_setting_new_credentials_invalidates_existing_sessions(self):
        auth.set_credentials("owner", "first-password-1234")
        token = auth.create_session()
        self.assertTrue(auth.verify_session(token))
        auth.set_credentials("owner", "second-password-5678")
        self.assertFalse(auth.verify_session(token))

    def test_session_lifecycle(self):
        token = auth.create_session()
        self.assertTrue(auth.verify_session(token))
        auth.revoke_session(token)
        self.assertFalse(auth.verify_session(token))

    def test_unknown_or_missing_session_token_is_not_authenticated(self):
        self.assertFalse(auth.verify_session(None))
        self.assertFalse(auth.verify_session("not-a-real-token"))

    def test_expired_session_is_not_authenticated(self):
        token = auth.create_session()
        with patch.object(auth, "_sessions", {token: -1.0}):
            self.assertFalse(auth.verify_session(token))

    def test_lockout_after_repeated_failed_attempts(self):
        auth.set_credentials("owner", "correct-horse-battery")
        for _ in range(auth.MAX_FAILED_ATTEMPTS):
            self.assertFalse(auth.verify_credentials("owner", "wrong"))
        # Even the correct password is now refused during the lockout window.
        self.assertFalse(auth.verify_credentials("owner", "correct-horse-battery"))

    def test_parse_cookie(self):
        self.assertEqual(auth.parse_cookie("aeris_session=abc123; other=x", "aeris_session"), "abc123")
        self.assertIsNone(auth.parse_cookie("other=x", "aeris_session"))
        self.assertIsNone(auth.parse_cookie(None, "aeris_session"))


if __name__ == "__main__":
    unittest.main()
