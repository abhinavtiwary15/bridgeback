"""Tests for DB-backed API dependency hydration."""

import os
import sys
import uuid
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.dependencies import get_engine_for_user
from data.database import create_action_task, init_db, save_message, save_session
from data.models import NLPProfile, ReconnectionAction, ReconnectionPlan, SessionRecord


def test_engine_hydrates_history_and_state_from_db():
    init_db()
    user_id = f"deps-{uuid.uuid4()}"

    save_message(user_id, "user", "I miss Priya.")
    save_message(user_id, "assistant", "Let's reconnect with Priya.")
    profile = NLPProfile(
        loneliness_score=62, relationship_signals=[], action_completed=False
    )
    plan = ReconnectionPlan(
        priority_actions=[
            ReconnectionAction(
                target="Priya",
                type="reconnect_person",
                action="Send a quick message to Priya now.",
                rationale="Rebuild connection.",
            )
        ],
        weekly_goal="Reach out once today.",
    )
    save_session(
        SessionRecord(
            user_id=user_id,
            timestamp=datetime.now(UTC),
            loneliness_score=62,
            nlp_profile=profile,
            plan=plan,
            action_completed=False,
            last_action_assigned="Send a quick message to Priya now.",
            action_timestamp=datetime.now(UTC),
        )
    )
    create_action_task(
        user_id=user_id,
        action_id=str(uuid.uuid4()),
        target="Priya",
        action_text="Send a quick message to Priya now.",
    )

    engine = get_engine_for_user(user_id, backend="ollama")
    assert len(engine.history) >= 2
    assert engine.current_plan is not None
    assert engine.last_action_assigned != ""
    assert engine.action_completed is False
