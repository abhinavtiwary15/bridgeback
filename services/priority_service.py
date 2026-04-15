"""Relationship priority scoring for reconnection actions."""

from __future__ import annotations

from typing import Iterable, Dict

from data.models import ReconnectionAction


def _difficulty_bonus(level: str) -> int:
    return {"low": 25, "medium": 15, "high": 5}.get(level, 10)


def _timeframe_bonus(timeframe: str) -> int:
    text = (timeframe or "").lower()
    if "today" in text:
        return 20
    if "weekend" in text:
        return 12
    if "week" in text:
        return 10
    return 6


def score_reconnection_action(action: ReconnectionAction, relationship_status: str = "unknown") -> int:
    score = 20
    if action.type == "reconnect_person":
        score += 20
    if relationship_status == "drifted":
        score += 20
    score += _difficulty_bonus(action.difficulty)
    score += _timeframe_bonus(action.timeframe)

    if action.suggested_message:
        score += 5

    return max(0, min(100, score))


def assign_priorities(
    actions: Iterable[ReconnectionAction],
    relationship_signals: list[Dict] | None = None,
) -> list[ReconnectionAction]:
    status_by_name = {}
    for rel in relationship_signals or []:
        name = (rel.get("name") or "").strip().lower()
        if name:
            status_by_name[name] = rel.get("status", "unknown")

    updated = []
    for action in actions:
        rel_status = status_by_name.get(action.target.strip().lower(), "unknown")
        action.priority_score = score_reconnection_action(action, rel_status)
        updated.append(action)
    return sorted(updated, key=lambda a: a.priority_score, reverse=True)
