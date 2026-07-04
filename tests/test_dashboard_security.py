"""
REEL GOD — Dashboard Security & Error-Handling Test Suite
=========================================================
Covers the hardening pass: login rate-limiting, session-secret generation,
username/password validation, JSON error handlers, and the health endpoint.

Run with:  python -m unittest tests.test_dashboard_security
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Adjust python path to find project modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import config
from dashboard import auth, security


class LoginRateLimiterTests(unittest.TestCase):
    def test_locks_out_after_max_attempts(self):
        rl = security.LoginRateLimiter(max_attempts=3, window_seconds=60, lockout_seconds=120)
        ip = "10.0.0.1"
        self.assertFalse(rl.is_locked(ip))
        self.assertEqual(rl.register_failure(ip), 0)
        self.assertEqual(rl.register_failure(ip), 0)
        self.assertEqual(rl.register_failure(ip), 120)  # third failure trips lockout
        self.assertTrue(rl.is_locked(ip))
        self.assertGreater(rl.retry_after(ip), 0)

    def test_success_clears_failures(self):
        rl = security.LoginRateLimiter(3, 60, 120)
        ip = "10.0.0.2"
        rl.register_failure(ip)
        rl.register_success(ip)
        self.assertFalse(rl.is_locked(ip))
        # Counter reset, so a single new failure must not lock.
        self.assertEqual(rl.register_failure(ip), 0)

    def test_isolated_per_ip(self):
        rl = security.LoginRateLimiter(2, 60, 60)
        rl.register_failure("1.1.1.1")
        rl.register_failure("1.1.1.1")
        self.assertTrue(rl.is_locked("1.1.1.1"))
        self.assertFalse(rl.is_locked("2.2.2.2"))


class SecretKeyTests(unittest.TestCase):
    def test_generates_and_persists_when_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            envp = Path(d) / ".env"
            placeholder = "reel-god-secret-key-change-this"
            key = security.ensure_secret_key(placeholder, placeholder, envp)
            self.assertNotEqual(key, placeholder)
            self.assertGreaterEqual(len(key), 32)
            self.assertIn("DASHBOARD_SECRET_KEY=", envp.read_text())

    def test_keeps_explicit_key(self):
        with tempfile.TemporaryDirectory() as d:
            envp = Path(d) / ".env"
            key = security.ensure_secret_key("a-real-strong-key", "placeholder", envp)
            self.assertEqual(key, "a-real-strong-key")
            self.assertFalse(envp.exists())


class CredentialValidationTests(unittest.TestCase):
    def test_username_rules(self):
        ok, _ = auth._validate_credentials("ab", "longenough")
        self.assertFalse(ok)  # too short
        ok, _ = auth._validate_credentials("has space", "longenough")
        self.assertFalse(ok)  # invalid char
        ok, _ = auth._validate_credentials("good.user-1", "longenough")
        self.assertTrue(ok)

    def test_password_min_length(self):
        short = "x" * (config.MIN_PASSWORD_LENGTH - 1)
        ok, msg = auth._validate_credentials("validuser", short)
        self.assertFalse(ok)
        self.assertIn(str(config.MIN_PASSWORD_LENGTH), msg)


class AppEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dashboard import app as dash_app
        dash_app.app.config["TESTING"] = True
        cls.client = dash_app.app.test_client()

    def test_healthz_is_public(self):
        r = self.client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_api_requires_auth_json(self):
        r = self.client.get("/api/ideas/pending")
        self.assertEqual(r.status_code, 401)
        self.assertFalse(r.get_json()["success"])

    def test_unknown_api_returns_json_404(self):
        r = self.client.get("/api/does-not-exist")
        self.assertEqual(r.status_code, 404)
        self.assertFalse(r.get_json()["success"])

    def test_wrong_login_shows_message(self):
        r = self.client.post("/login", data={"username": "nobody", "password": "nope"})
        self.assertIn(b"Invalid username or password", r.data)


if __name__ == "__main__":
    unittest.main()
