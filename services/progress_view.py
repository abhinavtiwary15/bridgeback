"""Rendering helpers for the progress tab."""

from __future__ import annotations

import html
import streamlit as st
import plotly.graph_objects as go

from tracking.tracker import (
    get_score_history,
    get_streak,
    get_total_connections,
    generate_weekly_insight,
    get_relationship_health_map,
)
from data.database import get_action_status_counts, get_reminder_events


def render_progress_tab(user_id: str, current_score: int | None) -> None:
    history = get_score_history(user_id)
    streak = get_streak(user_id)
    total_c = get_total_connections(user_id)
    insight = generate_weekly_insight(user_id)
    action_counts = get_action_status_counts(user_id)
    reminders = get_reminder_events(user_id, limit=200)
    sent_or_mocked = sum(1 for r in reminders if r.status in {"sent", "mocked"})
    adherence = 0
    if sent_or_mocked:
        adherence = int((action_counts["completed"] / sent_or_mocked) * 100)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        score_display = current_score if current_score is not None else "—"
        st.markdown(
            f"<div class='metric-card'><div class='metric-val'>{score_display}</div><div class='metric-lbl'>Current score</div></div>",
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"<div class='metric-card'><div class='metric-val'>{total_c}</div><div class='metric-lbl'>Connections made</div></div>",
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"<div class='metric-card'><div class='metric-val'>{streak}</div><div class='metric-lbl'>Action streak</div></div>",
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"<div class='metric-card'><div class='metric-val'>{adherence}%</div><div class='metric-lbl'>Check-in adherence</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"<div class='insight-box'>💡 {html.escape(insight)}</div>", unsafe_allow_html=True)
    st.caption(
        f"Action lifecycle: {action_counts['completed']} completed, "
        f"{action_counts['pending']} pending, {action_counts['blocked']} blocked."
    )

    st.subheader("Loneliness score over time")
    if history:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[h["date"] for h in history],
                y=[h["score"] for h in history],
                mode="lines+markers",
                line=dict(color="#4a7c59", width=2),
                marker=dict(size=8, color="#4a7c59"),
                fill="tozeroy",
                fillcolor="rgba(74,124,89,0.08)",
                name="Loneliness score",
            )
        )
        fig.add_hline(y=20, line_dash="dot", line_color="#4a7c59", annotation_text="Goal: below 20")
        fig.update_layout(
            yaxis=dict(range=[0, 100], title="Score"),
            xaxis=dict(title="Session"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=False,
            height=280,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete your first session to see your score trend.")

    st.subheader("Relationship health map")
    rel_map = get_relationship_health_map(user_id)
    if rel_map:
        cols = st.columns(min(len(rel_map), 4))
        for i, rel in enumerate(rel_map):
            with cols[i % 4]:
                status = rel.get("status", "unknown")
                colour = "#b83a3a" if status == "drifted" else "#4a7c59"
                emoji = "⚠" if status == "drifted" else "✓"
                name = html.escape(str(rel.get("name", "")))
                context = html.escape(str(rel.get("context", "")))
                st.markdown(
                    f"""
                    <div style='background:#f9f7f2;border-radius:10px;padding:10px;text-align:center;'>
                      <div style='font-size:1.5rem;'>{emoji}</div>
                      <div style='font-weight:500;'>{name}</div>
                      <div style='color:{colour};font-size:0.8em;'>{status.title()}</div>
                      <div style='color:#888;font-size:0.75em;margin-top:4px;'>{context}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Relationship map builds as you share more in your sessions.")
