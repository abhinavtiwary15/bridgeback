"""
BridgeBack — Streamlit Frontend (API Client)
Main entry point for Hugging Face Spaces deployment.
Run: streamlit run app.py
"""

import streamlit as st
import html
import requests
import os
import json
import logging
from abc import ABC, abstractmethod

# Internal imports for Local/Standalone mode
try:
    from tracking.tracker import (
        get_score_history, get_streak, get_total_connections, 
        generate_weekly_insight
    )
    from data.database import (
        init_db, get_db, DBUser, 
        get_action_tasks, complete_action_task, block_action_task,
        get_sessions, get_action_status_counts
    )
    from api.dependencies import (
        authenticate_user, get_password_hash, create_access_token, 
        get_engine_for_user
    )
    from services.chat_service import process_user_message
    from services.accountability_service import generate_micro_step
    from llm.plan_generator import generate_structured_action_response
    HAS_LOCAL_DEPS = True
except ImportError:
    HAS_LOCAL_DEPS = False

APP_TITLE = "BridgeBack"
APP_SUBTITLE = "Reconnect with real people"

# Support for hybrid deployment
API_BASE_URL = os.getenv("API_BASE_URL", "")
STANDALONE_MODE = os.getenv("STANDALONE_MODE", "true").lower() == "true"

# ── Backend Interface ────────────────────────────────────────────────────────
class Backend(ABC):
    @abstractmethod
    def login(self, username, password): pass
    @abstractmethod
    def register(self, username, password, telegram_id): pass
    @abstractmethod
    def chat(self, user_id, message, llm_backend): pass
    @abstractmethod
    def fetch_plan(self, user_id): pass
    @abstractmethod
    def update_action(self, user_id, action_id, status, blocker_reason=""): pass
    @abstractmethod
    def fetch_progress(self, user_id): pass

