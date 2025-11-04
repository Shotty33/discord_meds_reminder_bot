from __future__ import annotations

import asyncio
from typing import List, Tuple
from datetime import datetime, timedelta
import re

import pytz

from src.dao.reminders_dao import RemindersDAO, ReminderRow

TIME_24H = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")  # HH:MM

def hhmm_to_minute_of_day(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m

def minute_of_day_to_hhmm(n: int) -> str:
    return f"{n // 60:02d}:{n % 60:02d}"

class RemindersManager:
    def __init__(self, dao, default_tz: str = "America/New_York", chat_id: int = 1):
        self.dao = dao
        self.default_tz = default_tz
        self.chat_id = chat_id

    async def create_reminder(self, user_id: str, persona: str, time_str: str, label: str):
        await self.dao.ensure_user(user_id)
        await self.dao.add_reminder(user_id, time_str, label, persona, chat_id=self.chat_id)
        return True, f"✅ Added `{label}` at `{time_str}` ({persona})."

    async def get_reminders(self, user_id: str):
        rows: List[Tuple[str, str, str]] = await self.dao.list_reminders(user_id, chat_id=self.chat_id)
        if not rows:
            return True, "You have no reminders yet. Use `!r` to create one."
        lines = []
        for time_hhmm, label, persona in rows:
            lines.append(f"- `{time_hhmm}` — **{label}** ({persona})")
        return True, "Your reminders:\n" + "\n".join(lines)

    async def delete_reminder(self, user_id: str, time_str: str, label: str):
        deleted = await self.dao.delete_reminder(user_id, time_str, label, chat_id=self.chat_id)
        if deleted:
            return True, f"🗑️ Deleted `{label}` at `{time_str}`."
        return False, f"Couldn't find `{label}` at `{time_str}`."

    # NEW: minute-precision fetch (prevents duplicate sends)
    async def get_due_at_minute(self, hhmm: str):
        """
        Returns: List[(user_id, persona, label, send_at_datetime)]
        """
        rows = await self.dao.due_at_minute(hhmm, chat_id=self.chat_id)
        tz = pytz.timezone(self.default_tz)
        now = datetime.now(tz).replace(second=0, microsecond=0)
        out = []
        for user_id, persona, label in rows:
            out.append((user_id, persona, label, now))
        return out
