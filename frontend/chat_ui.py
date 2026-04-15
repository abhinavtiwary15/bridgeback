"""Streamlit chat UI block for structured action output."""

from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components


def render_structured_action_ui(
    structured_data: dict, user_id: str = "default"
) -> bool:
    """
    Render priority person, action, message, resilience scenarios.
    Returns True when user clicks mark-done.
    """
    if not structured_data:
        st.info("No structured action available yet.")
        return False

    person = structured_data.get("priority_person", {})
    action = structured_data.get("action", "")
    message = structured_data.get("message", "")
    resilience = structured_data.get("resilience", {})

    st.subheader("Priority person")
    st.markdown(
        f"**{html.escape(str(person.get('name', 'Unknown')))}** "
        f"(score: {person.get('priority_score', 0)})\n\n"
        f"{html.escape(str(person.get('reason', '')))}"
    )

    st.subheader("Action")
    st.markdown(html.escape(action))

    st.subheader("Message")
    st.code(message, language="text")
    st.caption("Copy the message and send now.")
    components.html(
        f"""
        <button id="copy-btn" onclick="
                navigator.clipboard.writeText({message!r});
                const note = document.getElementById('copy-note');
                note.style.display='inline';
                setTimeout(() => note.style.display='none', 1200);
            "
                style="padding:8px 12px;border-radius:8px;border:1px solid #4a7c59;background:#f0f7f2;cursor:pointer;">
          Copy message
        </button>
        <span id="copy-note" style="display:none;margin-left:8px;color:#2e6b2e;font-weight:600;">Copied!</span>
        """,
        height=46,
    )

    st.subheader("Response scenarios")
    scenarios = resilience.get("scenarios", [])
    for scenario in scenarios:
        with st.container(border=True):
            st.markdown(f"**{scenario.get('type', '').replace('_', ' ').title()}**")
            st.markdown(f"Reply example: {scenario.get('example_reply', '')}")
            st.markdown(f"Meaning: {scenario.get('meaning', '')}")
            st.markdown(f"Next step: {scenario.get('next_step', '')}")

    return st.button("Mark as Done", key=f"mark_done_{user_id}")
