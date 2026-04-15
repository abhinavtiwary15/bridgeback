"""Tests for blocker-first gate predicates."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.database import (
    complete_action_task,
    create_action_task,
    has_completed_action_since_last_session,
    has_pending_actions,
    init_db,
)


def test_gate_active_when_pending_and_no_completed():
    init_db()
    user_id = f"gate-{uuid.uuid4()}"
    action_id = str(uuid.uuid4())
    create_action_task(
        user_id=user_id,
        action_id=action_id,
        target="Rahul",
        action_text="Message Rahul today",
    )
    assert has_pending_actions(user_id) is True
    assert has_completed_action_since_last_session(user_id) is False


def test_gate_unlocks_after_action_completion():
    user_id = f"gate2-{uuid.uuid4()}"
    action_id = str(uuid.uuid4())
    create_action_task(
        user_id=user_id,
        action_id=action_id,
        target="Arjun",
        action_text="Call Arjun for 10 minutes",
    )
    complete_action_task(action_id, user_id=user_id)
    assert has_completed_action_since_last_session(user_id) is True


def test_gate_reactivates_for_new_pending_action():
    user_id = f"gate3-{uuid.uuid4()}"
    first_action = str(uuid.uuid4())
    create_action_task(
        user_id=user_id,
        action_id=first_action,
        target="Aman",
        action_text="Send Aman a check-in",
    )
    complete_action_task(first_action, user_id=user_id)
    assert has_completed_action_since_last_session(user_id) is True

    second_action = str(uuid.uuid4())
    create_action_task(
        user_id=user_id,
        action_id=second_action,
        target="Neha",
        action_text="Call Neha this evening",
    )
    assert has_pending_actions(user_id) is True
    assert has_completed_action_since_last_session(user_id) is False
