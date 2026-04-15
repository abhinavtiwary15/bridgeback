"""Tests for NLP layer (no API keys needed)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nlp.loneliness_scorer import score_loneliness, score_to_band
from nlp.drift_detector import detect_drift_signals, detect_anxiety_markers, classify_connection_need
from nlp.entity_extractor import extract_person_names
from nlp.crisis_detector import detect_crisis, build_crisis_response


def test_loneliness_high():
    text = "I feel so alone. I haven't spoken to anyone in weeks. I miss my old friends."
    score = score_loneliness(text, use_bert=False)
    assert score > 50, f"Expected >50, got {score}"


def test_loneliness_low():
    text = "I have close friends and a great social life. Hung out with my best friend yesterday."
    score = score_loneliness(text, use_bert=False)
    assert score < 50, f"Expected <50, got {score}"


def test_score_bands():
    label, desc = score_to_band(10)
    assert label == "minimal"
    label, desc = score_to_band(75)
    assert label == "severe"


def test_drift_signals():
    text = "We used to hang out all the time. Haven't spoken to her in months."
    signals = detect_drift_signals(text)
    assert len(signals) > 0


def test_anxiety_markers():
    text = "I'm too anxious to reach out. I don't know what to say."
    markers = detect_anxiety_markers(text)
    assert len(markers) > 0


def test_entity_extraction_regex():
    text = "I miss my friend Priya. I used to hang out with Rahul every weekend."
    names = extract_person_names(text)
    assert "Priya" in names or "Rahul" in names


def test_crisis_detection_positive():
    text = "I want to kill myself. Nobody would care."
    detected, signals = detect_crisis(text)
    assert detected is True
    assert len(signals) > 0


def test_crisis_detection_negative():
    text = "I feel a bit lonely today, wish I had more friends."
    detected, signals = detect_crisis(text)
    assert detected is False


def test_crisis_resources():
    response = build_crisis_response("IN")
    assert "iCall" in response or "Vandrevala" in response


def test_connection_need_family():
    text = "I really miss my mom and my sister. Haven't called them in so long."
    need = classify_connection_need(text)
    assert need == "family_reconnection"
