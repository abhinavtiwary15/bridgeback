"""Rendering helpers for the plan tab."""

from __future__ import annotations

import html

import streamlit as st

from data.database import block_action_task, complete_action_task, get_action_tasks
from data.models import NLPProfile, ReconnectionPlan
from services.accountability_service import generate_micro_step


def render_plan_tab(
    plan: ReconnectionPlan | None, profile: NLPProfile | None, user_id: str = "default"
) -> None:
    if not plan:
        st.info(
            "Complete a coaching session to generate your personalised reconnection plan."
        )
        return

    action_rows = get_action_tasks(user_id=user_id, limit=200)
    status_by_id = {row.action_id: row for row in action_rows}

    if plan.weekly_goal:
        st.markdown(
            f"<div class='insight-box'>🎯 <strong>This week's goal:</strong> {html.escape(plan.weekly_goal)}</div>",
            unsafe_allow_html=True,
        )

    st.subheader("Priority actions")
    for i, action in enumerate(plan.priority_actions):
        row = status_by_id.get(action.action_id)
        status = row.status if row else "pending"
        is_reach = action.type == "reconnect_person"
        card_class = "action-card" if is_reach else "action-card event"
        icon = "👤" if is_reach else "📍"
        diff_color = "#2e7a2e" if action.difficulty == "low" else "#a04400"
        status_color = {
            "completed": "#2e7a2e",
            "blocked": "#b83a3a",
            "pending": "#8a6800",
        }.get(status, "#8a6800")
        suggested = (
            f"<div class='suggested-msg'>💬 \"{html.escape(action.suggested_message)}\"</div>"
            if action.suggested_message
            else ""
        )
        st.markdown(
            f"""
            <div class='{card_class}'>
              <strong>{icon} {html.escape(action.target)}</strong>
              <span style='float:right;font-size:0.8em;color:{diff_color};'>{action.difficulty} effort</span><br/>
              {html.escape(action.action)}<br/>
              <em style='font-size:0.85em;color:#666;'>{html.escape(action.rationale)}</em>
              <div style='margin-top:6px;font-size:0.8em;color:{status_color};'><strong>Status:</strong> {status.title()}</div>
              <div style='margin-top:4px;font-size:0.8em;color:#4a7c59;'><strong>Priority score:</strong> {action.priority_score}</div>
              {suggested}
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1, 3])
        with c1:
            if (
                row
                and status != "completed"
                and st.button("Mark done", key=f"done_{i}_{row.action_id}")
            ):
                complete_action_task(row.action_id, user_id=user_id)
                st.success("Great work. Action marked as completed.")
                st.rerun()
        with c2:
            if row and status == "pending":
                blocker = st.text_input(
                    "Blocker (optional):",
                    key=f"blocker_{i}_{row.action_id}",
                    placeholder="Example: I am anxious they may not reply.",
                )
                if blocker and st.button(
                    "Save blocker + micro-step", key=f"save_blocker_{i}_{row.action_id}"
                ):
                    micro_step = generate_micro_step(blocker)
                    block_action_task(
                        row.action_id,
                        blocker_reason=blocker,
                        micro_step=micro_step,
                        user_id=user_id,
                    )
                    st.info(f"Micro-step: {micro_step}")
                    st.rerun()

        if row and row.status == "blocked" and row.micro_step:
            st.caption(f"Micro-step: {row.micro_step}")

    if profile and profile.relationship_signals:
        st.subheader("People in your life")
        cols = st.columns(min(len(profile.relationship_signals), 3))
        for i, rel in enumerate(profile.relationship_signals):
            with cols[i % 3]:
                status_color = "#b83a3a" if rel.status == "drifted" else "#4a7c59"
                st.markdown(
                    f"""
                    <div style='background:#f9f7f2;border:0.5px solid #ddd;border-radius:10px;padding:10px;'>
                      <strong>{html.escape(rel.name)}</strong><br/>
                      <span style='color:{status_color};font-size:0.85em;'>
                        {"⚠ Drifted" if rel.status == "drifted" else "✓ Active"}
                      </span><br/>
                      <span style='font-size:0.8em;color:#888;'>{html.escape(rel.last_mentioned_context)}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        "<br/><div style='color:#888;font-size:0.85em;text-align:center;'>"
        "⚠️ Don't open BridgeBack again until you've completed at least one action above."
        "</div>",
        unsafe_allow_html=True,
    )
