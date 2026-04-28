#!/usr/bin/env python3
"""
CivicPulse — Firestore Seed Script (Spark Plan Compatible)
Seeds Firestore with realistic Delhi ward data, volunteers, and sample dispatches.
Uses firebase-admin SDK with service account credentials.

Usage:
  pip install firebase-admin
  python seed_firestore.py --project civicpulse18

Note: On Spark plan, you need to generate a service account key from:
  Firebase Console → Project Settings → Service Accounts → Generate New Private Key
  Save it as service_account.json in this directory.
"""

import argparse
import json
import random
import math
from datetime import datetime, timedelta
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore


# ── Delhi Ward Data ─────────────────────────────────────────
# 30 realistic ward clusters across Delhi NCR
DELHI_WARDS = [
    # Central Delhi — high density
    {"name": "Chandni Chowk", "code": "WARD-DEL-001", "lat": 28.6506, "lng": 77.2334, "base_css": 62},
    {"name": "Karol Bagh", "code": "WARD-DEL-002", "lat": 28.6519, "lng": 77.1907, "base_css": 48},
    {"name": "Connaught Place", "code": "WARD-DEL-003", "lat": 28.6315, "lng": 77.2167, "base_css": 22},
    {"name": "Paharganj", "code": "WARD-DEL-004", "lat": 28.6423, "lng": 77.2132, "base_css": 55},
    {"name": "Daryaganj", "code": "WARD-DEL-005", "lat": 28.6386, "lng": 77.2427, "base_css": 41},

    # East Delhi
    {"name": "Laxmi Nagar", "code": "WARD-DEL-006", "lat": 28.6304, "lng": 77.2773, "base_css": 58},
    {"name": "Preet Vihar", "code": "WARD-DEL-007", "lat": 28.6378, "lng": 77.2955, "base_css": 35},
    {"name": "Mayur Vihar", "code": "WARD-DEL-008", "lat": 28.6093, "lng": 77.2987, "base_css": 29},
    {"name": "Patparganj", "code": "WARD-DEL-009", "lat": 28.6236, "lng": 77.2899, "base_css": 44},
    {"name": "Shakarpur", "code": "WARD-DEL-010", "lat": 28.6362, "lng": 77.2636, "base_css": 67},

    # South Delhi
    {"name": "Saket", "code": "WARD-DEL-011", "lat": 28.5244, "lng": 77.2067, "base_css": 18},
    {"name": "Hauz Khas", "code": "WARD-DEL-012", "lat": 28.5495, "lng": 77.2050, "base_css": 24},
    {"name": "Malviya Nagar", "code": "WARD-DEL-013", "lat": 28.5319, "lng": 77.2108, "base_css": 32},
    {"name": "Sangam Vihar", "code": "WARD-DEL-014", "lat": 28.4941, "lng": 77.2464, "base_css": 78},
    {"name": "Tughlaqabad", "code": "WARD-DEL-015", "lat": 28.5134, "lng": 77.2572, "base_css": 71},

    # North Delhi
    {"name": "Model Town", "code": "WARD-DEL-016", "lat": 28.7170, "lng": 77.1909, "base_css": 26},
    {"name": "Burari", "code": "WARD-DEL-017", "lat": 28.7570, "lng": 77.2012, "base_css": 63},
    {"name": "Civil Lines", "code": "WARD-DEL-018", "lat": 28.6810, "lng": 77.2263, "base_css": 19},
    {"name": "Sadar Bazaar", "code": "WARD-DEL-019", "lat": 28.6592, "lng": 77.2066, "base_css": 52},
    {"name": "Timarpur", "code": "WARD-DEL-020", "lat": 28.6925, "lng": 77.2183, "base_css": 37},

    # West Delhi
    {"name": "Rajouri Garden", "code": "WARD-DEL-021", "lat": 28.6485, "lng": 77.1245, "base_css": 42},
    {"name": "Dwarka", "code": "WARD-DEL-022", "lat": 28.5921, "lng": 77.0413, "base_css": 28},
    {"name": "Janakpuri", "code": "WARD-DEL-023", "lat": 28.6213, "lng": 77.0833, "base_css": 33},
    {"name": "Uttam Nagar", "code": "WARD-DEL-024", "lat": 28.6195, "lng": 77.0526, "base_css": 72},
    {"name": "Najafgarh", "code": "WARD-DEL-025", "lat": 28.5721, "lng": 76.9879, "base_css": 59},

    # Northeast Delhi — higher stress
    {"name": "Seelampur", "code": "WARD-DEL-026", "lat": 28.6757, "lng": 77.2662, "base_css": 81},
    {"name": "Jafrabad", "code": "WARD-DEL-027", "lat": 28.6726, "lng": 77.2587, "base_css": 76},
    {"name": "Mustafabad", "code": "WARD-DEL-028", "lat": 28.6943, "lng": 77.2585, "base_css": 84},
    {"name": "Bhajanpura", "code": "WARD-DEL-029", "lat": 28.6881, "lng": 77.2637, "base_css": 69},
    {"name": "Gokulpuri", "code": "WARD-DEL-030", "lat": 28.6977, "lng": 77.2706, "base_css": 73},
]

