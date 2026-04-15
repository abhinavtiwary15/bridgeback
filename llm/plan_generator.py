"""
BridgeBack — Layer 3: Reconnection Plan Generator
Combines drifted relationships + community events into a ranked,
low-barrier action plan. References specific people and places.
"""

from __future__ import annotations
from typing import List, Optional

from data.models import NLPProfile, ReconnectionPlan, ReconnectionAction
from llm.message_drafter import draft_outreach_message
from llm.rejection_trainer import generate_resilience_block
from tracking.priority_engine import rank_relationships
from community.event_matcher import find_events
from config import DEFAULT_LLM


def generate_plan(
    profile: NLPProfile,
    location: str = "",
    interests: Optional[List[str]] = None,
    backend: str = DEFAULT_LLM,
) -> ReconnectionPlan:
    """
    Build a personalised ReconnectionPlan from the user's NLP profile.

    Strategy:
    1. Drifted relationships → specific outreach actions with message drafts
    2. Active relationships  → lower-priority check-in actions
    3. Community events      → matched to interests + location
    4. Ranked by difficulty ascending (lowest barrier first)
    """
    actions: List[ReconnectionAction] = []

    # ── Step 1: Drifted relationships (highest priority) ──────────────────
    drifted = [r for r in profile.relationship_signals if r.status == "drifted"]
    for rel in drifted[:3]:          # cap at 3 reconnect actions
        message = draft_outreach_message(
            target_name=rel.name,
            relationship_context=rel.last_mentioned_context,
            backend=backend,
        )
        actions.append(ReconnectionAction(
            type="reconnect_person",
            target=rel.name,
            rationale=(
                f"You mentioned drifting from {rel.name}. "
                f"Context: \"{rel.last_mentioned_context}\""
            ),
            action=f"Send a message to {rel.name} today.",
            suggested_message=message,
            difficulty="low",
            timeframe="today",
        ))

    # ── Step 2: Active relationships (check-in nudge) ─────────────────────
    active = [r for r in profile.relationship_signals if r.status == "active"]
    for rel in active[:1]:           # just one, don't overwhelm
        actions.append(ReconnectionAction(
            type="reconnect_person",
            target=rel.name,
            rationale=f"Keep the momentum going with {rel.name}.",
            action=f"Plan something concrete with {rel.name} this week.",
            suggested_message=None,
            difficulty="low",
            timeframe="this week",
        ))

    # ── Step 3: Community events ──────────────────────────────────────────
    events = find_events(interests or [], location=location, limit=2)
    for event in events:
        actions.append(ReconnectionAction(
            type="community_event",
            target=event["name"],
            rationale=(
                f"Low-pressure environment to meet new people. "
                f"{event.get('rsvp_count', 0)} people attending."
            ),
            action=(
                f"Attend {event['name']} at {event.get('venue', 'local venue')} — "
                f"{event.get('date', '')} {event.get('time', '')}."
            ),
            suggested_message=None,
            difficulty="medium",
            timeframe="this week",
            registration_link=event.get("registration_link"),
        ))

    # ── Step 4: Rank by difficulty ────────────────────────────────────────
    order = {"low": 0, "medium": 1, "high": 2}
    actions.sort(key=lambda a: order.get(a.difficulty, 1))

    # ── Step 5: Weekly goal ───────────────────────────────────────────────
    n_actions = min(len(actions), 2)
    if drifted:
        goal = f"Reach out to {drifted[0].name}" + (
            f" and {drifted[1].name}" if len(drifted) > 1 else ""
        ) + " this week."
    elif events:
        goal = f"Attend {events[0]['name']} and report back next session."
    else:
        goal = f"Complete {n_actions} social action{'s' if n_actions != 1 else ''} this week."

    return ReconnectionPlan(
        priority_actions=actions[:4],   # hard cap at 4
        weekly_goal=goal,
    )


def generate_structured_action_response(
    profile: NLPProfile,
    backend: str = DEFAULT_LLM,
) -> dict:
    """
    New one-action-only structured format for enforcement-first flow.
    """
    nlp_profile_dict = profile.model_dump()
    ranked = rank_relationships(nlp_profile_dict)

    if ranked:
        person = ranked[0]
        target_name = person["name"]
        rel_context = ""
        for rel in profile.relationship_signals:
            if rel.name == target_name:
                rel_context = rel.last_mentioned_context
                break
        drafted_message = draft_outreach_message(
            target_name=target_name,
            relationship_context=rel_context,
            backend=backend,
        )
        action_text = f"Send this message to {target_name} now."
    else:
        person = {"name": "someone you trust", "priority_score": 0.4, "reason": "No clear relationship extracted yet"}
        target_name = person["name"]
        drafted_message = "Hey, it has been a while. Want to catch up for 15 minutes this week?"
        action_text = "Send this message now to one person you trust."

    resilience = generate_resilience_block(target_name, drafted_message, backend=backend)

    return {
        "priority_person": person,
        "action": action_text,
        "message": drafted_message,
        "resilience": resilience,
        "enforcement": "Send this now and come back after.",
    }
