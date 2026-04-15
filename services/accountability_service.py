"""Accountability check-ins, reply parsing, and blocker handling."""

from __future__ import annotations

import re
from dataclasses import dataclass

from data.database import (
    DBUser,
    SessionLocal,
    block_action_task,
    complete_action_task,
    create_reminder_event,
    get_device_tokens,
    get_latest_pending_action,
)
from services.notification_service import send_push_notification, send_telegram_message

BLOCKER_MICRO_STEPS = {
    "fear_of_rejection": "Send a two-line low-pressure message: 'Hey, thought of you today. No pressure to reply quickly.'",
    "time_pressure": "Set a 5-minute timer now and send one short check-in before it ends.",
    "not_sure_what_to_say": "Copy this starter: 'Hey, it has been a while. Want to catch up for 15 minutes this week?'",
    "social_anxiety": "Draft the message in notes first, then press send without editing more than once.",
}


@dataclass
class CheckinOutcome:
    handled: bool
    status: str
    micro_step: str = ""
    blocker_category: str = "unknown"


def send_pending_action_checkin(user_id: str = "default") -> bool:
    action = get_latest_pending_action(user_id=user_id)
    if not action:
        return False

    msg = (
        f"BridgeBack check-in: did you complete this action?\n"
        f"- {action.action_text}\n"
        "Reply YES if done, or NO + a short reason."
    )
    telegram_chat_id = None
    with SessionLocal() as db:
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if user:
            telegram_chat_id = user.telegram_chat_id

    result = send_telegram_message(msg, chat_id=telegram_chat_id)
    create_reminder_event(
        action_id=action.action_id,
        user_id=user_id,
        message=msg,
        status=result.status,
        provider_message_id=result.provider_message_id,
    )
    tokens = get_device_tokens(user_id=user_id)
    push_result = send_push_notification(
        tokens,
        title="BridgeBack check-in",
        body="Did you complete your reconnection action?",
    )
    create_reminder_event(
        action_id=action.action_id,
        user_id=user_id,
        message="Push reminder",
        status=push_result.status,
        provider_message_id=push_result.provider_message_id,
        channel="push",
    )
    return result.status in {"sent", "mocked"}


def infer_blocker_category(blocker_reason: str) -> str:
    reason = blocker_reason.lower()
    if "anxious" in reason or "anxiety" in reason or "scared" in reason:
        return "social_anxiety"
    if "reject" in reason or "ignored" in reason or "awkward" in reason:
        return "fear_of_rejection"
    if "busy" in reason or "time" in reason or "work" in reason:
        return "time_pressure"
    if "what to say" in reason or "words" in reason or "message" in reason:
        return "not_sure_what_to_say"
    return "unknown"


def generate_micro_step(blocker_reason: str) -> str:
    category = infer_blocker_category(blocker_reason)
    if category in BLOCKER_MICRO_STEPS:
        return BLOCKER_MICRO_STEPS[category]
    return "Do the smallest step now: open chat, type one sentence, and send within 2 minutes."


def parse_checkin_reply(reply_text: str) -> tuple[str, str]:
    text = reply_text.strip().lower()
    if re.search(r"\b(yes|done|completed|sent)\b", text):
        return "completed", ""
    if re.search(r"\b(no|not yet|didn't|didnt)\b", text):
        # reason: everything after no/not yet markers
        reason = reply_text
        return "blocked", reason
    return "unknown", ""


def apply_checkin_reply(user_id: str, reply_text: str) -> CheckinOutcome:
    action = get_latest_pending_action(user_id=user_id)
    if not action:
        return CheckinOutcome(handled=False, status="no_pending_action")

    status, reason = parse_checkin_reply(reply_text)
    if status == "completed":
        complete_action_task(action.action_id, user_id=user_id)
        return CheckinOutcome(handled=True, status="completed")
    if status == "blocked":
        blocker_category = infer_blocker_category(reason)
        micro_step = generate_micro_step(reason)
        block_action_task(
            action.action_id,
            blocker_reason=reason,
            blocker_category=blocker_category,
            micro_step=micro_step,
            user_id=user_id,
        )
        return CheckinOutcome(
            handled=True,
            status="blocked",
            micro_step=micro_step,
            blocker_category=blocker_category,
        )
    return CheckinOutcome(handled=False, status="unknown")
