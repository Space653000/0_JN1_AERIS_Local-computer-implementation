"""Multi-user login: one owner plus owner-granted accounts scoped to
specific pages/actions, credential storage, sessions, and permissions."""
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

    def test_set_and_verify_owner_credentials_roundtrip(self):
        auth.set_credentials("owner", "correct-horse-battery")
        self.assertTrue(auth.has_credentials())
        self.assertTrue(auth.verify_credentials("owner", "correct-horse-battery"))
        self.assertFalse(auth.verify_credentials("owner", "wrong-password"))
        self.assertFalse(auth.verify_credentials("someone-else", "correct-horse-battery"))

    def test_owner_has_every_permission_including_admin(self):
        auth.set_credentials("owner", "correct-horse-battery")
        role, permissions = auth.user_permissions("owner")
        self.assertEqual(role, "owner")
        self.assertIn("admin", permissions)
        for scope in auth.GRANTABLE_PERMISSIONS:
            self.assertIn(scope, permissions)
        self.assertTrue(auth.has_permission("owner", "admin"))

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

    def test_setting_new_owner_credentials_wipes_all_accounts_and_sessions(self):
        auth.set_credentials("owner", "first-password-1234")
        auth.grant_user("helper", "helper-password-1", ["dashboard"])
        token = auth.create_session("owner")
        self.assertTrue(auth.verify_session(token))
        auth.set_credentials("owner", "second-password-5678")
        self.assertFalse(auth.verify_session(token))
        self.assertEqual([u["username"] for u in auth.list_users()], ["owner"])

    def test_session_lifecycle(self):
        auth.set_credentials("owner", "correct-horse-battery")
        token = auth.create_session("owner")
        self.assertTrue(auth.verify_session(token))
        self.assertEqual(auth.session_username(token), "owner")
        auth.revoke_session(token)
        self.assertFalse(auth.verify_session(token))

    def test_unknown_or_missing_session_token_is_not_authenticated(self):
        self.assertFalse(auth.verify_session(None))
        self.assertFalse(auth.verify_session("not-a-real-token"))

    def test_expired_session_is_not_authenticated(self):
        token = auth.create_session("owner")
        with patch.object(auth, "_sessions", {token: {"username": "owner", "expires_at": -1.0}}):
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

    # -- multi-user / permission model --------------------------------

    def test_grant_user_creates_scoped_account(self):
        auth.set_credentials("owner", "owner-password-123")
        auth.grant_user("viewer", "viewer-password-1", ["dashboard", "progress"])
        self.assertTrue(auth.verify_credentials("viewer", "viewer-password-1"))
        role, permissions = auth.user_permissions("viewer")
        self.assertEqual(role, "granted")
        self.assertEqual(sorted(permissions), ["dashboard", "progress"])
        self.assertTrue(auth.has_permission("viewer", "dashboard"))
        self.assertFalse(auth.has_permission("viewer", "services"))
        self.assertFalse(auth.has_permission("viewer", "admin"))

    def test_granted_account_can_never_hold_admin(self):
        auth.set_credentials("owner", "owner-password-123")
        with self.assertRaises(ValueError):
            auth.grant_user("wannabe-admin", "password-1234", ["admin"])

    def test_grant_user_rejects_short_password(self):
        auth.set_credentials("owner", "owner-password-123")
        with self.assertRaises(ValueError):
            auth.grant_user("viewer", "short", ["dashboard"])

    def test_grant_user_cannot_overwrite_owner(self):
        auth.set_credentials("owner", "owner-password-123")
        with self.assertRaises(ValueError):
            auth.grant_user("owner", "new-password-1234", ["dashboard"])

    def test_revoke_user_removes_account_and_its_sessions(self):
        auth.set_credentials("owner", "owner-password-123")
        auth.grant_user("viewer", "viewer-password-1", ["dashboard"])
        token = auth.create_session("viewer")
        self.assertTrue(auth.verify_session(token))
        auth.revoke_user("viewer")
        self.assertFalse(auth.verify_session(token))
        self.assertFalse(auth.verify_credentials("viewer", "viewer-password-1"))

    def test_revoke_user_cannot_remove_owner(self):
        auth.set_credentials("owner", "owner-password-123")
        with self.assertRaises(ValueError):
            auth.revoke_user("owner")

    def test_revoke_unknown_user_raises(self):
        auth.set_credentials("owner", "owner-password-123")
        with self.assertRaises(ValueError):
            auth.revoke_user("nobody")

    def test_list_users_excludes_password_hashes(self):
        auth.set_credentials("owner", "owner-password-123")
        auth.grant_user("viewer", "viewer-password-1", ["dashboard"])
        users = auth.list_users()
        self.assertEqual(len(users), 2)
        for user in users:
            self.assertNotIn("hash_b64", user)
            self.assertNotIn("salt_b64", user)

    def test_legacy_single_owner_file_migrates_transparently(self):
        import base64
        import hashlib
        import json
        salt = b"0123456789abcdef"
        digest = hashlib.pbkdf2_hmac("sha256", b"legacy-password-1", salt, auth.PBKDF2_ITERATIONS)
        legacy = {
            "schema_version": 1, "username": "legacy-owner",
            "salt_b64": base64.b64encode(salt).decode("ascii"),
            "hash_b64": base64.b64encode(digest).decode("ascii"),
            "iterations": auth.PBKDF2_ITERATIONS,
        }
        auth.CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        auth.CREDENTIALS_PATH.write_text(json.dumps(legacy), encoding="utf-8")
        self.assertTrue(auth.verify_credentials("legacy-owner", "legacy-password-1"))
        role, permissions = auth.user_permissions("legacy-owner")
        self.assertEqual(role, "owner")
        self.assertIn("admin", permissions)

    def test_unknown_user_has_no_permissions(self):
        self.assertIsNone(auth.user_permissions("nobody"))
        self.assertFalse(auth.has_permission("nobody", "dashboard"))


if __name__ == "__main__":
    unittest.main()
