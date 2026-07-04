"""
REEL GOD — Dashboard Security Helpers
=====================================
Lightweight, dependency-free security utilities for the Flask dashboard:

* :class:`LoginRateLimiter` — a thread-safe, in-memory brute-force guard that
  temporarily locks out a client (by IP) after too many failed login attempts.
* :func:`ensure_secret_key` — upgrades the insecure placeholder session secret
  to a strong, persisted random key so cookies can't be forged.
* :func:`client_ip` — resolves the real client IP behind a reverse proxy.

Kept dependency-free on purpose (no flask-limiter) so it works everywhere and
adds no supply-chain surface.
"""

from __future__ import annotations

import os
import secrets
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict

from flask import Request


class LoginRateLimiter:
    """Per-IP sliding-window rate limiter with temporary lockout.

    Not a replacement for a real WAF, but it stops trivial password brute-force
    on a single-node deployment without any external dependencies.
    """

    def __init__(self, max_attempts: int, window_seconds: int, lockout_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: Dict[str, Deque[float]] = defaultdict(deque)
        self._locked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> None:
        window = self._attempts[key]
        while window and now - window[0] > self.window_seconds:
            window.popleft()

    def retry_after(self, key: str) -> int:
        """Seconds remaining on a lockout, or 0 if the key is not locked."""
        with self._lock:
            until = self._locked_until.get(key, 0.0)
            remaining = int(until - time.time())
            return max(0, remaining)

    def is_locked(self, key: str) -> bool:
        return self.retry_after(key) > 0

    def register_failure(self, key: str) -> int:
        """Record a failed attempt; returns seconds of lockout (0 if not locked)."""
        now = time.time()
        with self._lock:
            self._prune(key, now)
            self._attempts[key].append(now)
            if len(self._attempts[key]) >= self.max_attempts:
                self._locked_until[key] = now + self.lockout_seconds
                self._attempts[key].clear()
                return self.lockout_seconds
            return 0

    def register_success(self, key: str) -> None:
        """Clear all failure state for a key after a successful login."""
        with self._lock:
            self._attempts.pop(key, None)
            self._locked_until.pop(key, None)


def client_ip(request: Request) -> str:
    """Best-effort real client IP, honoring a single X-Forwarded-For hop."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def ensure_secret_key(current: str, insecure_default: str, env_path: Path) -> str:
    """Return a strong session secret, generating & persisting one if needed.

    If ``current`` is empty or still the shipped placeholder, a 256-bit random
    key is generated and written to ``.env`` (and the live environment) so it
    survives restarts. A real key supplied via the environment is used as-is.
    """
    if current and current != insecure_default:
        return current

    generated = secrets.token_hex(32)
    os.environ["DASHBOARD_SECRET_KEY"] = generated
    try:
        _persist_env_var(env_path, "DASHBOARD_SECRET_KEY", generated)
    except OSError:
        # If .env isn't writable (e.g. read-only container), the in-memory key
        # still secures this process; deployers should set the env var instead.
        pass
    return generated


def _persist_env_var(env_path: Path, key: str, value: str) -> None:
    """Idempotently write ``key=value`` into a .env file."""
    lines = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()

    out, replaced = [], False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    env_path.write_text("\n".join(out) + "\n")
