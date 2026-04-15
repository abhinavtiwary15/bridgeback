"""Pydantic request/response schemas for FastAPI routes."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = "default"
    message: str
    backend: Optional[str] = None


class ChatResponse(BaseModel):
    response_text: str
    structured_data: dict = Field(default_factory=dict)
    mode: str = "INTAKE"


class PlanActionDTO(BaseModel):
    action_id: str
    target: str
    action_text: str
    status: str
    blocker_reason: str = ""
    micro_step: str = ""


class PlanResponse(BaseModel):
    user_id: str
    actions: List[PlanActionDTO] = Field(default_factory=list)


class ActionUpdateRequest(BaseModel):
    user_id: str = "default"
    action_id: str
    status: Literal["completed", "blocked"]
    blocker_reason: str = ""


class BlockerRequest(BaseModel):
    user_id: str = "default"
    reply_text: str


class BlockerResponse(BaseModel):
    handled: bool
    status: str
    micro_step: str = ""


class ProgressPoint(BaseModel):
    session_num: int
    score: int
    date: str
    connections: int
    crisis: bool


class ProgressResponse(BaseModel):
    user_id: str
    history: List[ProgressPoint]
    streak: int
    total_connections: int
    insight: str
    action_status: dict


class ReminderResponse(BaseModel):
    queued: bool
    user_id: str
    timestamp: datetime


class DeviceTokenRequest(BaseModel):
    user_id: str = "default"
    token: str
    platform: str = "unknown"
