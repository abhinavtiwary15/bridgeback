"""
BridgeBack — Session Store
Per-user in-memory + DB session management helpers.
"""

from __future__ import annotations

from typing import Dict, List

from data.database import get_messages, save_message


def load_history(user_id: str = "default") -> List[Dict[str, str]]:
    """
    Load past messages from DB and return as LLM-compatible
    list of {"role": ..., "content": ...} dicts.
    """
    rows = get_messages(user_id, limit=40)
    return [{"role": r.role, "content": r.content} for r in rows]


def append_message(user_id: str, role: str, content: str) -> None:
    save_message(user_id, role, content)
