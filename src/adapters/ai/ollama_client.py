import requests
import asyncio
from typing import Optional

class OllamaClient:
    def __init__(self, model: str, host: str = "http://127.0.0.1:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def _generate_sync(self, prompt: str) -> str:
        # Use /api/generate (single prompt) to keep deps minimal
        resp = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("response") or "").strip()
        return text or "(no response)"

    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_sync, prompt)
