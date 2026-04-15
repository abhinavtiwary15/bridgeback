"""
BridgeBack — Database Layer
SQLite via SQLAlchemy. Stores sessions, action logs, and user profiles.
"""

from __future__ import annotations
import json
from datetime import datetime, UTC
from typing import List, Optional
import uuid

from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean,
    DateTime, Text, Float, event
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from config import DATABASE_URL
from data.models import SessionRecord, NLPProfile, ReconnectionPlan


# ── ORM Base ──────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass

class DBUser(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    telegram_chat_id = Column(String, nullable=True) # For telegram bot
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class DBSession(Base):
    __tablename__ = "sessions"
    session_id   = Column(String, primary_key=True)
    user_id      = Column(String, index=True, default="default")
    timestamp    = Column(DateTime, default=lambda: datetime.now(UTC))
    loneliness_score = Column(Integer, default=0)
    connections_reported = Column(Text, default="[]")   # JSON list
    actions_completed = Column(Integer, default=0)
    actions_pending  = Column(Text, default="[]")        # JSON list
    mood_signal      = Column(String, default="neutral")
    crisis_flagged   = Column(Boolean, default=False)
    nlp_profile_json = Column(Text, default="{}")
    plan_json        = Column(Text, default="{}")


class DBMessage(Base):
    __tablename__ = "messages"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(String, index=True, default="default")
    role      = Column(String)                      # "user" | "assistant"
    content   = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))


class DBUserProfile(Base):
    __tablename__ = "user_profiles"
    user_id           = Column(String, primary_key=True, default="default")
    location          = Column(String, default="")
    interests         = Column(Text, default="[]")   # JSON list
    current_score     = Column(Integer, default=0)
    baseline_score    = Column(Integer, default=0)
    total_connections = Column(Integer, default=0)
    created_at        = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at        = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class DBActionTask(Base):
    __tablename__ = "action_tasks"
    action_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, default="default")
    target = Column(String, default="")
    action_text = Column(Text, default="")
    status = Column(String, default="pending")
    blocker_reason = Column(Text, default="")
    blocker_category = Column(String, default="unknown")
    micro_step = Column(Text, default="")
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class DBReminderEvent(Base):
    __tablename__ = "reminder_events"
    reminder_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action_id = Column(String, index=True)
    user_id = Column(String, index=True, default="default")
    channel = Column(String, default="whatsapp")
    message = Column(Text, default="")
    status = Column(String, default="queued")
    provider_message_id = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class DBDeviceToken(Base):
    __tablename__ = "device_tokens"
    token = Column(String, primary_key=True)
    user_id = Column(String, index=True, default="default")
    platform = Column(String, default="unknown")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# ── Engine & Helpers ──────────────────────────────────────────────────────────

IS_SQLITE = DATABASE_URL.startswith("sqlite")
engine = (
    create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    if IS_SQLITE
    else create_engine(DATABASE_URL)
)

# Enable WAL mode for SQLite concurrency
@event.listens_for(engine, "connect")
def set_wal(dbapi_conn, _):
    if IS_SQLITE:
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables on startup. Falls back to alembic for production."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── CRUD helpers ──────────────────────────────────────────────────────────────

def save_session(record: SessionRecord) -> None:
    with SessionLocal() as db:
        row = DBSession(
            session_id=record.session_id,
            user_id=record.user_id,
            timestamp=record.timestamp,
            loneliness_score=record.loneliness_score,
            connections_reported=json.dumps(record.connections_reported),
            actions_completed=record.actions_completed,
            actions_pending=json.dumps(record.actions_pending),
            mood_signal=record.mood_signal,
            crisis_flagged=record.crisis_flagged,
            nlp_profile_json=record.nlp_profile.model_dump_json() if record.nlp_profile else "{}",
            plan_json=record.plan.model_dump_json() if record.plan else "{}",
        )
        db.merge(row)
        db.commit()


def get_sessions(user_id: str = "default", limit: int = 50) -> List[DBSession]:
    with SessionLocal() as db:
        return (
            db.query(DBSession)
            .filter(DBSession.user_id == user_id)
            .order_by(DBSession.timestamp.desc())
            .limit(limit)
            .all()
        )


def save_message(user_id: str, role: str, content: str) -> None:
    with SessionLocal() as db:
        msg = DBMessage(user_id=user_id, role=role, content=content)
        db.add(msg)
        db.commit()


def get_messages(user_id: str = "default", limit: int = 40) -> List[DBMessage]:
    with SessionLocal() as db:
        return (
            db.query(DBMessage)
            .filter(DBMessage.user_id == user_id)
            .order_by(DBMessage.timestamp.asc())
            .limit(limit)
            .all()
        )