# ── Volunteer Data ──────────────────────────────────────────
FIRST_NAMES = [
    "Aarav", "Priya", "Rohan", "Meera", "Vikram", "Ananya", "Arjun", "Diya",
    "Karan", "Neha", "Siddharth", "Kavya", "Ravi", "Ishita", "Amit",
    "Pooja", "Nikhil", "Shreya", "Rahul", "Divya", "Aditya", "Sneha",
    "Varun", "Ritika", "Harsh", "Swati", "Gaurav", "Kriti", "Manish", "Anjali",
]
LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Singh", "Reddy", "Gupta", "Kumar", "Iyer",
    "Das", "Joshi", "Chauhan", "Nair", "Bhatt", "Kapoor", "Mishra",
]
SKILLS = ["medical", "logistics", "counseling", "teaching", "language"]
SIGNAL_TYPES = ["pharmacy", "school", "utility", "social", "foodbank", "health"]


def css_status(score):
    if score >= 76:
        return "critical"
    if score >= 56:
        return "high"
    if score >= 31:
        return "elevated"
    return "stable"


def generate_signal_breakdown(base_css):
    """Generate signal contributions that roughly sum to the CSS score."""
    breakdown = {}
    remaining = base_css / 100.0
    for i, sig in enumerate(SIGNAL_TYPES):
        if i == len(SIGNAL_TYPES) - 1:
            breakdown[sig] = round(max(0, remaining), 3)
        else:
            portion = remaining * random.uniform(0.1, 0.4)
            breakdown[sig] = round(portion, 3)
            remaining -= portion
    return breakdown


def generate_css_history(base_css, days=14):
    """Generate CSS history for the past N days."""
    history = []
    now = datetime.utcnow()
    for i in range(days):
        date = now - timedelta(days=days - 1 - i)
        # Add daily variation
        variation = random.gauss(0, 5)
        daily_css = max(0, min(100, base_css + variation))
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "computedAt": date.isoformat() + "Z",
            "cssScore": round(daily_css, 1),
            "signalBreakdown": generate_signal_breakdown(daily_css),
        })
    return history


