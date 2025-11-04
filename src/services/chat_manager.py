from __future__ import annotations
from typing import Dict
from src.utils.types import ChatClient

class ChatManager:
    """
    Platform-agnostic chat facade (Discord, Slack, etc).
    Register adapters by name and send via the active one.
    """
    def __init__(self, default: str = "discord"):
        self._default = default
        self._clients: Dict[str, ChatClient] = {}

    def register(self, name: str, client: ChatClient) -> None:
        self._clients[name] = client

    def use(self, name: str) -> None:
        if name not in self._clients:
            raise KeyError(f"Unknown chat client '{name}'")
        self._default = name

    def current(self) -> str:
        return self._default

    async def send_dm(self, user_id: str, text: str) -> None:
        if self._default not in self._clients:
            raise RuntimeError("No chat client registered")
        await self._clients[self._default].send_dm(user_id, text)
