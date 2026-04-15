"""Relationship Priority Engine."""

from __future__ import annotations

from typing import Dict, List


def _score_relationship(signal: dict) -> tuple[float, str]:
    name = signal.get("name", "")
    status = signal.get("status", "unknown")
    context = (signal.get("context") or signal.get("last_mentioned_context") or "").lower()
    mention_count = int(signal.get("mention_count", 1) or 1)

    emotional_importance = min(1.0, mention_count / 5.0)
    drift_severity = 1.0 if ("used to" in context or status == "drifted") else 0.3
    recency_penalty = 0.2 if "last week" in context or "yesterday" in context else 1.0
    active_penalty = 0.35 if status == "active" else 1.0

    weighted = (
        0.45 * emotional_importance
        + 0.35 * drift_severity
        + 0.20 * recency_penalty
    ) * active_penalty

    reason = "High emotional importance + long drift" if status == "drifted" else "Meaningful person with reconnection potential"
    if not name:
        reason = "Insufficient relationship data"
    return max(0.0, min(1.0, weighted)), reason


def rank_relationships(nlp_profile: dict) -> list:
    """
    Return top 1-3 people ranked for reconnection priority.
    """
    signals: List[Dict] = nlp_profile.get("relationship_signals", []) or []
    ranked = []
    for signal in signals:
        name = signal.get("name", "")
        if not name:
            continue
        score, reason = _score_relationship(signal)
        ranked.append(
            {
                "name": name,
                "priority_score": round(score, 2),
                "reason": reason,
            }
        )
    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    return ranked[:3]
