"""
CivicPulse — Synthetic Data Generator

Generates realistic synthetic data for development and testing.
Produces deterministic output when seeded for reproducible tests.

Usage:
    python generate.py --city delhi --wards 50 --days 60 --seed 42
    python generate.py --city mumbai --wards 30 --days 90 --seed 123
"""

import argparse
import json
import math
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

# Ward name fragments for realistic generation
WARD_PREFIXES = [
    "Chandni", "Sadar", "Lajpat", "Karol", "Rajinder", "Patel",
    "Nehru", "Gandhi", "Subhash", "Ambedkar", "Tilak", "Bose",
    "Shastri", "Indira", "Sardar", "Bhagat", "Maulana", "Vivekananda",
    "Tagore", "Ram", "Krishna", "Lakshmi", "Durga", "Sarojini",
    "Ashoka", "Vikram", "Prithvi", "Chandra", "Janaki", "Sita",
]

WARD_SUFFIXES = [
    "Nagar", "Bagh", "Chowk", "Bazaar", "Vihar", "Enclave",
    "Colony", "Park", "Extension", "Block", "Marg", "Lane",
    "Gate", "Ganj", "Pura", "Garh", "Abad", "Wadi",
]

SIGNAL_TYPES = ["pharmacy", "school", "utility", "social", "foodbank", "health"]

SKILLS = ["medical", "logistics", "counseling", "teaching", "language"]

VOLUNTEER_HANDLES = [
    "swift", "brave", "calm", "keen", "bold", "wise", "kind",
    "warm", "cool", "fair", "true", "pure", "deep", "wide",
    "free", "glad", "sure", "safe", "fast", "firm",
]

# City coordinate centers
CITY_COORDS = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
}


def generate_wards(city: str, num_wards: int, rng: random.Random) -> list[dict]:
    """Generate ward records for a city."""
    center_lat, center_lng = CITY_COORDS.get(city, (28.6139, 77.2090))
    wards = []

    for i in range(num_wards):
        prefix = rng.choice(WARD_PREFIXES)
        suffix = rng.choice(WARD_SUFFIXES)
        name = f"{prefix} {suffix}"

        # Spread wards around city center (within ~15km)
        lat_offset = rng.uniform(-0.15, 0.15)
        lng_offset = rng.uniform(-0.15, 0.15)

        ward = {
            "id": str(uuid.UUID(int=rng.getrandbits(128))),
            "city_id": city,
            "ward_code": f"WARD-{city.upper()[:3]}-{i + 1:03d}",
            "name": f"Ward {i + 1} - {name}",
            "lat": round(center_lat + lat_offset, 3),
            "lng": round(center_lng + lng_offset, 3),
            "population_tier": rng.choice([1, 2, 2, 3, 3, 3]),  # Skew toward larger
        }
        wards.append(ward)

    return wards


def generate_signals(
    wards: list[dict], num_days: int, rng: random.Random
) -> list[dict]:
    """
    Generate signal history with plausible patterns.
    Includes weekday spikes, seasonal trends, and ward-specific baselines.
    """
    signals = []
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=num_days)

    for ward in wards:
        # Each ward has a baseline distress level
        ward_baseline = rng.uniform(0.15, 0.55)

        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()

            # Weekday spike factor (higher on weekdays)
            weekday_factor = 1.1 if day_of_week < 5 else 0.85

            # Seasonal trend (gradual increase then decrease)
            season_phase = (day_offset / num_days) * 2 * math.pi
            seasonal_factor = 1.0 + 0.15 * math.sin(season_phase)

            # Generate 2-4 signals per ward per day
            num_signals_today = rng.randint(2, 4)
            selected_types = rng.sample(SIGNAL_TYPES, min(num_signals_today, len(SIGNAL_TYPES)))

            for signal_type in selected_types:
                # Type-specific baseline variance
                type_offset = {
                    "pharmacy": rng.uniform(-0.05, 0.1),
                    "school": rng.uniform(-0.1, 0.05),
                    "utility": rng.uniform(-0.05, 0.08),
                    "social": rng.uniform(-0.1, 0.15),
                    "foodbank": rng.uniform(-0.05, 0.12),
                    "health": rng.uniform(-0.08, 0.05),
                }.get(signal_type, 0)

                # Compute intensity
                intensity = (
                    ward_baseline
                    * weekday_factor
                    * seasonal_factor
                    + type_offset
                    + rng.gauss(0, 0.08)  # Random noise
                )
                intensity = max(0.0, min(1.0, intensity))

                # Random hour of day
                hour = rng.randint(6, 22)
                minute = rng.randint(0, 59)
                timestamp = current_date.replace(hour=hour, minute=minute, second=0)

                signal = {
                    "source": f"{signal_type}_synthetic",
                    "location_pin": ward["ward_code"],
                    "signal_type": signal_type,
                    "intensity_score": round(intensity, 3),
                    "timestamp": timestamp.isoformat(),
                    "confidence": round(rng.uniform(0.55, 0.95), 3),
                }
                signals.append(signal)

    return signals


