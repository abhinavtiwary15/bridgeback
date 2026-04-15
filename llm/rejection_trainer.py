"""Rejection Resilience Trainer."""

from __future__ import annotations

import json

from config import DEFAULT_LLM, ANTHROPIC_API_KEY, OPENAI_API_KEY, CLAUDE_MODEL, OPENAI_MODEL

_SYSTEM = """
You are a practical social confidence coach.
Normalize fear of rejection in one short paragraph.
Do not use therapy language.
Keep everything concise and actionable.
Return strict JSON:
{
  "message":"...",
  "scenarios":[
    {"type":"positive","example_reply":"...","meaning":"...","next_step":"..."},
    {"type":"neutral","example_reply":"...","meaning":"...","next_step":"..."},
    {"type":"no_response","example_reply":"...","meaning":"...","next_step":"..."}
  ]
}
"""


def _fallback(person_name: str) -> dict:
    return {
        "message": "Fear of rejection is normal. One message does not define your worth; it only opens a door.",
        "scenarios": [
            {
                "type": "positive",
                "example_reply": f"Hey! Great to hear from you. Let's meet this week.",
                "meaning": f"{person_name} is open to reconnecting.",
                "next_step": "Confirm a simple time and place."
            },
            {
                "type": "neutral",
                "example_reply": "Hey, busy this week. Maybe later.",
                "meaning": "Not a rejection, just low availability.",
                "next_step": "Reply once with a low-pressure option for next week."
            },
            {
                "type": "no_response",
                "example_reply": "No reply for several days.",
                "meaning": "Silence is data, not proof of failure.",
                "next_step": "Wait 5-7 days, send one gentle follow-up, then move to another person."
            },
        ],
    }


def generate_resilience_block(person_name: str, message: str, backend: str = DEFAULT_LLM) -> dict:
    prompt = (
        f"Person name: {person_name}\n"
        f"Draft message: {message}\n"
        "Generate the resilience block now."
    )
    try:
        if backend == "openai" and OPENAI_API_KEY:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=500,
                messages=[{"role": "system", "content": _SYSTEM}, {"role": "user", "content": prompt}],
            )
            text = resp.choices[0].message.content
        elif ANTHROPIC_API_KEY:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=500,
                system=_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text
        else:
            return _fallback(person_name)

        cleaned = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        return _fallback(person_name)
