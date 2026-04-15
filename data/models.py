"""
BridgeBack — Data Models
Pydantic models shared across all layers.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ── User Auth Models ────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    username: str
    password: str
    telegram_chat_id: Optional[str] = None


class UserOut(BaseModel):
    id: str
    username: str
    telegram_chat_id: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Relationship ──────────────────────────────────────────────────────────────


class RelationshipSignal(BaseModel):
    name: str
    status: Literal["active", "drifted", "unknown"] = "unknown"
    last_mentioned_context: str = ""
    mention_count: int = 1


# ── NLP Profile (Layer 1 output) ──────────────────────────────────────────────


class NLPProfile(BaseModel):
    loneliness_score: int = Field(0, ge=0, le=100)
    relationship_signals: List[RelationshipSignal] = Field(default_factory=list)
    drift_signals: List[str] = Field(default_factory=list)
    social_anxiety_markers: List[str] = Field(default_factory=list)
    connection_need_type: Literal[
        "deep_friendship",
        "community_belonging",
        "family_reconnection",
        "romantic",
        "professional",
        "unknown",
    ] = "unknown"
    connections_reported_count: int = Field(0, ge=0)
    last_action_assigned: str = ""
    action_completed: bool = True
    action_timestamp: Optional[datetime] = None
    crisis_detected: bool = False


# ── Reconnection Action (Layer 3) ─────────────────────────────────────────────


class ReconnectionAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["reconnect_person", "community_event"]
    target: str
    rationale: str = ""
    action: str
    suggested_message: Optional[str] = None
    difficulty: Literal["low", "medium", "high"] = "low"
    timeframe: str = "this week"
    registration_link: Optional[str] = None
    priority_score: int = Field(0, ge=0, le=100)


class ReconnectionPlan(BaseModel):
    priority_actions: List[ReconnectionAction] = Field(default_factory=list)
    weekly_goal: str = ""
    avoid_note: str = (
        "Do not open BridgeBack unless you have completed "
        "at least one action from this list."
    )


# ── Accountability Models ──────────────────────────────────────────────────────


class ActionTask(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    target: str
    action_text: str
    status: Literal["pending", "completed", "blocked"] = "pending"
    blocker_reason: str = ""
    blocker_category: str = "unknown"
    micro_step: str = ""
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ReminderEvent(BaseModel):
    reminder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_id: str
    user_id: str = "default"
    channel: Literal["whatsapp", "push"] = "whatsapp"
    message: str = ""
    status: Literal["queued", "sent", "failed", "mocked"] = "queued"
    provider_message_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Session (Layer 4) ─────────────────────────────────────────────────────────


class SessionRecord(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    loneliness_score: int = 0
    connections_reported: List[str] = Field(default_factory=list)
    actions_completed: int = 0
    actions_pending: List[str] = Field(default_factory=list)
    mood_signal: str = "neutral"
    crisis_flagged: bool = False
    last_action_assigned: str = ""
    action_completed: bool = True
    action_timestamp: Optional[datetime] = None
    nlp_profile: Optional[NLPProfile] = None
    plan: Optional[ReconnectionPlan] = None


# ── Conversation Message ───────────────────────────────────────────────────────


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── LLM Response wrapper ──────────────────────────────────────────────────────


class LLMResponse(BaseModel):
    text: str
    mode: Literal["INTAKE", "COACHING", "CRISIS", "REDIRECT"] = "INTAKE"
    updated_profile: Optional[NLPProfile] = None
    updated_plan: Optional[ReconnectionPlan] = None
