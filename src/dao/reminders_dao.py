from __future__ import annotations

import asyncio
from typing import List, Tuple


class RemindersDAO:
    """
    SQLite DAO for reminders.

    Expects DatabaseManager to expose:
      - connection() -> sqlite3.Connection
    and to have row_factory set to sqlite3.Row so dict-style access works.
    """

    def __init__(self, db):
        self.db = db

    # ------------------------- users -------------------------

    async def ensure_user(self, user_id: str) -> None:
        def work(conn):
            conn.execute(
                "INSERT OR IGNORE INTO users(user_id) VALUES(?)",
                (user_id,),
            )
            conn.commit()

        await asyncio.to_thread(lambda: work(self.db.connection()))

    # ----------------------- reminders -----------------------

    async def add_reminder(
        self,
        user_id: str,
        time_hhmm: str,
        label: str,
        persona: str,
        chat_id: int = 1,
    ) -> None:
        def work(conn):
            conn.execute(
                """
                INSERT INTO reminders(user_id, chat_id, label, persona, time_hhmm, active)
                VALUES(?,?,?,?,?,1)
                """,
                (user_id, chat_id, label, persona, time_hhmm),
            )
            conn.commit()

        await asyncio.to_thread(lambda: work(self.db.connection()))

    async def list_reminders(
        self,
        user_id: str,
        chat_id: int = 1,
    ) -> List[Tuple[str, str, str]]:
        """
        Returns: [(time_hhmm, label, persona), ...]
        """
        def work(conn):
            cur = conn.execute(
                """
                SELECT time_hhmm, label, persona
                FROM reminders
                WHERE user_id=? AND chat_id=? AND active=1
                ORDER BY time_hhmm, label
                """,
                (user_id, chat_id),
            )
            return [(r["time_hhmm"], r["label"], r["persona"]) for r in cur.fetchall()]

        return await asyncio.to_thread(lambda: work(self.db.connection()))

    async def delete_reminder(
        self,
        user_id: str,
        time_hhmm: str,
        label: str,
        chat_id: int = 1,
    ) -> int:
        """
        Returns number of rows deleted (0 or 1).
        """
        def work(conn):
            cur = conn.execute(
                """
                DELETE FROM reminders
                WHERE user_id=? AND chat_id=? AND time_hhmm=? AND label=?
                """,
                (user_id, chat_id, time_hhmm, label),
            )
            conn.commit()
            return cur.rowcount

        return await asyncio.to_thread(lambda: work(self.db.connection()))

    async def due_at_minute(
        self,
        hhmm: str,
        chat_id: int = 1,
    ) -> List[Tuple[str, str, str]]:
        """
        Returns reminders due exactly at hhmm for the given chat_id.
        Output: [(user_id, persona, label), ...]
        """
        def work(conn):
            cur = conn.execute(
                """
                SELECT user_id, persona, label
                FROM reminders
                WHERE active=1 AND chat_id=? AND time_hhmm=?
                """,
                (chat_id, hhmm),
            )
            return [(r["user_id"], r["persona"], r["label"]) for r in cur.fetchall()]

        return await asyncio.to_thread(lambda: work(self.db.connection()))
