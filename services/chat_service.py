"""
BridgeBack chat service utilities.
Keeps Streamlit UI layer thin by handling chat orchestration and persistence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Tuple

from data.database import (
    create_action_task,
    increment_connections,
    save_message,
    save_session,
    update_profile_score,
)
from data.models import LLMResponse, SessionRecord
from services.accountability_service import send_pending_action_checkin
from services.interfaces import ChatEngine


@dataclass
class ChatProcessResult:
    assistant_text: str
    is_crisis: bool
    score: int | None
    connection_count: int


def process_user_message(
    engine: ChatEngine, user_id: str, user_text: str
) -> Tuple[ChatProcessResult, LLMResponse]:
    """
    Process one user message end-to-end.
    - stores user + assistant messages
    - updates profile score and connection totals
    - stores immutable session record snapshot
    Returns a summary object and the raw engine response for UI updates.
    """
    save_message(user_id, "user", user_text)
    response = engine.chat(user_text)
    save_message(user_id, "assistant", response.text)

    score = None
    if (
        response.updated_profile
        and response.updated_profile.loneliness_score is not None
    ):
        score = response.updated_profile.loneliness_score
        update_profile_score(user_id, score)

    connection_count = 0
    if response.updated_profile:
        connection_count = response.updated_profile.connections_reported_count
        if connection_count > 0:
            increment_connections(user_id, connection_count)

    connection_notes = []
    if connection_count > 0:
        connection_notes = [
            f"Reported {connection_count} completed connection(s) this session"
        ]

    save_session(
        SessionRecord(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=datetime.now(UTC),
            loneliness_score=score or 0,
            connections_reported=connection_notes,
            actions_completed=connection_count,
            actions_pending=[
                action.action
                for action in (
                    response.updated_plan.priority_actions
                    if response.updated_plan
                    else []
                )
            ],
            crisis_flagged=response.mode == "CRISIS",
            nlp_profile=response.updated_profile,
            plan=response.updated_plan,
        )
    )

    if response.updated_plan:
        for action in response.updated_plan.priority_actions:
            create_action_task(
                user_id=user_id,
                action_id=action.action_id,
                target=action.target,
                action_text=action.action,
            )
        # Fire a reminder/check-in after plan refresh (mocked if Twilio not configured).
        send_pending_action_checkin(user_id=user_id)

    result = ChatProcessResult(
        assistant_text=response.text,
        is_crisis=response.mode == "CRISIS",
        score=score,
        connection_count=connection_count,
    )
    return result, response
