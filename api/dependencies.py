"""Shared API dependencies with DB-backed conversation hydration."""

from __future__ import annotations

import json

from config import DEFAULT_LLM
from data.database import (
    get_latest_pending_action,
    get_sessions,
    has_completed_action_since_last_session,
)
from data.models import NLPProfile, ReconnectionPlan
from data.session_store import load_history
from llm.conversation import ConversationEngine


def get_engine_for_user(user_id: str, backend: str | None = None) -> ConversationEngine:
    """
    Build a fresh engine hydrated from persistent storage.
    This avoids in-memory-only state and works across restarts/workers.
    """
    engine = ConversationEngine(backend=backend or DEFAULT_LLM)
    engine.history = load_history(user_id)

    latest_sessions = get_sessions(user_id=user_id, limit=1)
    if latest_sessions:
        latest = latest_sessions[0]
        try:
            profile_data = json.loads(latest.nlp_profile_json or "{}")
            if profile_data:
                engine.current_profile = NLPProfile.model_validate(profile_data)
        except Exception:
            engine.current_profile = None
        try:
            plan_data = json.loads(latest.plan_json or "{}")
            if plan_data:
                engine.current_plan = ReconnectionPlan.model_validate(plan_data)
        except Exception:
            engine.current_plan = None

    latest_pending = get_latest_pending_action(user_id=user_id)
    if latest_pending:
        engine.last_action_assigned = latest_pending.action_text
        engine.action_timestamp = latest_pending.created_at
    engine.action_completed = has_completed_action_since_last_session(user_id=user_id)
    return engine


# ── Auth Dependencies ─────────────────────────────────────────────────────────

import os  # noqa: E402
from datetime import UTC, datetime, timedelta  # noqa: E402

import bcrypt  # noqa: E402
from fastapi import Depends, HTTPException, status  # noqa: E402
from fastapi.security import OAuth2PasswordBearer  # noqa: E402
from jose import JWTError, jwt  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from data.database import DBUser, get_db  # noqa: E402

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-default-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def authenticate_user(db: Session, username: str, password: str) -> DBUser | None:
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
