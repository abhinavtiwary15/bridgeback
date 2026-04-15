"""
BridgeBack — Layer 2: Conversation Engine
Supports FREE backends: Groq, Google Gemini, Ollama (local)
Also supports paid: Claude (Anthropic), OpenAI

FREE options:
  groq   → console.groq.com      (free account, no card needed)
  gemini → aistudio.google.com   (free API key, no card needed)
  ollama → run locally, zero cost (install from ollama.ai)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    DEFAULT_LLM,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    MAX_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_URL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from data.models import (
    LLMResponse,
    NLPProfile,
    ReconnectionAction,
    ReconnectionPlan,
    RelationshipSignal,
)
from llm.system_prompt import SYSTEM_PROMPT
from nlp.crisis_detector import build_crisis_response, detect_crisis
from services.priority_service import assign_priorities

logger = logging.getLogger(__name__)


_COMPANIONSHIP_PATTERNS = [
    r"\b(be my friend|be my companion|talk to me|stay with me)\b",
    r"\b(i just want to chat|keep me company|don'?t leave)\b",
    r"\b(you are my only friend|you are all i have)\b",
]


def _looks_like_companionship_request(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _COMPANIONSHIP_PATTERNS)


# ── Backend callers ───────────────────────────────────────────────────────────


def _call_groq(messages: List[Dict], system: str) -> str:
    """Groq — FREE tier. Get key at console.groq.com"""
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    full_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=MAX_TOKENS,
        messages=full_messages,
    )
    return response.choices[0].message.content


def _call_gemini(messages: List[Dict], system: str) -> str:
    """Google Gemini — FREE tier. Get key at aistudio.google.com"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY if GEMINI_API_KEY else "dummy_key_for_testing")

    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
        ),
    )
    return response.text


