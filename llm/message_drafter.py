"""
BridgeBack — Layer 3: Message Drafter
Generates specific, warm outreach messages for drifted relationships.
Uses the LLM to write personalised drafts given relationship context.
"""

from __future__ import annotations
from config import DEFAULT_LLM, ANTHROPIC_API_KEY, OPENAI_API_KEY, CLAUDE_MODEL, OPENAI_MODEL

_DRAFTER_SYSTEM = """
You are a warm, human message-writing assistant.
Given information about a drifted friendship or relationship, write a short, natural,
non-cringe outreach message the user can send TODAY.

Rules:
- Keep it under 3 sentences.
- Sound like a real person, not a therapist or a greeting card.
- Don't over-explain. Just a casual, genuine reach-out.
- Reference something specific about the relationship if context is given.
- End with a low-pressure invitation (coffee, call, catch-up).
- Respond with ONLY the message text. No quotes, no preamble.
"""


def draft_outreach_message(
    target_name: str,
    relationship_context: str = "",
    user_name: str = "",
    backend: str = DEFAULT_LLM,
) -> str:
    """
    Generate a personalised outreach message draft.

    Args:
        target_name:          Name of the person to reach out to.
        relationship_context: What the user said about this person.
        user_name:            User's name (optional, for personalisation).
        backend:              "claude" | "openai"

    Returns:
        A short, ready-to-send message string.
    """
    prompt = f"Write a message from {user_name or 'me'} to {target_name}."
    if relationship_context:
        prompt += f"\nContext about {target_name}: {relationship_context}"

    try:
        if backend == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=150,
                messages=[
                    {"role": "system", "content": _DRAFTER_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=150,
                system=_DRAFTER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()

    except Exception:
        # Graceful fallback
        return (
            f"Hey {target_name}, been thinking about you lately! "
            "Hope you're doing well — would love to catch up soon. "
            "Want to grab coffee or jump on a quick call this week?"
        )
