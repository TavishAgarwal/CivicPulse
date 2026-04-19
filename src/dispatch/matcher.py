"""
CivicPulse — Volunteer Dispatch Matcher

Constraint-satisfaction matching algorithm.
All weights loaded from environment — never hardcoded.
"""

import logging
import math
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Weights from environment
WEIGHT_PROXIMITY = float(os.environ.get("DISPATCH_WEIGHT_PROXIMITY", "0.35"))
WEIGHT_SKILL = float(os.environ.get("DISPATCH_WEIGHT_SKILL", "0.30"))
WEIGHT_AVAILABILITY = float(os.environ.get("DISPATCH_WEIGHT_AVAILABILITY", "0.20"))
WEIGHT_FATIGUE = float(os.environ.get("DISPATCH_WEIGHT_FATIGUE", "0.15"))
FATIGUE_EXCLUSION_THRESHOLD = float(os.environ.get("FATIGUE_EXCLUSION_THRESHOLD", "0.85"))
MATCH_COUNT = int(os.environ.get("DISPATCH_MATCH_COUNT", "5"))


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate great-circle distance in km between two points."""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def compute_proximity_score(
    vol_lat: Optional[float],
    vol_lng: Optional[float],
    ward_lat: Optional[float],
    ward_lng: Optional[float],
    max_radius_km: int,
) -> float:
    """
    Compute proximity score (0-1).
    1.0 = at the ward location, 0.0 = at or beyond max_radius.
    """
    if any(v is None for v in [vol_lat, vol_lng, ward_lat, ward_lng]):
        return 0.3  # Unknown location — moderate default

    distance = haversine_distance(
        float(vol_lat), float(vol_lng),
        float(ward_lat), float(ward_lng),
    )

    if distance > max_radius_km:
        return 0.0

    return max(0.0, 1.0 - (distance / max_radius_km))


def compute_skill_alignment(
    volunteer_skills: list[str],
    required_skills: list[str],
) -> float:
    """
    Compute skill alignment score (0-1).
    1.0 = all required skills matched, 0.0 = no overlap.
    """
    if not required_skills:
        return 1.0 if volunteer_skills else 0.5

    vol_set = set(volunteer_skills or [])
    req_set = set(required_skills)

    if not req_set:
        return 1.0

    overlap = len(vol_set & req_set)
    return overlap / len(req_set)


def compute_match_score(
    volunteer: dict,
    ward: dict,
    required_skills: list[str],
) -> dict:
    """
    Compute overall match score with breakdown.
    All weights from environment variables.

    Args:
        volunteer: Dict with lat, lng, skills, is_available, fatigue_score, max_radius_km
        ward: Dict with lat, lng
        required_skills: List of required skill tags

    Returns:
        Dict with total score and component breakdown
    """
    # Hard constraints — exclude immediately
    if not volunteer.get("is_available", False):
        return {"total": 0.0, "excluded": True, "reason": "unavailable"}

    fatigue = float(volunteer.get("fatigue_score", 0))
    if fatigue >= FATIGUE_EXCLUSION_THRESHOLD:
        return {"total": 0.0, "excluded": True, "reason": "fatigue_too_high"}

    max_radius = int(volunteer.get("max_radius_km", 10))

    # Check if within radius
    distance = 999.0
    if all(volunteer.get(k) is not None for k in ["lat", "lng"]) and all(ward.get(k) is not None for k in ["lat", "lng"]):
        distance = haversine_distance(
            float(volunteer["lat"]), float(volunteer["lng"]),
            float(ward["lat"]), float(ward["lng"]),
        )
        if distance > max_radius:
            return {"total": 0.0, "excluded": True, "reason": "out_of_radius", "distance_km": round(distance, 2)}

    # Soft scores
    proximity = compute_proximity_score(
        volunteer.get("lat"), volunteer.get("lng"),
        ward.get("lat"), ward.get("lng"),
        max_radius,
    )

    skill = compute_skill_alignment(
        volunteer.get("skills", []),
        required_skills,
    )

    availability = 1.0 if volunteer.get("is_available") else 0.0
    fatigue_inv = 1.0 - fatigue

    total = (
        WEIGHT_PROXIMITY * proximity
        + WEIGHT_SKILL * skill
        + WEIGHT_AVAILABILITY * availability
        + WEIGHT_FATIGUE * fatigue_inv
    )

    return {
        "total": round(total, 4),
        "proximity": round(proximity, 4),
        "skill": round(skill, 4),
        "availability": round(availability, 4),
        "fatigue": round(fatigue_inv, 4),
        "distance_km": round(distance, 2),
        "excluded": False,
    }


def rank_volunteers(
    volunteers: list[dict],
    ward: dict,
    required_skills: list[str],
    top_n: Optional[int] = None,
) -> list[dict]:
    """
    Rank volunteers by match score for a given ward.

    Returns:
        Sorted list of {volunteer, score_breakdown} dicts, best first.
    """
    if top_n is None:
        top_n = MATCH_COUNT

    results = []
    for vol in volunteers:
        scores = compute_match_score(vol, ward, required_skills)
        if not scores.get("excluded", False) and scores["total"] > 0.1:
            results.append({
                "volunteer": vol,
                "scores": scores,
            })

    results.sort(key=lambda r: r["scores"]["total"], reverse=True)
    return results[:top_n]
