"""
BridgeBack — Layer 5: Crisis Detector
Scans user text for acute distress signals.
If detected, BridgeBack immediately switches to referral mode.
"""

from __future__ import annotations

import re
from typing import Tuple

from config import CRISIS_KEYWORDS, CRISIS_RESOURCES

# ── Patterns ──────────────────────────────────────────────────────────────────

_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in CRISIS_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

_HOPELESSNESS_PATTERNS = [
    r"no(body| one) (would |will )?(care|miss me)",
    r"what('?s| is) the point",
    r"can'?t go on",
    r"i('?m| am) done",
    r"i('?ve| have) given up",
    r"i don'?t (want to|wanna) (be here|exist|live)",
]

_HOPELESSNESS_RE = re.compile("|".join(_HOPELESSNESS_PATTERNS), re.IGNORECASE)


# ── Public API ────────────────────────────────────────────────────────────────


def detect_crisis(text: str) -> Tuple[bool, list[str]]:
    """
    Returns (is_crisis, matched_signals).
    is_crisis=True means immediate escalation is required.
    """
    signals: list[str] = []

    keyword_matches = _KEYWORD_PATTERN.findall(text)
    if keyword_matches:
        signals.extend(keyword_matches)

    hope_matches = _HOPELESSNESS_RE.findall(text)
    if hope_matches:
        signals.extend([m for m in hope_matches if m])

    return bool(signals), signals


def get_crisis_resources(region: str = "IN") -> str:
    """Return formatted crisis resource string for the given region."""
    resources = CRISIS_RESOURCES.get(region.upper(), CRISIS_RESOURCES["DEFAULT"])
    lines = ["**Please reach out to one of these right now:**\n"]
    for name, contact in resources:
        lines.append(f"- **{name}**: {contact}")
    lines.append(
        "\nYou don't have to face this alone. "
        "These people are trained to help — please call or text now."
    )
    return "\n".join(lines)


def build_crisis_response(region: str = "IN") -> str:
    """Full crisis message BridgeBack will send."""
    resources = get_crisis_resources(region)
    return (
        "I hear you, and I'm really glad you said something. "
        "What you're feeling is real and it matters.\n\n"
        "I'm an AI and I'm not equipped to give you what you need right now — "
        "but real humans are, and they're ready for your call.\n\n"
        + resources
        + "\n\nIf there's someone in your life — a family member, a friend, "
        "anyone — please reach out to them right now too. "
        "You deserve real human support."
    )
