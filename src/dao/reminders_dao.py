from dataclasses import dataclass
import asyncio
from src.services.database_manager import DatabaseManager


@dataclass(frozen=True)
class ReminderRow:
    id: int
    user_id: str
    label: str
    persona: str
    minute_of_day: int
    tz: str
    active: bool

from typing import List, Tuple, Optional

class RemindersDAO:
    def __init__(self, db):
        self.db = db

    async def ensure_user(self, user_id: str) -> None:
        def work(conn):
            conn.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
            conn.commit()
        await asyncio.to_thread(lambda: work(self.db.connection()))

    async def add_reminder(self, user_id: str, time_hhmm: str, label: str, persona: str, chat_id: int = 1) -> None:
        def work(conn):
            conn.execute(
                "INSERT INTO reminders(user_id, chat_id, label, persona, time_hhmm, active) "
                "VALUES(?,?,?,?,?,1)",
                (user_id, chat_id, label, persona, time_hhmm),
            )
            conn.commit()
        await asyncio.to_thread(lambda: work(self.db.connection()))

    async def list_reminders(self, user_id: str, chat_id: int = 1) -> List[Tuple[str, str, str]]:
        def work(conn):
            cur = conn.execute(
                "SELECT time_hhmm, label, persona "
                "FROM reminders WHERE user_id=? AND chat_id=? AND active=1 "
                "ORDER BY time_hhmm, label",
                (user_id, chat_id),
            )
            return [(r["time_hhmm"], r["label"], r["persona"]) for r in cur.fetchall()]
        return await asyncio.to_thread(lambda: work(self.db.connection()))

    async def delete_reminder(self, user_id: str, time_hhmm: str, label: str, chat_id: int = 1) -> int:
        def work(conn):
            cur = conn.execute(
                "DELETE FROM reminders WHERE user_id=? AND chat_id=? AND time_hhmm=? AND label=?",
                (user_id, chat_id, time_hhmm, label),
            )
            conn.commit()
            return cur.rowcount
        return await asyncio.to_thread(lambda: work(self.db.connection()))

    # NEW: exact-minute lookup (prevents duplicates with every-minute loop)
    async def due_at_minute(self, hhmm: str, chat_id: int = 1) -> List[Tuple[str, str, str]]:
        def work(conn):
            cur = conn.execute(
                "SELECT user_id, persona, label "
                "FROM reminders WHERE active=1 AND chat_id=? AND time_hhmm=?",
                (chat_id, hhmm),
            )
            return [(r["user_id"], r["persona"], r["label"]) for r in cur.fetchall()]
        return await asyncio.to_thread(lambda: work(self.db.connection()))