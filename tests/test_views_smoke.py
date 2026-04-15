"""Smoke tests for Streamlit rendering helpers."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.models import (
    NLPProfile,
    ReconnectionAction,
    ReconnectionPlan,
    RelationshipSignal,
)
from services import plan_view, progress_view


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _DummyStreamlit:
    def info(self, *_args, **_kwargs):
        return None

    def markdown(self, *_args, **_kwargs):
        return None

    def subheader(self, *_args, **_kwargs):
        return None

    def text_input(self, *_args, **_kwargs):
        return ""

    def button(self, *_args, **_kwargs):
        return False

    def caption(self, *_args, **_kwargs):
        return None

    def success(self, *_args, **_kwargs):
        return None

    def rerun(self):
        return None

    def columns(self, n):
        count = n if isinstance(n, int) else len(n)
        return [_DummyContext() for _ in range(count)]

    def plotly_chart(self, *_args, **_kwargs):
        return None


def test_render_plan_tab_smoke(monkeypatch):
    monkeypatch.setattr(plan_view, "st", _DummyStreamlit())
    monkeypatch.setattr(plan_view, "get_action_tasks", lambda **_kwargs: [])
    plan = ReconnectionPlan(
        priority_actions=[
            ReconnectionAction(
                type="reconnect_person",
                target="Priya",
                rationale="Important friendship to rebuild.",
                action="Send a short check-in message.",
                suggested_message="Hey Priya, thinking of you. Want to catch up this week?",
                difficulty="low",
                timeframe="today",
            )
        ],
        weekly_goal="Reach out to one real person this week.",
    )
    profile = NLPProfile(
        loneliness_score=62,
        relationship_signals=[
            RelationshipSignal(
                name="Priya",
                status="drifted",
                last_mentioned_context="We used to meet every weekend.",
            )
        ],
    )
    plan_view.render_plan_tab(plan=plan, profile=profile)


def test_render_progress_tab_smoke(monkeypatch):
    monkeypatch.setattr(progress_view, "st", _DummyStreamlit())
    monkeypatch.setattr(
        progress_view,
        "get_score_history",
        lambda _user_id: [{"date": "Apr 14", "score": 55}],
    )
    monkeypatch.setattr(progress_view, "get_streak", lambda _user_id: 2)
    monkeypatch.setattr(progress_view, "get_total_connections", lambda _user_id: 4)
    monkeypatch.setattr(
        progress_view,
        "generate_weekly_insight",
        lambda _user_id: "You completed 2 social actions this week.",
    )
    monkeypatch.setattr(
        progress_view,
        "get_relationship_health_map",
        lambda _user_id: [
            {"name": "Rahul", "status": "active", "context": "Spoke yesterday"}
        ],
    )
    monkeypatch.setattr(
        progress_view,
        "get_action_status_counts",
        lambda _user_id: {"completed": 2, "pending": 1, "blocked": 0},
    )
    monkeypatch.setattr(
        progress_view, "get_reminder_events", lambda _user_id, limit=200: []
    )
    progress_view.render_progress_tab(user_id="default", current_score=55)
