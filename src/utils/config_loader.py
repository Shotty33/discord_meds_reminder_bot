import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self):
        # Load .env from project root (one level above src/)
        # Adjust the relative path if your .env lives elsewhere.
        root = Path(__file__).resolve().parents[2]  # project root
        env_path = root / ".env"
        load_dotenv(dotenv_path=env_path)

        # ---- Discord ----
        self._discord_token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")

        # ---- SQLite paths ----
        self._sqlite_db_path = os.getenv("SQLITE_DB_PATH", str(root / "src" / "database" / "reminders.db"))
        self._schema_path   = os.getenv("SQLITE_SCHEMA_PATH", str(root / "src" / "database" / "schema.sql"))

        # ---- Timezone ----
        self._default_timezone = os.getenv("DEFAULT_TIMEZONE", "America/New_York")

        # ---- AI ----
        self._ai_provider = os.getenv("AI_PROVIDER", "none")
        self._ai_model = os.getenv("AI_MODEL", "mistral")
        self._ai_ollama_host = os.getenv("AI_OLLAMA_HOST", "http://127.0.0.1:11434")
        self._ai_enabled = self._parse_bool(os.getenv("AI_ENABLED", "false"))

        logger.info(
            "AI config: provider=%s model=%s mock=%s host=%s",
            self._ai_provider, self._ai_model, not self._ai_enabled, self._ai_ollama_host
        )

    def _parse_bool(self, v: str, default=False) -> bool:
        if v is None:
            return default
        return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")

    def get_ai_tone(self) -> str:
        return os.getenv("AI_TONE", "PG").upper()  # PG | PG13 | R

    def get_ai_allow_slang(self) -> bool:
        return self._parse_bool(os.getenv("AI_ALLOW_SLANG", "false"))

    def get_ai_allow_catchphrases(self) -> bool:
        return self._parse_bool(os.getenv("AI_ALLOW_CATCHPHRASES", "false"))

    @staticmethod
    def _parse_bool(val: str) -> bool:
        return str(val).strip().lower() in ("1", "true", "t", "yes", "y", "on")

    # ---- Discord
    def get_discord_token(self) -> str:
        return self._discord_token

    # ---- SQLite paths
    def get_sqlite_db_path(self) -> str:
        return self._sqlite_db_path

    def get_schema_path(self) -> str:
        return self._schema_path

    # ---- Timezone
    def get_default_timezone(self) -> str:
        return self._default_timezone

    # ---- AI
    def get_ai_provider(self) -> str:
        return self._ai_provider

    def get_ai_model(self) -> str:
        return self._ai_model

    def get_ai_ollama_host(self) -> str:
        return self._ai_ollama_host

    def is_ai_enabled(self) -> bool:
        return self._ai_enabled