def generate_volunteers(
    wards: list[dict], num_volunteers: int, rng: random.Random
) -> list[dict]:
    """Generate volunteer profiles with varied skills and locations."""
    volunteers = []

    for i in range(num_volunteers):
        # Pick a random ward as base location
        base_ward = rng.choice(wards)

        # Generate display handle (no real names)
        adj = rng.choice(VOLUNTEER_HANDLES)
        num = rng.randint(100, 999)
        handle = f"{adj}_{num}"

        # Random skill set (1-3 skills)
        num_skills = rng.randint(1, 3)
        skills = rng.sample(SKILLS, num_skills)

        volunteer = {
            "id": str(uuid.UUID(int=rng.getrandbits(128))),
            "display_handle": handle,
            "skills": skills,
            "max_radius_km": rng.choice([5, 10, 10, 15, 20, 25]),
            "lat": base_ward["lat"] + rng.uniform(-0.02, 0.02),
            "lng": base_ward["lng"] + rng.uniform(-0.02, 0.02),
            "city_id": base_ward["city_id"],
            "fatigue_score": round(rng.uniform(0.0, 0.4), 2),
            "performance_rating": round(rng.uniform(3.0, 5.0), 1) if rng.random() > 0.3 else None,
            "is_available": rng.random() > 0.2,  # 80% available
        }
        volunteers.append(volunteer)

    return volunteers


def generate_sql_inserts(wards: list[dict], volunteers: list[dict]) -> str:
    """Generate SQL INSERT statements for seeding the database."""
    lines = ["-- Auto-generated seed data\n"]

    # Wards
    lines.append("-- Wards")
    for w in wards:
        lines.append(
            f"INSERT INTO wards (id, city_id, ward_code, name, lat, lng, population_tier) "
            f"VALUES ('{w['id']}', '{w['city_id']}', '{w['ward_code']}', "
            f"'{w['name'].replace(chr(39), chr(39)+chr(39))}', {w['lat']}, {w['lng']}, {w['population_tier']}) "
            f"ON CONFLICT (ward_code) DO NOTHING;"
        )

    lines.append("\n-- Volunteers")
    for v in volunteers:
        skills_arr = "'{" + ",".join(v["skills"]) + "}'"
        perf = f"{v['performance_rating']}" if v["performance_rating"] is not None else "NULL"
        lines.append(
            f"INSERT INTO volunteers (id, display_handle, skills, max_radius_km, lat, lng, city_id, "
            f"fatigue_score, performance_rating, is_available) "
            f"VALUES ('{v['id']}', '{v['display_handle']}', {skills_arr}, {v['max_radius_km']}, "
            f"{v['lat']:.3f}, {v['lng']:.3f}, '{v['city_id']}', {v['fatigue_score']}, {perf}, "
            f"{v['is_available']}) ON CONFLICT DO NOTHING;"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="CivicPulse Synthetic Data Generator")
    parser.add_argument("--city", type=str, default="delhi", help="City name")
    parser.add_argument("--wards", type=int, default=50, help="Number of wards")
    parser.add_argument("--days", type=int, default=60, help="Days of history")
    parser.add_argument("--volunteers", type=int, default=200, help="Number of volunteers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    output_dir = args.output_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)

    print(f"🏙️  Generating data for {args.city} (seed={args.seed})...")

    # Generate wards
    print(f"📍 Generating {args.wards} wards...")
    wards = generate_wards(args.city, args.wards, rng)

    # Generate signals
    print(f"📡 Generating {args.days} days of signal history...")
    signals = generate_signals(wards, args.days, rng)
    print(f"   → {len(signals)} total signals generated")

    # Generate volunteers
    print(f"👥 Generating {args.volunteers} volunteer profiles...")
    volunteers = generate_volunteers(wards, args.volunteers, rng)

    # Write outputs
    signals_path = os.path.join(output_dir, "signals_sample.json")
    with open(signals_path, "w") as f:
        json.dump(signals, f, indent=2, default=str)
    print(f"✅ Signals → {signals_path}")

    volunteers_path = os.path.join(output_dir, "volunteers_sample.json")
    with open(volunteers_path, "w") as f:
        json.dump(volunteers, f, indent=2, default=str)
    print(f"✅ Volunteers → {volunteers_path}")

    # Generate SQL seed file
    sql_path = os.path.join(output_dir, "seed.sql")
    sql = generate_sql_inserts(wards, volunteers)
    with open(sql_path, "w") as f:
        f.write(sql)
    print(f"✅ SQL seed → {sql_path}")

    # Summary
    print(f"\n📊 Summary:")
    print(f"   City: {args.city}")
    print(f"   Wards: {len(wards)}")
    print(f"   Signals: {len(signals)} ({args.days} days)")
    print(f"   Volunteers: {len(volunteers)}")
    print(f"   Seed: {args.seed}")


if __name__ == "__main__":
    main()
