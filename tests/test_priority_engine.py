"""Tests for relationship priority engine."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tracking.priority_engine import rank_relationships


def test_rank_relationships_returns_top_ranked_people():
    profile = {
        "relationship_signals": [
            {
                "name": "Priya",
                "status": "drifted",
                "context": "We used to talk daily.",
                "mention_count": 5,
            },
            {
                "name": "Rahul",
                "status": "active",
                "context": "Spoke last week.",
                "mention_count": 3,
            },
            {
                "name": "Neha",
                "status": "drifted",
                "context": "Haven't spoken in months.",
                "mention_count": 2,
            },
        ]
    }
    ranked = rank_relationships(profile)
    assert len(ranked) >= 1
    assert ranked[0]["name"] == "Priya"
    assert "priority_score" in ranked[0]
    assert "reason" in ranked[0]
