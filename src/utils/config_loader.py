import os
import logging
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self):
        load_dotenv()

        self._discord_token = os.getenv("DISCORD_BOT_TOKEN")
        self._default_timezone = os.getenv("DEFAULT_TIMEZONE", "America/New_York")

        # SQLite (optional; has a sensible default)
        self._sqlite_path = os.getenv("SQLITE_DB_PATH", os.path.join("database", "reminders.db"))

        if not self._discord_token:
            raise RuntimeError("DISCORD_BOT_TOKEN is missing in environment (.env).")

        # Optional notice
        os.makedirs(os.path.dirname(self._sqlite_path), exist_ok=True)
        logging.info("Using SQLite DB at %s", os.path.abspath(self._sqlite_path))

    def get_discord_token(self) -> str:
        return self._discord_token

    def get_default_timezone(self) -> str:
        return self._default_timezone

    def get_sqlite_path(self) -> str:
        return self._sqlite_path
