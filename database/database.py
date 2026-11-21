import os
import sqlite3
from datetime import datetime, timezone


class EmailHistoryDB:
    def __init__(self, db_path: str = "email_history.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS email_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    recipient TEXT,
                    subject TEXT,
                    email_body TEXT,
                    tone TEXT,
                    created_time TEXT,
                    status TEXT,
                    gmail_draft_id TEXT
                )
                """
            )

    def save_email(self, user_id: str, recipient: str, subject: str, body: str, tone: str, status: str, draft_id: str = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO email_history (user_id, recipient, subject, email_body, tone, created_time, status, gmail_draft_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    recipient,
                    subject,
                    body,
                    tone,
                    datetime.now(timezone.utc).isoformat(),
                    status,
                    draft_id,
                ),
            )

    def get_history(self, user_id: str = None, limit: int = 20):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if user_id:
                rows = conn.execute(
                    "SELECT * FROM email_history WHERE user_id = ? ORDER BY created_time DESC LIMIT ?",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM email_history ORDER BY created_time DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]