def get_or_create_profile(user_id: str = "default") -> DBUserProfile:
    with SessionLocal() as db:
        profile = db.query(DBUserProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = DBUserProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile


def update_profile_score(user_id: str, score: int) -> None:
    with SessionLocal() as db:
        profile = db.query(DBUserProfile).filter_by(user_id=user_id).first()
        if profile:
            if profile.baseline_score == 0:
                profile.baseline_score = score
            profile.current_score = score
            db.commit()
        else:
            db.add(DBUserProfile(
                user_id=user_id,
                current_score=score,
                baseline_score=score,
            ))
            db.commit()


def increment_connections(user_id: str, count: int = 1) -> None:
    with SessionLocal() as db:
        profile = db.query(DBUserProfile).filter_by(user_id=user_id).first()
        if profile:
            profile.total_connections += count
            db.commit()


def create_action_task(
    user_id: str,
    action_id: str,
    target: str,
    action_text: str,
    due_at: Optional[datetime] = None,
) -> None:
    with SessionLocal() as db:
        existing = db.query(DBActionTask).filter(DBActionTask.action_id == action_id).first()
        if existing:
            return
        row = DBActionTask(
            action_id=action_id,
            user_id=user_id,
            target=target,
            action_text=action_text,
            due_at=due_at,
        )
        db.add(row)
        db.commit()


def get_action_tasks(user_id: str = "default", status: Optional[str] = None, limit: int = 100) -> List[DBActionTask]:
    with SessionLocal() as db:
        q = db.query(DBActionTask).filter(DBActionTask.user_id == user_id)
        if status:
            q = q.filter(DBActionTask.status == status)
        return q.order_by(DBActionTask.created_at.desc()).limit(limit).all()


def get_latest_pending_action(user_id: str = "default") -> Optional[DBActionTask]:
    with SessionLocal() as db:
        return (
            db.query(DBActionTask)
            .filter(DBActionTask.user_id == user_id, DBActionTask.status == "pending")
            .order_by(DBActionTask.created_at.desc())
            .first()
        )


def complete_action_task(action_id: str, user_id: str = "default") -> bool:
    with SessionLocal() as db:
        row = db.query(DBActionTask).filter(
            DBActionTask.action_id == action_id,
            DBActionTask.user_id == user_id,
        ).first()
        if not row:
            return False
        row.status = "completed"
        row.completed_at = datetime.now(UTC)
        row.blocker_reason = ""
        row.micro_step = ""
        db.commit()
        return True


def block_action_task(
    action_id: str,
    blocker_reason: str,
    micro_step: str,
    user_id: str = "default",
    blocker_category: str = "unknown",
) -> bool:
    with SessionLocal() as db:
        row = db.query(DBActionTask).filter(
            DBActionTask.action_id == action_id,
            DBActionTask.user_id == user_id,
        ).first()
        if not row:
            return False
        row.status = "blocked"
        row.blocker_reason = blocker_reason
        row.blocker_category = blocker_category
        row.micro_step = micro_step
        db.commit()
        return True


def has_completed_action_since_last_session(user_id: str = "default") -> bool:
    with SessionLocal() as db:
        latest_pending = (
            db.query(DBActionTask)
            .filter(DBActionTask.user_id == user_id, DBActionTask.status == "pending")
            .order_by(DBActionTask.created_at.desc())
            .first()
        )
        latest_completed = (
            db.query(DBActionTask)
            .filter(DBActionTask.user_id == user_id, DBActionTask.status == "completed")
            .order_by(DBActionTask.completed_at.desc())
            .first()
        )
        if latest_completed is None or latest_completed.completed_at is None:
            return False
        if latest_pending is None:
            return True
        return latest_completed.completed_at >= latest_pending.created_at


def has_pending_actions(user_id: str = "default") -> bool:
    with SessionLocal() as db:
        return db.query(DBActionTask).filter(
            DBActionTask.user_id == user_id,
            DBActionTask.status == "pending",
        ).first() is not None


def create_reminder_event(
    action_id: str,
    user_id: str,
    message: str,
    status: str,
    provider_message_id: str = "",
    channel: str = "whatsapp",
) -> None:
    with SessionLocal() as db:
        row = DBReminderEvent(
            reminder_id=str(uuid.uuid4()),
            action_id=action_id,
            user_id=user_id,
            channel=channel,
            message=message,
            status=status,
            provider_message_id=provider_message_id,
        )
        db.add(row)
        db.commit()


def get_reminder_events(user_id: str = "default", limit: int = 100) -> List[DBReminderEvent]:
    with SessionLocal() as db:
        return (
            db.query(DBReminderEvent)
            .filter(DBReminderEvent.user_id == user_id)
            .order_by(DBReminderEvent.created_at.desc())
            .limit(limit)
            .all()
        )


def get_action_status_counts(user_id: str = "default") -> dict:
    with SessionLocal() as db:
        pending = db.query(DBActionTask).filter(DBActionTask.user_id == user_id, DBActionTask.status == "pending").count()
        completed = db.query(DBActionTask).filter(DBActionTask.user_id == user_id, DBActionTask.status == "completed").count()
        blocked = db.query(DBActionTask).filter(DBActionTask.user_id == user_id, DBActionTask.status == "blocked").count()
        return {"pending": pending, "completed": completed, "blocked": blocked}


def upsert_device_token(user_id: str, token: str, platform: str = "unknown") -> None:
    with SessionLocal() as db:
        row = db.query(DBDeviceToken).filter(DBDeviceToken.token == token).first()
        if row:
            row.user_id = user_id
            row.platform = platform
        else:
            row = DBDeviceToken(token=token, user_id=user_id, platform=platform)
            db.add(row)
        db.commit()


def get_device_tokens(user_id: str = "default") -> List[str]:
    with SessionLocal() as db:
        rows = db.query(DBDeviceToken).filter(DBDeviceToken.user_id == user_id).all()
        return [r.token for r in rows]
