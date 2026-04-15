"""Tests for conversation parsing and backend selection."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llm.conversation import _build_nlp_profile, _build_plan, ConversationEngine


def test_profile_parses_connections_and_anxiety():
    parsed = {
        "loneliness_score": 64,
        "relationship_signals": [
            {"name": "Priya", "status": "drifted", "context": "We used to walk together."}
        ],
        "drift_signals": ["we used to"],
        "social_anxiety_markers": ["afraid to reach out"],
        "connection_need_type": "deep_friendship",
        "connections_reported": 2,
        "crisis": False,
    }
    profile = _build_nlp_profile(parsed)

    assert profile.loneliness_score == 64
    assert profile.connections_reported_count == 2
    assert "afraid to reach out" in profile.social_anxiety_markers
    assert profile.relationship_signals[0].name == "Priya"


def test_plan_supports_name_fallback():
    parsed = {
        "relationship_signals": [
            {"name": "Board Game Night", "status": "drifted", "context": "Missed community events."}
        ],
        "plan": {
            "priority_actions": [
                {
                    "type": "community_event",
                    "name": "Board Game Night",
                    "rationale": "Low pressure social setting.",
                    "action": "Attend this Thursday at 7PM.",
                    "difficulty": "low",
                    "timeframe": "this week",
                }
            ],
            "weekly_goal": "Complete one social action this week.",
        }
    }

    plan = _build_plan(parsed)
    assert plan is not None
    assert plan.priority_actions[0].target == "Board Game Night"
    assert plan.priority_actions[0].priority_score > 0


def test_companion_request_triggers_redirect_without_backend():
    engine = ConversationEngine(backend="groq")
    response = engine.chat("Please just keep me company, you are my only friend.")
    assert response.mode == "REDIRECT"
    assert "not who you actually need" in response.text
