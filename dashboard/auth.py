"""
REEL GOD — Dashboard Authentication
===================================
Lightweight username + password account system backed by the project's SQLite
database. Passwords are stored as salted hashes (never plaintext), so the
dashboard is safe to expose on the public internet.

One shared workspace: every account can see and drive the same REEL GOD agent
(posts, ideas, schedule). This is intentional — it lets the commander log in
from a phone, laptop, or any device and reach the same content.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table (if missing) and seed the first admin account.

    The bootstrap admin is read from the ``COMMANDER_USERNAME`` /
    ``COMMANDER_PASSWORD`` env vars (defaults ``admin`` / ``admin``) and is only
    created when no accounts exist yet, so redeploys never clobber a real
    password the commander has already set.
    """
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

        count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if count == 0:
            username = os.environ.get("COMMANDER_USERNAME", "admin").strip() or "admin"
            password = os.environ.get("COMMANDER_PASSWORD", "admin")
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            conn.commit()


def user_count() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]


def verify_user(username: str, password: str) -> bool:
    """Return True when the username exists and the password matches its hash."""
    if not username or not password:
        return False
    with _connect() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
    return bool(row) and check_password_hash(row["password_hash"], password)


def create_user(username: str, password: str) -> tuple[bool, str]:
    """Create a new login. Returns (ok, message)."""
    username = (username or "").strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password or "") < 4:
        return False, "Password must be at least 4 characters."
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
        return True, f"Account '{username}' created."
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' is already taken."


def change_password(username: str, current_password: str, new_password: str) -> tuple[bool, str]:
    """Change a user's password after verifying the current one."""
    if not verify_user(username, current_password):
        return False, "Current password is incorrect."
    if len(new_password or "") < 4:
        return False, "New password must be at least 4 characters."
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (generate_password_hash(new_password), username.strip()),
        )
        conn.commit()
    return True, "Password updated."


def list_usernames() -> list[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY id").fetchall()
    return [r["username"] for r in rows]
