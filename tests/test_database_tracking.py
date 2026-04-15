"""Integration-style tests for database and tracking helpers."""

import os
import sys
import uuid
from datetime import datetime, timedelta, UTC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.database import (
    init_db,
    save_session,
    get_sessions,
    update_profile_score,
    increment_connections,
    get_or_create_profile,
)
from data.models import SessionRecord, LLMResponse, NLPProfile
from services.chat_service import process_user_message
from tracking.tracker import (
    get_score_history,
    get_streak,
    get_total_connections,
    generate_weekly_insight,
)


def test_database_roundtrip_and_tracker_metrics():
    init_db()
    user_id = f"test-user-{uuid.uuid4()}"
    now = datetime.now(UTC)

    save_session(
        SessionRecord(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=now - timedelta(days=2),
            loneliness_score=70,
            actions_completed=0,
        )
    )
    save_session(
        SessionRecord(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=now - timedelta(days=1),
            loneliness_score=60,
            actions_completed=1,
        )
    )

    rows = get_sessions(user_id=user_id, limit=10)
    assert len(rows) == 2

    history = get_score_history(user_id)
    assert len(history) == 2
    assert history[-1]["score"] == 60

    insight = generate_weekly_insight(user_id)
    assert "social action" in insight.lower()
    assert "dropped 10 points" in insight.lower()


def test_profile_updates_connection_totals():
    user_id = f"test-profile-{uuid.uuid4()}"
    update_profile_score(user_id, 58)
    increment_connections(user_id, 3)

    profile = get_or_create_profile(user_id)
    assert profile.current_score == 58
    assert profile.baseline_score == 58
    assert get_total_connections(user_id) == 3
    assert get_streak(user_id) == 0


class _ZeroScoreEngine:
    backend = "ollama"

    def chat(self, _user_message: str) -> LLMResponse:
        return LLMResponse(
            text="ok",
            mode="COACHING",
            updated_profile=NLPProfile(loneliness_score=0),
            updated_plan=None,
        )

    def clear_history(self) -> None:
        return None


def test_chat_service_persists_zero_score():
    user_id = f"test-zero-{uuid.uuid4()}"
    update_profile_score(user_id, 55)
    process_user_message(_ZeroScoreEngine(), user_id=user_id, user_text="test message")
    profile = get_or_create_profile(user_id)
    assert profile.current_score == 0
