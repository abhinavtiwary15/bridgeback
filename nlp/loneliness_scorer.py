"""
BridgeBack — Layer 1: Loneliness Scorer
Estimates a 0–100 loneliness score calibrated against the UCLA Loneliness Scale.

Primary path  : HuggingFace BERT model (sentence-transformers).
Fallback path : Rule-based keyword scoring (no ML dependencies required).
The fallback activates automatically when torch/transformers are not installed,
making the app runnable on Hugging Face Spaces free tier without GPU.
"""

from __future__ import annotations
import re
from typing import Optional
from functools import lru_cache

# ── UCLA Loneliness Scale anchor phrases ─────────────────────────────────────
# These represent the 20-item scale's linguistic signatures.

_HIGH_LONELINESS_PHRASES = [
    "feel alone", "feel lonely", "no one understands", "no one cares",
    "nobody to talk to", "no close friends", "isolated", "left out",
    "no one to turn to", "feel empty", "don't belong", "no real friends",
    "no one notices", "disconnected", "invisible", "drifted apart",
    "haven't spoken", "used to be friends", "lost touch", "miss them",
    "no social life", "never invited", "feel unwanted", "feel forgotten",
]

_LOW_LONELINESS_PHRASES = [
    "close friends", "good support", "family around", "people who care",
    "hang out", "social plans", "see friends", "feel connected",
    "not alone", "strong relationships", "lots of friends",
]

_DRIFT_MARKERS = [
    r"we used to", r"haven'?t (spoken|talked|seen|heard from)",
    r"lost touch", r"drifted", r"not as close", r"a long time ago",
    r"used to hang", r"used to talk", r"been a while",
]

_ANXIETY_MARKERS = [
    r"too anxious", r"too scared", r"afraid to reach out",
    r"don'?t know what to say", r"might reject",
    r"awkward", r"nervous about", r"can'?t bring myself",
]

_DRIFT_RE   = re.compile("|".join(_DRIFT_MARKERS),   re.IGNORECASE)
_ANXIETY_RE = re.compile("|".join(_ANXIETY_MARKERS), re.IGNORECASE)


@lru_cache(maxsize=1)
def _get_sentence_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def _rule_based_score(text: str) -> int:
    """Lightweight keyword scoring. Returns 0–100."""
    text_lower = text.lower()
    score = 40  # neutral baseline

    for phrase in _HIGH_LONELINESS_PHRASES:
        if phrase in text_lower:
            score += 6

    for phrase in _LOW_LONELINESS_PHRASES:
        if phrase in text_lower:
            score -= 7

    drift_hits   = len(_DRIFT_RE.findall(text))
    anxiety_hits = len(_ANXIETY_RE.findall(text))
    score += drift_hits * 5
    score += anxiety_hits * 4

    # penalise very short messages (insufficient signal)
    if len(text.split()) < 10:
        score = max(score - 10, 20)

    return max(0, min(100, score))


def _bert_score(text: str) -> Optional[int]:
    """
    Attempt BERT-based scoring using sentence-transformers.
    Returns None if dependencies unavailable.
    """
    try:
        from sentence_transformers import util
        model = _get_sentence_model()

        anchor_lonely   = "I feel very lonely and have no one to talk to or spend time with."
        anchor_connected = "I have close friends and feel connected and supported by the people in my life."

        emb_text      = model.encode(text, convert_to_tensor=True)
        emb_lonely    = model.encode(anchor_lonely,    convert_to_tensor=True)
        emb_connected = model.encode(anchor_connected, convert_to_tensor=True)

        sim_lonely    = float(util.cos_sim(emb_text, emb_lonely))
        sim_connected = float(util.cos_sim(emb_text, emb_connected))

        # Map similarity differential to 0–100
        raw = (sim_lonely - sim_connected + 1) / 2  # normalise to 0–1
        return max(0, min(100, int(raw * 100)))

    except ImportError:
        return None


def score_loneliness(text: str, use_bert: bool = True) -> int:
    """
    Public entry point.
    Returns 0–100 loneliness score.
    Tries BERT first; falls back to rule-based if unavailable.
    """
    if use_bert:
        bert = _bert_score(text)
        if bert is not None:
            # Blend with rule-based for stability
            rule = _rule_based_score(text)
            return int(0.6 * bert + 0.4 * rule)

    return _rule_based_score(text)


def score_to_band(score: int) -> tuple[str, str]:
    """Return (severity_label, human_description) for a given score."""
    from config import SCORE_BANDS
    for (lo, hi), (label, desc) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return label, desc
    return "unknown", "Score out of expected range"
