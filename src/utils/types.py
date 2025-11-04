from typing import Protocol, runtime_checkable, Optional, Dict, Any

@runtime_checkable
class AIClient(Protocol):
    async def generate(self, *, persona: str, prompt: str, meta: Optional[Dict[str, Any]] = None) -> str: ...

@runtime_checkable
class ChatClient(Protocol):
    async def send_dm(self, user_id: str, text: str) -> None: ...
