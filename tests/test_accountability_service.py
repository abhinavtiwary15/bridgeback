"""Tests for accountability/check-in service behavior."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.database import create_action_task, get_action_tasks, init_db
from services.accountability_service import (
    apply_checkin_reply,
    generate_micro_step,
    infer_blocker_category,
    parse_checkin_reply,
)


def test_parse_checkin_reply_variants():
    status, reason = parse_checkin_reply("YES done")
    assert status == "completed"
    assert reason == ""

    status, reason = parse_checkin_reply("No, I was too anxious")
    assert status == "blocked"
    assert "anxious" in reason.lower()


def test_apply_checkin_reply_updates_action_status():
    init_db()
    user_id = f"acct-{uuid.uuid4()}"
    action_id = str(uuid.uuid4())
    create_action_task(
        user_id=user_id,
        action_id=action_id,
        target="Priya",
        action_text="Send Priya a check-in message",
    )

    outcome = apply_checkin_reply(user_id, "No, I felt anxious and overthinking.")
    assert outcome.handled is True
    assert outcome.status == "blocked"
    assert outcome.micro_step

    rows = get_action_tasks(user_id=user_id, limit=10)
    assert rows[0].status == "blocked"


def test_generate_micro_step_has_fallback():
    step = generate_micro_step("I do not know")
    assert "smallest step" in step.lower()


def test_infer_blocker_category_anxiety():
    category = infer_blocker_category("I felt anxious and scared to message.")
    assert category == "social_anxiety"
