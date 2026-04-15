"""Service-level typing contracts used across BridgeBack modules."""

from __future__ import annotations

from typing import Protocol

from data.models import LLMResponse


class ChatEngine(Protocol):
    """Typing contract for conversation engine implementations."""

    backend: str

    def chat(self, user_message: str) -> LLMResponse: ...

    def clear_history(self) -> None: ...
