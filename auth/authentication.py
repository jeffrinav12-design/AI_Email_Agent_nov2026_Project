import hashlib
import os
import sqlite3
from datetime import datetime, timezone


class UserAuthManager:
    def __init__(self, db_path: str = "email_history.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TEXT,
                    gmail_account TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_gmail_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    gmail_account TEXT,
                    token_path TEXT,
                    created_at TEXT,
                    UNIQUE(user_id, gmail_account)
                )
                """
            )

    def register_user(self, username: str, password: str):
        if not username or not password:
            raise ValueError("Username and password are required.")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO users (username, password_hash, created_at, gmail_account) VALUES (?, ?, ?, ?)",
                    (username, password_hash, datetime.now(timezone.utc).isoformat(), None),
                )
            except sqlite3.IntegrityError:
                raise ValueError("Username already exists.")

    def login_user(self, username: str, password: str):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash),
            ).fetchone()
        if not row:
            raise ValueError("Invalid username or password.")
        return dict(row)

    def set_gmail_account(self, user_id: int, gmail_account: str, token_path: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_gmail_tokens (user_id, gmail_account, token_path, created_at) VALUES (?, ?, ?, ?)",
                (user_id, gmail_account, token_path, datetime.now(timezone.utc).isoformat()),
            )
            conn.execute(
                "UPDATE users SET gmail_account = ? WHERE id = ?",
                (gmail_account, user_id),
            )

    def get_user_gmail_accounts(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT gmail_account, token_path FROM user_gmail_tokens WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_user_by_id(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
