"""
BridgeBack — Layer 1: Drift Detector
Identifies linguistic markers indicating relationship drift —
past-tense references, hedging language, expressed distance.
"""

from __future__ import annotations
import re
from typing import List, Dict


_DRIFT_PATTERNS: Dict[str, str] = {
    "past_tense_reference":   r"\bwe used to\b|\bthey used to\b|\bi used to\b",
    "hedging_language":       r"\bhaven'?t (?:spoken|talked|seen|heard from|met|caught up)\b",
    "expressed_missing":      r"\b(?:miss|missing|thought about|think about)\b",
    "temporal_distance":      r"\b(?:a long time ago|ages ago|it'?s been a while|been months|been years)\b",
    "not_as_close":           r"\bnot as close\b|\bdrifted apart\b|\bgrew apart\b",
    "lost_touch":             r"\blost touch\b|\bfell out of touch\b",
    "last_contact_hedging":   r"\blast (?:time|we|i)\b|\ba (?:few|couple of) (?:months|years)\b",
    "social_withdrawal":      r"\bstay(?:ing)? home\b|\bavoid(?:ing)?\b|\bdon'?t go out\b",
}

_ANXIETY_PATTERNS: Dict[str, str] = {
    "fear_of_rejection":      r"\bafraid (?:to|they)\b|\bscared (?:to|they)\b|\bfear (?:of|that)\b",
    "low_self_efficacy":      r"\bdon'?t know what to say\b|\bwouldn'?t know how\b|\bnot sure how\b",
    "avoidance_language":     r"\bcan'?t bring myself\b|\bjust can'?t\b|\btoo (?:anxious|nervous|awkward)\b",
    "paralysis":              r"\bkeep putting it off\b|\bkept meaning to\b|\bmeant to reach out\b",
}

_COMPILED_DRIFT    = {k: re.compile(v, re.IGNORECASE) for k, v in _DRIFT_PATTERNS.items()}
_COMPILED_ANXIETY  = {k: re.compile(v, re.IGNORECASE) for k, v in _ANXIETY_PATTERNS.items()}


def detect_drift_signals(text: str) -> List[str]:
    """Return list of drift signal labels found in text."""
    return [label for label, pattern in _COMPILED_DRIFT.items() if pattern.search(text)]


def detect_anxiety_markers(text: str) -> List[str]:
    """Return list of social anxiety marker labels found in text."""
    return [label for label, pattern in _COMPILED_ANXIETY.items() if pattern.search(text)]


def classify_connection_need(text: str) -> str:
    """
    Classify what type of connection the user most needs.
    Returns one of: deep_friendship | community_belonging |
                    family_reconnection | romantic | professional | unknown
    """
    text_lower = text.lower()

    family_keywords   = ["family", "mom", "mum", "dad", "brother", "sister",
                         "parents", "relatives", "cousin", "aunt", "uncle"]
    romantic_keywords = ["partner", "girlfriend", "boyfriend", "dating",
                         "relationship", "romantic", "love"]
    community_keywords= ["community", "belong", "group", "club", "meetup",
                         "event", "people", "strangers", "new friends"]
    professional_keywords = ["colleagues", "coworkers", "work friends",
                              "networking", "office", "team"]

    if any(w in text_lower for w in family_keywords):
        return "family_reconnection"
    if any(w in text_lower for w in romantic_keywords):
        return "romantic"
    if any(w in text_lower for w in professional_keywords):
        return "professional"
    if any(w in text_lower for w in community_keywords):
        return "community_belonging"

    # Default to deep_friendship if drift/loneliness signals are present
    if detect_drift_signals(text):
        return "deep_friendship"

    return "unknown"
