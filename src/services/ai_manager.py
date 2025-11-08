from __future__ import annotations
import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)

class AIManager:
    """
    Provider-agnostic generator for persona reminders.
    - enabled == True  → actually call the model
    - enabled == False → deterministic fallback (no network)
    """

    def __init__(
        self,
        config=None,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        ollama_host: Optional[str] = None,
        enabled: bool | None = None,
    ):
        if config:
            self.provider = (provider or config.get_ai_provider()).lower()
            self.model = model or (config.get_ai_model() or "mistral")
            self.ollama_host = (ollama_host or config.get_ai_ollama_host()).rstrip("/")
            # enabled=True means “call the model”
            self.enabled = config.is_ai_enabled() if (enabled is None) else enabled

            # Style knobs
            self.tone = config.get_ai_tone()  # "PG" | "PG13" | "R"
            self.allow_slang = config.get_ai_allow_slang()
            self.allow_catchphrases = config.get_ai_allow_catchphrases()
        else:
            self.provider = (provider or "none").lower()
            self.model = model or "mistral"
            self.ollama_host = (ollama_host or "http://127.0.0.1:11434").rstrip("/")
            self.enabled = bool(enabled)
            self.tone = "PG"
            self.allow_slang = False
            self.allow_catchphrases = False

        logger.info(
            "AIManager: provider=%s model=%s enabled=%s host=%s tone=%s slang=%s catchphrases=%s",
            self.provider, self.model, self.enabled, self.ollama_host,
            self.tone, self.allow_slang, self.allow_catchphrases
        )

    # ---------- Prompt building ----------
    def _build_prompt(self, persona: str, label: str, user_name: Optional[str]) -> str:
        # Base rules
        rules: list[str] = [
            "Write exactly ONE sentence (<120 chars) as the requested persona.",
            "Goal: a short, motivating reminder.",
            "Do NOT include the user's name in the sentence; name will be appended after.",
            "No emojis or hashtags.",
            "No backstory; focus only on the reminder.",
        ]

        # Tone gate
        if self.tone in ("PG", "PG13"):
            rules.append("Keep it family-safe; no profanity or sexual content.")
        else:  # R
            rules.append("R language allowed (light profanity OK); avoid slurs/hate speech.")

        # Slang & catchphrases
        rules.append("Slang is allowed if it fits the persona." if self.allow_slang else "Avoid slang.")
        rules.append(
            "You MAY allude to or lightly echo the persona's style/catchphrases."
            if self.allow_catchphrases else
            "Avoid copyrighted catchphrases or verbatim quotes."
        )

        return (
            "You are writing a persona-styled reminder.\n"
            + "\n".join(f"- {r}" for r in rules) + "\n"
            f"Persona: {persona}\n"
            f"Task: remind the user to {label}.\n"
            "Output: only the single sentence (no quotes)."
        )

    # ---------- Public API ----------
    async def generate(self, persona: str, label: str, user_name: Optional[str] = None) -> str:
        prompt = self._build_prompt(persona, label, user_name)
        logger.debug("AI Prompt => %s", prompt)

        if not self.enabled:
            # Deterministic fallback
            clean = (label or "").strip().rstrip(".!?")
            line = f"Remember to {clean}."
        else:
            if self.provider == "ollama":
                line = await self._generate_with_ollama(prompt=prompt)
            else:
                # Unknown provider => fallback
                clean = (label or "").strip().rstrip(".!?")
                line = f"Remember to {clean}."

        # Append user name at the end if not present
        first = (line or "").strip()
        if user_name and user_name.lower() not in first.lower():
            first = f"{first.rstrip('.!?')}, {user_name}."

        # Consistent persona signature
        return f"{first}\n- {persona}"

    # ---------- Provider implementations ----------
    async def _generate_with_ollama(self, *, prompt: str, temperature: float = 0.7) -> str:
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
            "stream": False,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise RuntimeError(f"Ollama error {resp.status}: {text}")
                    data = await resp.json()
                    msg = (data.get("response") or "").strip()
                    return msg or "Remember to take care of yourself."
        except Exception as e:
            logger.exception("AIManager._generate_with_ollama failed: %s", e)
            return "Remember to take care of yourself."
