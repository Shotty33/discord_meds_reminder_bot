import datetime
from typing import List, Dict, Tuple

from src.utils.config_loader import ConfigLoader
from database_manager import DatabaseManager
from src.bot import logger


class RemindersManager:
    """
    Orchestrates reminder behavior for a user.

    This class is the 'application logic layer' / internal API for the bot.
    - Validates user input (time format, etc.)
    - Talks to the persistence layer (DatabaseManager)
    - Returns user-facing messages back to the caller (bot or other interface)

    It does NOT:
    - talk to Discord directly
    - schedule jobs
    - send DMs

    """

    def __init__(self, config: ConfigLoader, db: DatabaseManager):
        """
        Dependency injection:
        - config: provides environment / defaults (timezone, etc.)
        - db: provides Firestore persistence
        """
        self.config = config
        self.db = db

    # ------------------------
    # internal helpers
    # ------------------------
    def _validate_time_string(self, reminder_time_str: str) -> bool:
        """
        Return True if reminder_time_str is HH:MM in 24-hour format.
        """
        try:
            datetime.datetime.strptime(reminder_time_str, "%H:%M")
            return True
        except ValueError:
            return False

    # ------------------------
    # public API
    # ------------------------
    def create_reminder(
            self,
            user_id: str,
            persona: str,
            time_str: str,
            label: str,
    ) -> Tuple[bool, str]:
        """
        Create (append) a new reminder for the given Discord user.

        Returns:
            (success, message)
            - success: bool
            - message: safe-to-send string for the caller (Discord layer, etc.)
        """

        # Validate time string
        if not self._validate_time_string(time_str):
            return False, "Invalid time format. Please use 24-hour HH:MM like `08:00`."

        # Attempt persistence
        try:
            self.db.add_reminder(
                user_id=user_id,
                label=label,
                reminder_time=time_str,
                persona=persona,
                timezone=self.config.get_default_timezone(),
            )
        except Exception as e:
            logger.exception("[RemindersManager] create_reminder failed")
            return (
                False,
                f"Something went wrong saving your reminder: {e}"
            )

        # Success message back to caller
        return (
            True,
            f"Sweet. `{persona}` will remind you at {time_str} to `{label}`."
        )

    def get_reminders(self, user_id: str) -> Tuple[bool, str]:
        """
        Fetch all active reminders for the given user and format them.
        Returns:
            (success, message)
        """

        try:
            reminders = self.db.list_reminders(user_id)
        except Exception as e:
            logger.exception("[RemindersManager] get_reminders failed")
            return (
                False,
                f"Couldn't load your reminders: {e}"
            )

        if not reminders:
            return True, "You don't have any active reminders."

        lines: List[str] = []
        for r in reminders:
            time_str = r.get("time", "??:??")
            label = r.get("label", "<?>")
            persona = r.get("persona", "<?>")
            lines.append(f"- {time_str} :: {label} [{persona}]")

        return True, "\n".join(lines)

    def delete_reminder(self, user_id: str, time_str: str, label: str) -> Tuple[bool, str]:
        """
        Delete a reminder for the user. Matching is done on (time, label).
        Returns:
            (success, message)
        """

        # Validate before touching DB
        if not self._validate_time_string(time_str):
            return False, "Time must be HH:MM in 24-hour format, like `08:00`."

        try:
            deleted = self.db.delete_reminder(user_id, label, time_str)
        except Exception as e:
            logger.exception("[RemindersManager] delete_reminder failed")
            return (
                False,
                f"Couldn't delete that reminder: {e}"
            )

        if deleted:
            return True, f"Deleted reminder `{label}` at {time_str}."
        else:
            return False, "I couldn't find a matching reminder to delete."
