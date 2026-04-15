"""
BridgeBack — Layer 1: Entity Extractor
Extracts person names and places from raw user text using spaCy NER.
Falls back to regex heuristics if spaCy model isn't available.
"""

from __future__ import annotations
import re
from typing import List, Tuple
from functools import lru_cache


# ── Regex fallback ────────────────────────────────────────────────────────────
# Catches "my friend Priya", "my brother Rahul", "I was with Deepa" etc.

_RELATIONSHIP_TRIGGERS = [
    r"my (?:friend|best friend|girlfriend|boyfriend|partner|husband|wife|"
    r"brother|sister|mom|mum|dad|father|mother|colleague|coworker|roommate|flatmate|"
    r"ex|ex-friend|childhood friend|school friend|cousin|uncle|aunt|neighbour|neighbor)\s+([A-Z][a-z]+)",
    r"(?:I was|I went|I spoke|I talked|I called|I texted|I messaged|I met|I saw)\s+(?:with\s+)?([A-Z][a-z]+)",
    r"([A-Z][a-z]+)\s+(?:and I|told me|called me|texted me|messaged me)",
    r"(?:miss|missing|thinking about|thought about)\s+([A-Z][a-z]+)",
    r"(?:haven'?t (?:spoken|talked|seen|heard from|met))\s+(?:with\s+)?([A-Z][a-z]+)",
]

_REGEX_PERSON = re.compile(
    "|".join(_RELATIONSHIP_TRIGGERS)
)

# Common first-name stopwords to filter out false positives
_STOPWORDS = {
    "I", "The", "A", "An", "It", "He", "She", "They", "We",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Google", "Facebook", "Instagram", "Twitter", "WhatsApp",
}


@lru_cache(maxsize=1)
def _get_spacy_model():
    import spacy
    return spacy.load("en_core_web_sm")


def _extract_spacy(text: str) -> List[Tuple[str, str]]:
    """Returns list of (name, label) using spaCy."""
    try:
        nlp = _get_spacy_model()
    except OSError:
        raise ImportError("spaCy model not found")

    doc = nlp(text)
    results = []
    for ent in doc.ents:
        if ent.label_ == "PERSON" and ent.text not in _STOPWORDS:
            results.append((ent.text.strip(), "PERSON"))
        elif ent.label_ in ("GPE", "LOC"):
            results.append((ent.text.strip(), "PLACE"))
    return results


def _extract_regex(text: str) -> List[Tuple[str, str]]:
    """Regex-based fallback name extraction."""
    matches = _REGEX_PERSON.findall(text)
    names = set()
    for match_tuple in matches:
        for name in match_tuple:
            name = name.strip()
            if name and name not in _STOPWORDS and len(name) > 1:
                names.add(name)
    return [(name, "PERSON") for name in names]


def extract_entities(text: str) -> List[Tuple[str, str]]:
    """
    Extract (entity_text, entity_type) pairs from text.
    entity_type is "PERSON" or "PLACE".
    Tries spaCy first; falls back to regex.
    """
    try:
        return _extract_spacy(text)
    except (ImportError, Exception):
        return _extract_regex(text)


def extract_person_names(text: str) -> List[str]:
    """Return just the list of person name strings."""
    return [name for name, label in extract_entities(text) if label == "PERSON"]
