# src/services/reminders_manager.py
from __future__ import annotations

import re
import logging
from datetime import datetime
from typing import List, Tuple, Optional
import pytz

from src.services.ai_manager import AIManager

logger = logging.getLogger(__name__)

# HH:MM 24h
TIME_24H = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class RemindersManager:
    def __init__(self, dao, default_tz: str = "America/New_York", chat_id: int = 1, config=None):
        self.dao = dao
        self.default_tz = default_tz
        self.chat_id = chat_id
        self.ai = AIManager(config=config)  # AI uses your config

    # ---------- helpers ----------
    @staticmethod
    def _validate_time_hhmm(time_str: str) -> Optional[str]:
        ts = (time_str or "").strip()
        if not ts or not TIME_24H.match(ts):
            return None
        h, m = ts.split(":")
        return f"{int(h):02d}:{int(m):02d}"

    # ---------- CRUD ----------
    async def create_reminder(self, user_id: str, persona: str, time_str: str, label: str):
        t = self._validate_time_hhmm(time_str)
        if not t:
            return False, "Time must be HH:MM in 24-hour format (e.g., 08:00, 21:30)."

        await self.dao.ensure_user(user_id)
        await self.dao.add_reminder(user_id, t, label, persona, chat_id=self.chat_id)
        return True, f"✅ Added `{label}` at `{t}` ({persona})."

    async def get_reminders(self, user_id: str):
        rows: List[Tuple[str, str, str]] = await self.dao.list_reminders(user_id, chat_id=self.chat_id)
        if not rows:
            return True, "You have no reminders yet. Use `!r` to create one."
        lines = [f"- `{t}` — **{label}** ({persona})" for (t, label, persona) in rows]
        return True, "Your reminders:\n" + "\n".join(lines)

    async def delete_reminder(self, user_id: str, time_str: str, label: str):
        t = self._validate_time_hhmm(time_str)
        if not t:
            return False, "Time must be HH:MM in 24-hour format."
        deleted = await self.dao.delete_reminder(user_id, t, label, chat_id=self.chat_id)
        if deleted:
            return True, f"🗑️ Deleted `{label}` at `{t}`."
        return False, f"Couldn't find `{label}` at `{t}`."

    # ---------- minute-precision fetch for the dispatcher ----------
    async def get_due_at_minute(self, hhmm: str) -> List[Tuple[str, str, str, datetime]]:
        """
        Returns: List[(user_id, persona, label, send_at_datetime)]
        """
        t = self._validate_time_hhmm(hhmm)
        if not t:
            return []
        rows = await self.dao.due_at_minute(t, chat_id=self.chat_id)  # [(user_id, persona, label)]
        tz = pytz.timezone(self.default_tz)
        send_at = datetime.now(tz).replace(second=0, microsecond=0)
        return [(user_id, persona, label, send_at) for (user_id, persona, label) in rows]

    # ---------- AI rendering ----------
    async def render_message(self, persona: str, label: str, user_name: Optional[str] = None) -> str:
        """
        Ask AIManager to generate the one-line persona reminder,
        then append signature formatting handled in AIManager.
        """
        return await self.ai.generate(persona=persona, label=label, user_name=user_name)
