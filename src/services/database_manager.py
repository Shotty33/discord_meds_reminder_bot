from typing import List, Dict, Optional
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account
from src.utils.config_loader import ConfigLoader
from src.bot import logger


class DatabaseManager:
    """
    Adapter around Firestore that handles persistence of reminders.

    Firestore schema:
      Collection: "users"
        Document ID: <discord_user_id>
        Document body:
        {
            "timezone": "America/New_York",
            "reminders": [
                {
                    "label": "Adderall",
                    "time": "08:00",           # HH:MM, 24h
                    "persona": "batman",
                    "active": True,
                    "createdAt": "2025-10-25T12:05:00Z"
                }
            ]
        }

    Notes:
    - We do NOT track or store whether the user actually took meds.
    - We only store what to say, when to say it, and in what voice.
    """

    def __init__(self, config: ConfigLoader):
        """
        Dependency-injected configuration.
        We build and hold the Firestore client once.
        """
        project_id = config.get_gcp_project_id()
        cred_path = config.get_gcp_credentials_path()

        if not project_id or not cred_path:
            logger.error("Missing GOOGLE_PROJECT_ID or GOOGLE_APPLICATION_CREDENTIALS in environment")
            raise RuntimeError("Firestore configuration is missing. Check your .env file.")

        credentials = service_account.Credentials.from_service_account_file(cred_path)
        self.client = firestore.Client(project=project_id, credentials=credentials)

        # we may want this default if the user doesn't have one set yet
        self.default_timezone = config.get_default_timezone()

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------

    def _user_doc_ref(self, user_id: str) -> firestore.DocumentReference:
        """
        Return DocumentReference for this Discord user's Firestore record.
        """
        return self.client.collection("users").document(user_id)

    def _get_user_doc(self, user_id: str) -> Dict:
        """
        Get this user's stored data.
        Returns {} if user doesn't exist yet in Firestore.
        """
        doc_ref = self._user_doc_ref(user_id)
        snapshot = doc_ref.get()
        if snapshot.exists:
            return snapshot.to_dict()
        return {}

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def add_reminder(
            self,
            user_id: str,
            label: str,
            reminder_time: str,
            persona: str,
            timezone: Optional[str] = None,
    ) -> None:
        """
        Add (append) a reminder under this user's Firestore doc.

        We do not generate numeric IDs.
        We just append a dict containing:
          label (what to do)
          time (HH:MM 24h)
          persona (voice/character)
          active (bool)
          createdAt (UTC timestamp ISO)
        """

        doc_ref = self._user_doc_ref(user_id)
        existing_doc = self._get_user_doc(user_id)

        reminders: List[Dict] = existing_doc.get("reminders", [])

        new_reminder = {
            "label": label,
            "time": reminder_time,
            "persona": persona,
            "active": True,
            "createdAt": datetime.utcnow().isoformat() + "Z",
        }

        reminders.append(new_reminder)

        # Merge back into Firestore
        doc_ref.set(
            {
                "timezone": existing_doc.get("timezone", timezone or self.default_timezone),
                "reminders": reminders,
            },
            merge=True,
        )

        logger.info(f"[DB] Added reminder for user {user_id}: {new_reminder}")

    def list_reminders(self, user_id: str) -> List[Dict]:
        """
        Return all ACTIVE reminders for this user.
        If the user doesn't exist yet, return [].
        """
        data = self._get_user_doc(user_id)

        reminders = data.get("reminders", [])
        active_reminders = [r for r in reminders if r.get("active", True)]

        logger.info(f"[DB] Retrieved {len(active_reminders)} reminders for user {user_id}")
        return active_reminders

    def delete_reminder(self, user_id: str, label: str, reminder_time: str) -> bool:
        """
        Delete a reminder that matches (label, time) for this user.
        We don't use IDs because this is personal-scale usage.

        Returns:
            True if a reminder was removed
            False if no match found
        """

        doc_ref = self._user_doc_ref(user_id)
        existing_doc = self._get_user_doc(user_id)

        reminders: List[Dict] = existing_doc.get("reminders", [])
        if not reminders:
            logger.info(f"[DB] No reminders to delete for user {user_id}")
            return False

        # Filter out the one we want to delete
        filtered = [
            r for r in reminders
            if not (
                    r.get("label") == label
                    and r.get("time") == reminder_time
                    and r.get("active", True) is True
            )
        ]

        # If nothing changed, nothing matched
        if len(filtered) == len(reminders):
            logger.info(
                f"[DB] No reminder matched label='{label}' time='{reminder_time}' for user {user_id}"
            )
            return False

        # Write back the updated list
        doc_ref.set(
            {
                "timezone": existing_doc.get("timezone", self.default_timezone),
                "reminders": filtered,
            },
            merge=True,
        )

        logger.info(
            f"[DB] Deleted reminder for user {user_id}: label='{label}', time='{reminder_time}'"
        )
        return True