def _call_ollama(messages: List[Dict], system: str) -> str:
    """Ollama — 100% local, completely free. Install from ollama.ai"""
    import requests

    full_messages = [{"role": "system", "content": system}] + messages
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": full_messages,
            "stream": False,
            "options": {"num_predict": MAX_TOKENS},
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def _call_claude(messages: List[Dict], system: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _call_openai(messages: List[Dict], system: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    full_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=MAX_TOKENS,
        messages=full_messages,
    )
    return response.choices[0].message.content


def _call_llm(messages: List[Dict], system: str, backend: str) -> str:
    dispatch = {
        "groq": _call_groq,
        "gemini": _call_gemini,
        "ollama": _call_ollama,
        "claude": _call_claude,
        "openai": _call_openai,
    }
    fn = dispatch.get(backend, _call_groq)
    return fn(messages, system)


def get_available_backends() -> List[str]:
    """Return configured backends with required credentials/dependencies present."""
    available: List[str] = []
    if GROQ_API_KEY:
        available.append("groq")
    if GEMINI_API_KEY:
        available.append("gemini")
    # Ollama is local; keep available regardless of key state.
    available.append("ollama")
    if ANTHROPIC_API_KEY:
        available.append("claude")
    if OPENAI_API_KEY:
        available.append("openai")
    return available


# ── JSON parser ───────────────────────────────────────────────────────────────


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    return json.loads(cleaned)


def _build_nlp_profile(parsed: Dict) -> NLPProfile:
    sigs = [
        RelationshipSignal(
            name=r.get("name", ""),
            status=r.get("status", "unknown"),
            last_mentioned_context=r.get(
                "context", r.get("last_mentioned_context", "")
            ),
        )
        for r in parsed.get("relationship_signals", [])
    ]
    return NLPProfile(
        loneliness_score=parsed.get("loneliness_score") or 0,
        relationship_signals=sigs,
        drift_signals=parsed.get("drift_signals", []),
        social_anxiety_markers=parsed.get("social_anxiety_markers", []),
        connection_need_type=parsed.get("connection_need_type", "unknown"),
        connections_reported_count=max(
            0, int(parsed.get("connections_reported", 0) or 0)
        ),
        crisis_detected=parsed.get("crisis", False),
    )


def _build_plan(parsed: Dict) -> Optional[ReconnectionPlan]:
    plan_data = parsed.get("plan")
    if not plan_data:
        return None
    actions = [
        ReconnectionAction(
            type=a.get("type", "reconnect_person"),
            target=a.get("target", a.get("name", "")),
            rationale=a.get("rationale", ""),
            action=a.get("action", ""),
            suggested_message=a.get("suggested_message"),
            difficulty=a.get("difficulty", "low"),
            timeframe=a.get("timeframe", "this week"),
        )
        for a in plan_data.get("priority_actions", [])
    ]
    prioritized = assign_priorities(
        actions,
        relationship_signals=parsed.get("relationship_signals", []),
    )
    return ReconnectionPlan(
        priority_actions=prioritized,
        weekly_goal=plan_data.get("weekly_goal", ""),
    )


# ── Conversation Engine ───────────────────────────────────────────────────────


class ConversationEngine:
    def __init__(self, backend: str = DEFAULT_LLM):
        self.backend: str = backend
        self.history: List[Dict[str, str]] = []
        self.current_profile: Optional[NLPProfile] = None
        self.current_plan: Optional[ReconnectionPlan] = None
        self.last_action_assigned: str = ""
        self.action_completed: bool = True
        self.action_timestamp: Optional[datetime] = None

    def chat(self, user_message: str) -> LLMResponse:
        msg_lower = user_message.lower()
        if any(
            token in msg_lower
            for token in ["done", "completed", "sent it", "i sent", "finished"]
        ):
            self.action_completed = True

        if not self.action_completed and self.last_action_assigned:
            reminder_text = (
                f"You still have one pending action: {self.last_action_assigned} "
                "Send this now. Come back after you've done it. "
                "If something is blocking you, tell me in one line and I will reduce friction."
            )
            return LLMResponse(
                text=reminder_text,
                mode="COACHING",
                updated_profile=self.current_profile,
                updated_plan=self.current_plan,
            )

        # Crisis pre-screen (no LLM needed)
        is_crisis, _ = detect_crisis(user_message)
        if is_crisis:
            return LLMResponse(
                text=build_crisis_response(),
                mode="CRISIS",
                updated_profile=NLPProfile(
                    loneliness_score=self.current_profile.loneliness_score
                    if self.current_profile
                    else 85,
                    crisis_detected=True,
                ),
            )

        if _looks_like_companionship_request(user_message):
            person_name = None
            if self.current_profile and self.current_profile.relationship_signals:
                person_name = self.current_profile.relationship_signals[0].name
            person_name = person_name or "someone you trust"
            return LLMResponse(
                text=(
                    "I hear you, and I am glad you shared that. "
                    f"But I am not who you actually need right now. {person_name} is. "
                    "Let us focus on reconnecting with them, and I will help you with exactly what to say."
                ),
                mode="REDIRECT",
                updated_profile=self.current_profile,
                updated_plan=self.current_plan,
            )

        self.history.append({"role": "user", "content": user_message})

        if self.backend not in get_available_backends():
            return LLMResponse(
                text=(
                    f"The `{self.backend}` backend is not configured in this environment. "
                    "Choose an available backend in settings or add the required API key."
                ),
                mode="INTAKE",
            )

        try:
            raw = _call_llm(self.history, SYSTEM_PROMPT, self.backend)
        except ImportError as e:
            logger.exception("Backend dependency missing for %s", self.backend)
            return LLMResponse(
                text=(
                    f"Backend dependency missing for `{self.backend}`: {e}. "
                    "Install required package(s) and try again."
                ),
                mode="INTAKE",
            )
        except Exception as e:
            logger.exception("LLM backend call failed for %s", self.backend)
            return LLMResponse(
                text=f"Connection error: {e}. Please check your API key and try again.",
                mode="INTAKE",
            )

        self.history.append({"role": "assistant", "content": raw})

        try:
            parsed = _parse_llm_json(raw)
            profile = _build_nlp_profile(parsed)
            plan = _build_plan(parsed)
            self.current_profile = profile
            if plan:
                self.current_plan = plan
                if plan.priority_actions:
                    self.last_action_assigned = plan.priority_actions[0].action
                    self.action_completed = False
                    self.action_timestamp = datetime.now(UTC)
                message_text = parsed.get("message", raw)
                if self.last_action_assigned:
                    message_text = (
                        message_text
                        + "\n\nSend this now. Come back after you've done it."
                    )
            else:
                message_text = parsed.get("message", raw)
            return LLMResponse(
                text=message_text,
                mode=parsed.get("mode", "INTAKE"),
                updated_profile=profile,
                updated_plan=plan,
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.warning(
                "Model response was not valid BridgeBack JSON; returning raw text."
            )
            return LLMResponse(text=raw, mode="INTAKE")

    def clear_history(self):
        self.history = []
        self.current_profile = None
        self.current_plan = None
