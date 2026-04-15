"""
BridgeBack — Layer 4: Longitudinal Progress Tracker
Tracks loneliness score over time, connection streaks,
relationship health, and generates weekly insights.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from data.database import get_action_status_counts, get_or_create_profile, get_sessions

logger = logging.getLogger(__name__)


def get_score_history(user_id: str = "default") -> List[Dict]:
    """
    Return list of {session_num, score, date, connections} dicts
    ordered chronologically for charting.
    """
    sessions = get_sessions(user_id)
    sessions_sorted = sorted(sessions, key=lambda s: s.timestamp)
    return [
        {
            "session_num": i + 1,
            "score": s.loneliness_score,
            "date": s.timestamp.strftime("%b %d"),
            "connections": s.actions_completed,
            "crisis": s.crisis_flagged,
        }
        for i, s in enumerate(sessions_sorted)
    ]


def get_streak(user_id: str = "default") -> int:
    """
    Return the current streak of consecutive weeks where the user
    completed at least one social action.
    """
    sessions = get_sessions(user_id)
    sessions_sorted = sorted(sessions, key=lambda s: s.timestamp, reverse=True)
    streak = 0
    for s in sessions_sorted:
        if s.actions_completed >= 1:
            streak += 1
        else:
            break
    return streak


def get_total_connections(user_id: str = "default") -> int:
    profile = get_or_create_profile(user_id)
    return profile.total_connections


def get_score_delta(user_id: str = "default") -> Optional[int]:
    """
    Return score improvement (positive = better).
    baseline_score - current_score (lower score = less lonely = improvement).
    """
    profile = get_or_create_profile(user_id)
    if profile.baseline_score and profile.current_score:
        return profile.baseline_score - profile.current_score
    return None


def generate_weekly_insight(user_id: str = "default") -> str:
    """
    Auto-generate a weekly insight summary string.
    e.g. "This week you reached out to 2 people. Your score dropped 11 points."
    """
    history = get_score_history(user_id)
    if not history:
        return "Start your first session to begin tracking your progress."

    latest = history[-1]
    connections = latest["connections"]
    score = latest["score"]

    insight_parts = []

    if connections == 0:
        insight_parts.append("No social actions recorded this week yet.")
    elif connections == 1:
        insight_parts.append("You completed 1 social action this week.")
    else:
        insight_parts.append(f"You completed {connections} social actions this week.")

    if len(history) >= 2:
        prev_score = history[-2]["score"]
        delta = prev_score - score
        if delta > 0:
            insight_parts.append(f"Your loneliness score dropped {delta} points. 🎉")
        elif delta < 0:
            insight_parts.append(
                f"Your score rose {abs(delta)} points — let's focus on that."
            )
        else:
            insight_parts.append("Your score held steady.")

    streak = get_streak(user_id)
    if streak >= 2:
        insight_parts.append(f"You're on a {streak}-session streak of taking action.")

    action_counts = get_action_status_counts(user_id)
    if action_counts["blocked"] > 0:
        insight_parts.append(
            f"{action_counts['blocked']} action(s) are blocked; complete one micro-step today."
        )

    return " ".join(insight_parts)


def get_relationship_health_map(user_id: str = "default") -> List[Dict]:
    """
    Return a list of relationship nodes for network graph visualisation.
    Aggregates relationship signals across all sessions.
    """
    sessions = get_sessions(user_id)
    relationships: Dict[str, Dict] = {}

    for s in sessions:
        try:
            profile_data = json.loads(s.nlp_profile_json or "{}")
            signals = profile_data.get("relationship_signals", [])
            for sig in signals:
                name = sig.get("name", "")
                status = sig.get("status", "unknown")
                ctx = sig.get("last_mentioned_context", "")
                if name:
                    if name not in relationships:
                        relationships[name] = {
                            "name": name,
                            "status": status,
                            "context": ctx,
                            "mentions": 0,
                        }
                    relationships[name]["mentions"] += 1
                    # latest status wins
                    relationships[name]["status"] = status
        except json.JSONDecodeError:
            logger.warning(
                "Invalid nlp_profile_json for session %s",
                getattr(s, "session_id", "unknown"),
            )
            continue

    return list(relationships.values())