def seed_wards(db_client):
    """Seed city and ward data into Firestore."""
    print("\n🏙️  Seeding city: Delhi...")

    # Create city document
    city_ref = db_client.collection("cities").document("delhi")
    city_ref.set({
        "name": "Delhi",
        "state": "Delhi NCR",
        "country": "India",
        "totalWards": len(DELHI_WARDS),
        "lastUpdated": firestore.SERVER_TIMESTAMP,
    })

    for ward in DELHI_WARDS:
        css = ward["base_css"] + random.uniform(-3, 3)
        css = round(max(0, min(100, css)), 1)

        ward_ref = city_ref.collection("wards").document(ward["code"].lower().replace("-", "_"))
        ward_data = {
            "name": ward["name"],
            "code": ward["code"],
            "lat": ward["lat"],
            "lng": ward["lng"],
            "currentCSS": css,
            "cssStatus": css_status(css),
            "population": random.randint(15000, 85000),
            "signalBreakdown": generate_signal_breakdown(css),
            "lastSignalAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        ward_ref.set(ward_data)

        # Add CSS history subcollection
        history = generate_css_history(ward["base_css"])
        for entry in history:
            ward_ref.collection("cssHistory").document(entry["date"]).set(entry)

        status_icon = "🔴" if css >= 76 else "🟠" if css >= 56 else "🟡" if css >= 31 else "🟢"
        print(f"  {status_icon} {ward['code']} — {ward['name']:20s} CSS: {css:5.1f} ({css_status(css)})")

    print(f"\n  ✅ {len(DELHI_WARDS)} wards seeded with 14-day CSS history each.")


def seed_volunteers(db_client, count=30):
    """Seed volunteer profiles into Firestore."""
    print(f"\n👥 Seeding {count} volunteers...")

    for i in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        handle = f"{first}_{last}"
        vol_id = f"vol_{i:03d}"

        num_skills = random.randint(1, 3)
        vol_skills = random.sample(SKILLS, num_skills)

        vol_ref = db_client.collection("volunteers").document(vol_id)
        vol_ref.set({
            "displayHandle": handle,
            "email": f"{first.lower()}.{last.lower()}@volunteer.civicpulse.org",
            "skills": vol_skills,
            "maxRadiusKm": random.choice([5, 10, 15, 20, 25]),
            "fatigueScore": round(random.uniform(0, 0.6), 2),
            "performanceRating": round(random.uniform(3.0, 5.0), 1),
            "isAvailable": random.random() > 0.2,  # 80% available
            "cityId": "delhi",
            "totalDispatches": random.randint(0, 25),
            "joinedAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        })
        print(f"  ✅ {vol_id} — {handle} [{', '.join(vol_skills)}]")

    print(f"\n  ✅ {count} volunteers seeded.")


def seed_dispatches(db_client, count=8):
    """Seed sample dispatch records."""
    print(f"\n📋 Seeding {count} sample dispatches...")

    statuses = ["pending", "confirmed", "active", "completed"]
    now = datetime.utcnow()

    for i in range(count):
        ward = random.choice(DELHI_WARDS)
        vol_idx = random.randint(0, 29)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)

        created = now - timedelta(hours=random.randint(1, 72))

        dispatch_ref = db_client.collection("dispatches").document()
        dispatch_ref.set({
            "wardId": ward["code"].lower().replace("-", "_"),
            "wardName": ward["code"],
            "volunteerId": f"vol_{vol_idx:03d}",
            "volunteerName": f"{first}_{last}",
            "cssAtDispatch": round(ward["base_css"] + random.uniform(-5, 5), 1),
            "matchScore": round(random.uniform(0.6, 0.95), 2),
            "status": random.choice(statuses),
            "createdBy": "seed-script",
            "dispatchedAt": created,
            "auditLog": [
                {
                    "action": "created",
                    "timestamp": created.isoformat() + "Z",
                    "by": "seed-script",
                }
            ],
        })
        print(f"  📌 Dispatch → {ward['code']} ({ward['name']})")

    print(f"\n  ✅ {count} dispatches seeded.")


def seed_config(db_client):
    """Seed application config/thresholds."""
    print("\n⚙️  Seeding config/thresholds...")
    db_client.collection("config").document("thresholds").set({
        "cssStableMax": 30,
        "cssElevatedMax": 55,
        "cssHighThreshold": 56,
        "cssCriticalThreshold": 76,
        "autoDispatchMinCSS": 76,
        "humanApprovalRequired": True,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })
    print("  ✅ Config seeded.")


def main():
    parser = argparse.ArgumentParser(description="Seed CivicPulse Firestore")
    parser.add_argument("--project", default="civicpulse18", help="Firebase project ID")
    parser.add_argument("--cred", default=None,
                        help="Path to service account JSON. If not provided, uses GOOGLE_APPLICATION_CREDENTIALS env var.")
    args = parser.parse_args()

    print("=" * 60)
    print("  CivicPulse — Firestore Seed Script")
    print(f"  Project: {args.project}")
    print("=" * 60)

    # Initialize Firebase Admin
    if args.cred:
        cred = credentials.Certificate(args.cred)
    else:
        # Try to find service_account.json in script directory
        script_dir = Path(__file__).parent
        sa_path = script_dir / "service_account.json"
        if sa_path.exists():
            cred = credentials.Certificate(str(sa_path))
            print(f"  Using credentials: {sa_path}")
        else:
            print("\n⚠️  No service account found!")
            print("  Please do ONE of the following:")
            print(f"  1. Place service_account.json in {script_dir}/")
            print("  2. Run with --cred /path/to/service_account.json")
            print("  3. Set GOOGLE_APPLICATION_CREDENTIALS env var")
            print("\n  To get a service account key:")
            print("  → Firebase Console → Project Settings → Service Accounts")
            print("  → Generate New Private Key")
            return

    firebase_admin.initialize_app(cred, {"projectId": args.project})
    db_client = firestore.client()

    # Seed all collections
    seed_wards(db_client)
    seed_volunteers(db_client)
    seed_dispatches(db_client)
    seed_config(db_client)

    print("\n" + "=" * 60)
    print("  ✅ ALL SEED DATA WRITTEN SUCCESSFULLY!")
    print("  → 30 wards with 14-day CSS history")
    print("  → 30 volunteers with skills & availability")
    print("  → 8 sample dispatches with audit logs")
    print("  → Config thresholds document")
    print("=" * 60)
    print("\n  Next steps:")
    print("  1. Run the dashboard:  cd src/dashboard && npm run dev")
    print("  2. Login with demo mode or create a Firebase Auth user")
    print("  3. View the heatmap at /dashboard")
    print()


if __name__ == "__main__":
    main()
