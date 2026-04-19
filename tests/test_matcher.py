"""
CivicPulse — Dispatch Matcher Unit Tests

Tests volunteer matching algorithm — weights, scoring, and ranking.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "dispatch"))

from matcher import (
    haversine_distance,
    compute_proximity_score,
    compute_skill_alignment,
    compute_match_score,
    rank_volunteers,
)


class TestHaversineDistance:
    def test_same_point(self):
        assert haversine_distance(28.6, 77.2, 28.6, 77.2) == 0.0

    def test_short_distance(self):
        # ~1.1 km in Delhi
        d = haversine_distance(28.6, 77.2, 28.61, 77.2)
        assert 0.5 < d < 2.0

    def test_long_distance(self):
        # Delhi to Mumbai ~1,150 km
        d = haversine_distance(28.6, 77.2, 19.0, 72.8)
        assert 1000 < d < 1300


class TestProximityScore:
    def test_at_location(self):
        score = compute_proximity_score(28.6, 77.2, 28.6, 77.2, 10)
        assert score == 1.0

    def test_out_of_radius(self):
        score = compute_proximity_score(28.6, 77.2, 19.0, 72.8, 10)
        assert score == 0.0

    def test_unknown_location(self):
        score = compute_proximity_score(None, None, 28.6, 77.2, 10)
        assert score == 0.3

    def test_within_radius(self):
        score = compute_proximity_score(28.6, 77.2, 28.605, 77.205, 10)
        assert 0.8 < score <= 1.0


class TestSkillAlignment:
    def test_perfect_match(self):
        assert compute_skill_alignment(["medical", "logistics"], ["medical", "logistics"]) == 1.0

    def test_partial_match(self):
        assert compute_skill_alignment(["medical"], ["medical", "logistics"]) == 0.5

    def test_no_match(self):
        assert compute_skill_alignment(["teaching"], ["medical", "logistics"]) == 0.0

    def test_no_requirements(self):
        assert compute_skill_alignment(["medical"], []) == 1.0


class TestMatchScore:
    def setup_method(self):
        self.volunteer = {
            "id": "vol-1",
            "lat": 28.6,
            "lng": 77.2,
            "skills": ["medical", "logistics"],
            "is_available": True,
            "fatigue_score": 0.2,
            "max_radius_km": 15,
        }
        self.ward = {"lat": 28.605, "lng": 77.205}

    def test_available_volunteer_scores_positive(self):
        scores = compute_match_score(self.volunteer, self.ward, ["medical"])
        assert scores["total"] > 0.5
        assert not scores["excluded"]

    def test_unavailable_volunteer_excluded(self):
        self.volunteer["is_available"] = False
        scores = compute_match_score(self.volunteer, self.ward, [])
        assert scores["total"] == 0.0
        assert scores["excluded"]
        assert scores["reason"] == "unavailable"

    def test_fatigued_volunteer_excluded(self):
        self.volunteer["fatigue_score"] = 0.9
        scores = compute_match_score(self.volunteer, self.ward, [])
        assert scores["total"] == 0.0
        assert scores["excluded"]
        assert scores["reason"] == "fatigue_too_high"

    def test_out_of_radius_excluded(self):
        self.volunteer["lat"] = 19.0  # Mumbai
        self.volunteer["lng"] = 72.8
        scores = compute_match_score(self.volunteer, self.ward, [])
        assert scores["total"] == 0.0
        assert scores["excluded"]
        assert scores["reason"] == "out_of_radius"


class TestRankVolunteers:
    def test_ranking_order(self):
        # Closer volunteer should rank higher
        volunteers = [
            {"id": "far", "lat": 28.7, "lng": 77.3, "skills": ["logistics"],
             "is_available": True, "fatigue_score": 0.3, "max_radius_km": 20},
            {"id": "close", "lat": 28.601, "lng": 77.201, "skills": ["medical", "logistics"],
             "is_available": True, "fatigue_score": 0.1, "max_radius_km": 15},
        ]
        ward = {"lat": 28.6, "lng": 77.2}
        ranked = rank_volunteers(volunteers, ward, ["medical"], top_n=2)

        assert len(ranked) == 2
        assert ranked[0]["volunteer"]["id"] == "close"

    def test_empty_volunteers(self):
        ranked = rank_volunteers([], {"lat": 28.6, "lng": 77.2}, [], top_n=5)
        assert ranked == []
