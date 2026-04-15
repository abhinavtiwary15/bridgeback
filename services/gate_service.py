"""Blocker-first gate logic shared by Streamlit and API layers."""

from __future__ import annotations

from dataclasses import dataclass

from data.database import (
    has_pending_actions,
    has_completed_action_since_last_session,
    get_latest_pending_action,
)
from services.accountability_service import apply_checkin_reply


@dataclass
class GateState:
    active: bool
    action_id: str = ""
    action_text: str = ""


def get_gate_state(user_id: str = "default") -> GateState:
    pending = has_pending_actions(user_id)
    completed = has_completed_action_since_last_session(user_id)
    action = get_latest_pending_action(user_id)
    if pending and not completed and action:
        return GateState(active=True, action_id=action.action_id, action_text=action.action_text)
    return GateState(active=False)


def submit_gate_reply(user_id: str, reply_text: str):
    return apply_checkin_reply(user_id=user_id, reply_text=reply_text)
