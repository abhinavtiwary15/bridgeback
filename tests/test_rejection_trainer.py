"""Tests for rejection resilience trainer."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llm.rejection_trainer import generate_resilience_block


def test_rejection_trainer_returns_structured_block():
    block = generate_resilience_block("Priya", "Hey Priya, want to catch up this week?")
    assert "message" in block
    assert "scenarios" in block
    assert len(block["scenarios"]) == 3
    scenario_types = {s["type"] for s in block["scenarios"]}
    assert {"positive", "neutral", "no_response"} <= scenario_types