class RemoteBackend(Backend):
    def login(self, username, password):
        return requests.post(f"{API_BASE_URL}/auth/token", data={"username": username, "password": password})
    
    def register(self, username, password, telegram_id):
        return requests.post(f"{API_BASE_URL}/auth/register", json={"username": username, "password": password, "telegram_chat_id": telegram_id})
    
    def chat(self, user_id, message, llm_backend):
        return requests.post(f"{API_BASE_URL}/chat", json={"user_id": user_id, "message": message, "backend": llm_backend}, headers=self._headers())
    
    def fetch_plan(self, user_id):
        r = requests.get(f"{API_BASE_URL}/plan", params={"user_id": user_id}, headers=self._headers())
        return r.json().get("actions", []) if r.status_code == 200 else []
    
    def update_action(self, user_id, action_id, status, blocker_reason=""):
        return requests.post(f"{API_BASE_URL}/plan/action", json={"user_id": user_id, "action_id": action_id, "status": status, "blocker_reason": blocker_reason}, headers=self._headers())
    
    def fetch_progress(self, user_id):
        r = requests.get(f"{API_BASE_URL}/progress", params={"user_id": user_id}, headers=self._headers())
        return r.json() if r.status_code == 200 else {}

    def _headers(self):
        return {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.get("access_token") else {}

class LocalBackend(Backend):
    def __init__(self):
        init_db()

    def login(self, username, password):
        with next(get_db()) as db:
            user = authenticate_user(db, username, password)
            if user:
                token = create_access_token(data={"sub": str(user.id)})
                return type('Res', (object,), {"status_code": 200, "json": lambda: {"access_token": token}})()
            return type('Res', (object,), {"status_code": 401})()

    def register(self, username, password, telegram_id):
        with next(get_db()) as db:
            existing = db.query(DBUser).filter(DBUser.username == username).first()
            if existing: return type('Res', (object,), {"status_code": 400, "json": lambda: {"detail": "User exists"}})()
            hashed = get_password_hash(password)
            user = DBUser(username=username, hashed_password=hashed, telegram_chat_id=telegram_id)
            db.add(user)
            db.commit()
            return type('Res', (object,), {"status_code": 200})()

    def chat(self, user_id, message, llm_backend):
        engine = get_engine_for_user(user_id, backend=llm_backend)
        result, response = process_user_message(engine=engine, user_id=user_id, user_text=message)
        structured = {}
        if response.updated_profile:
            structured = generate_structured_action_response(response.updated_profile, backend=engine.backend)
        data = {"response_text": result.assistant_text, "structured_data": structured, "mode": response.mode}
        return type('Res', (object,), {"status_code": 200, "json": lambda: data})()

    def fetch_plan(self, user_id):
        rows = get_action_tasks(user_id=user_id, limit=100)
        return [{"action_id": r.action_id, "target": r.target, "action_text": r.action_text, "status": r.status, "blocker_reason": r.blocker_reason or "", "micro_step": r.micro_step or ""} for r in rows]

    def update_action(self, user_id, action_id, status, blocker_reason=""):
        if status == "completed":
            complete_action_task(action_id, user_id=user_id)
        else:
            ms = generate_micro_step(blocker_reason)
            block_action_task(action_id, blocker_reason=blocker_reason, micro_step=ms, user_id=user_id)
        return type('Res', (object,), {"status_code": 200})()

    def fetch_progress(self, user_id):
        return {
            "streak": get_streak(user_id),
            "total_connections": get_total_connections(user_id),
            "insight": generate_weekly_insight(user_id),
            "action_status": get_action_status_counts(user_id),
            "history": get_score_history(user_id)
        }

# ── Initialization ───────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="🌉", layout="wide", initial_sidebar_state="collapsed")

# Detect backend
if API_BASE_URL:
    st.session_state._backend_impl = RemoteBackend()
    backend_mode_label = "Remote API"
elif HAS_LOCAL_DEPS:
    st.session_state._backend_impl = LocalBackend()
    backend_mode_label = "Standalone (Local)"
else:
    st.error("No API_BASE_URL found and local dependencies missing. Check your installation.")
    st.stop()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }
  .stChatMessage { border-radius: 12px; margin-bottom: 0.5rem; }
  .score-pill { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 14px; font-weight: 500; margin: 2px; }
  .score-minimal  { background: #e8f5e8; color: #2e6b2e; }
  .score-mild     { background: #fff8e1; color: #8a6800; }
  .score-moderate { background: #fff3e0; color: #a04400; }
  .score-severe   { background: #fce4ec; color: #8b1a35; }
  .score-acute    { background: #ffebee; color: #7a1a1a; }
  .action-card { background: #f9f7f2; border-left: 3px solid #4a7c59; border-radius: 8px; padding: 12px 16px; margin: 8px 0; }
  .metric-card { background: #f0f7f2; border-radius: 10px; padding: 16px; text-align: center; }
  .metric-val { font-family: 'DM Serif Display', serif; font-size: 2.5rem; color: #4a7c59; }
  .metric-lbl { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# State
if "access_token" not in st.session_state: st.session_state.access_token = None
if "user_id" not in st.session_state: st.session_state.user_id = None
if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "I'm BridgeBack. Have you felt distant from anyone recently?"}]
if "current_score" not in st.session_state: st.session_state.current_score = None
if "backend" not in st.session_state: st.session_state.backend = os.getenv("DEFAULT_LLM", "gemini")

def handle_login(username, password):
    res = st.session_state._backend_impl.login(username, password)
    if res.status_code == 200:
        st.session_state.access_token = res.json()["access_token"]
        st.session_state.user_id = username
        st.rerun()
    else: st.error("Invalid credentials")

def handle_register(username, password, telegram_chat_id):
    res = st.session_state._backend_impl.register(username, password, telegram_chat_id)
    if res.status_code == 200: st.success("Registered! You can now log in.")
    else: st.error(res.json().get("detail", "Registration failed") if hasattr(res, 'json') else "Registration failed")

# ── Auth UI View ─────────────────────────────────────────────────────────────
if not st.session_state.access_token:
    st.markdown(f"# 🌉 {APP_TITLE}")
    st.caption(APP_SUBTITLE)
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Login"): handle_login(u, p)
    with tab2:
        ru = st.text_input("Username", key="r_u")
        rp = st.text_input("Password", type="password", key="r_p")
        rchat_id = st.text_input("Telegram Chat ID", key="r_tg")
        if st.button("Register"): handle_register(ru, rp, rchat_id)
    st.stop()

# ── Main App View ────────────────────────────────────────────────────────────
col_logo, col_score = st.columns([3, 2])
with col_logo:
    st.markdown(f"# 🌉 {APP_TITLE}")
    st.caption(f"Logged in as: {st.session_state.user_id} | Mode: {backend_mode_label}")
    if st.button("Logout"):
        st.session_state.access_token = None
        st.rerun()

with col_score:
    if st.session_state.current_score is not None:
        score = st.session_state.current_score
        band, css = ("Minimal", "score-minimal") if score <= 20 else ("Mild", "score-mild") if score <= 40 else ("Moderate", "score-moderate") if score <= 60 else ("Severe", "score-severe") if score <= 80 else ("Acute", "score-acute")
        st.markdown(f"**Score** <span class='score-pill {css}'>{score} — {band}</span>", unsafe_allow_html=True)
        st.progress(score / 100)

st.divider()
tab_chat, tab_plan, tab_progress = st.tabs(["💬 Coach", "📋 My Plan", "📈 Progress"])

with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    user_input = st.chat_input("Tell me what's been going on…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)
        with st.spinner("Thinking..."):
            res = st.session_state._backend_impl.chat(st.session_state.user_id, user_input, st.session_state.backend)
            if res.status_code == 200:
                data = res.json()
                bot_msg = data.get("response_text", "Sorry, error.")
                st.session_state.messages.append({"role": "assistant", "content": bot_msg})
                with st.chat_message("assistant"): st.markdown(bot_msg)
            else: st.error("Failed to connect to backend.")

with tab_plan:
    actions = st.session_state._backend_impl.fetch_plan(st.session_state.user_id)
    if not actions: st.info("No actions in your plan yet.")
    else:
        for a in actions:
            st.markdown(f"<div class='action-card'><h4>{html.escape(a['target'])}</h4><p>Status: {a['status']}</p><p><strong>Action:</strong> {html.escape(a['action_text'])}</p></div>", unsafe_allow_html=True)
            if a["status"] == "pending":
                if st.button("Mark Completed", key=f"comp_{a['action_id']}"):
                    st.session_state._backend_impl.update_action(st.session_state.user_id, a["action_id"], "completed")
                    st.rerun()

with tab_progress:
    prog = st.session_state._backend_impl.fetch_progress(st.session_state.user_id)
    if prog:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><div class='metric-val'>{prog.get('total_connections', 0)}</div><div class='metric-lbl'>Connections</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-val'>{prog.get('streak', 0)}</div><div class='metric-lbl'>Wk Streak</div></div>", unsafe_allow_html=True)
        st.markdown(f"**Insight:** {html.escape(prog.get('insight', ''))}")

st.sidebar.markdown("### Settings")
backend_opts = ["groq", "gemini", "ollama", "claude", "openai"]
st.session_state.backend = st.sidebar.selectbox("Backend", backend_opts, index=backend_opts.index(st.session_state.backend) if st.session_state.backend in backend_opts else 1)
