from __future__ import annotations
from typing import Dict, Optional, Any
from src.utils.types import AIClient

class AIManager:
    """
    Provider-agnostic AI facade.
    Register one or more AI providers (adapters) that implement AIClient
    and switch between them at runtime without touching business logic.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, AIClient] = {}
        self._default: Optional[str] = None

    # ---- registration / selection ----
    def register(self, name: str, client: AIClient, *, default: bool = False) -> None:
        self._providers[name] = client
        if default or self._default is None:
            self._default = name

    def use(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"Unknown AI provider '{name}'")
        self._default = name

    def current(self) -> str:
        if not self._default:
            raise RuntimeError("No AI provider registered")
        return self._default

    # ---- generation ----
    async def generate(
        self,
        *,
        persona: str,
        prompt: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self._default:
            raise RuntimeError("No AI provider registered")
        provider = self._providers[self._default]
        return await provider.generate(persona=persona, prompt=prompt, meta=meta or {})
