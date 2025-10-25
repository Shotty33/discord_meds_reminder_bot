import os
from dotenv import load_dotenv


class ConfigLoader:
    """
    Centralized configuration access.

    Responsibilities:
    - Load environment variables from `.env`
    - Expose getters for specific config values
    - Keep secrets & runtime settings in one place
    """

    def __init__(self):
        load_dotenv()

        self._discord_token = os.getenv("DISCORD_BOT_TOKEN")

        self._gcp_project_id = os.getenv("GOOGLE_PROJECT_ID")
        self._gcp_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        self._gemini_api_key = os.getenv("GEMINI_API_KEY")

        self._default_timezone = os.getenv("DEFAULT_TIMEZONE", "America/New_York")

        if not self._discord_token:
            raise RuntimeError("DISCORD_BOT_TOKEN is missing in environment (.env).")

        if not self._gcp_project_id:
            raise RuntimeError("GOOGLE_PROJECT_ID is missing in environment (.env).")

        if not self._gcp_credentials_path:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is missing in environment (.env).")

    # ------------- Discord -------------
    def get_discord_token(self) -> str:
        return self._discord_token

    # ------------- Firestore / GCP -------------
    def get_gcp_project_id(self) -> str:
        return self._gcp_project_id

    def get_gcp_credentials_path(self) -> str:
        return self._gcp_credentials_path

    # ------------- AI / Persona -------------
    def get_gemini_api_key(self) -> str | None:
        return self._gemini_api_key

    # ------------- Defaults / Behavior -------------
    def get_default_timezone(self) -> str:
        return self._default_timezone
