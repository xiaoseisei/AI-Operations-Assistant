"""Provider-neutral ports used by application and workflow layers."""

from typing import Protocol


class EmailProvider(Protocol):
    """Minimal inbound email port; provider SDKs stay behind connectors."""

    def fetch_message(self, message_id: str) -> dict: ...


class LLMProvider(Protocol):
    """Minimal text-generation port; model SDKs stay behind connectors."""

    def generate(self, prompt: str) -> str: ...
