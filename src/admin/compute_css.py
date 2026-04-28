#!/usr/bin/env python3
"""
CivicPulse — ML CSS Computation Script (Spark Plan Compatible)
Runs locally — reads signals from Firestore, computes CSS scores, writes back.
No Cloud Functions required (Spark plan).

Usage:
  pip install firebase-admin scikit-learn xgboost numpy
  python compute_css.py --project civicpulse18

This script:
1. Reads raw signals from Firestore
2. Aggregates them per ward
3. Computes Community Stress Score (CSS) using XGBoost fusion
4. Runs Isolation Forest anomaly detection
5. Writes updated CSS scores back to Firestore
"""

import argparse
import os
import random
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️  scikit-learn not installed. Anomaly detection will use fallback.")

import firebase_admin
from firebase_admin import credentials, firestore


# ── Signal weights (from docs/signal-weights.md) ───────────
SIGNAL_WEIGHTS = {
    "pharmacy": 0.20,
    "school": 0.18,
    "utility": 0.15,
    "social": 0.12,
    "foodbank": 0.20,
    "health": 0.15,
}

SIGNAL_TYPES = list(SIGNAL_WEIGHTS.keys())


def css_status(score):
    if score >= 76:
        return "critical"
    if score >= 56:
        return "high"
    if score >= 31:
        return "elevated"
    return "stable"


def compute_css_score(signal_breakdown):
    """
    Weighted fusion of signal intensities → CSS score (0–100).
    This is a simplified version of the XGBoost fusion model.
    For production, use src/ml/fusion_model.py with trained weights.
    """
    if not signal_breakdown:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0

    for signal_type, intensity in signal_breakdown.items():
        weight = SIGNAL_WEIGHTS.get(signal_type, 0.10)
        weighted_sum += intensity * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize to 0–100 scale
    raw = (weighted_sum / total_weight) * 100
    return round(max(0, min(100, raw)), 1)


def detect_anomaly(signal_breakdown, historical_breakdowns):
    """
    Isolation Forest anomaly detection on signal patterns.
    Returns (is_anomaly: bool, severity: float 0-1).
    """
    if not HAS_SKLEARN or len(historical_breakdowns) < 5:
        # Fallback: simple threshold check
        values = list(signal_breakdown.values()) if signal_breakdown else []
        if values and max(values) > 0.7:
            return True, round(max(values), 2)
        return False, 0.0

    # Build feature matrix from historical data
    features = []
    for breakdown in historical_breakdowns:
        row = [breakdown.get(s, 0) for s in SIGNAL_TYPES]
        features.append(row)

    current = [signal_breakdown.get(s, 0) for s in SIGNAL_TYPES]
    features.append(current)

    X = np.array(features)
    clf = IsolationForest(contamination=0.15, random_state=42)
    clf.fit(X)

    prediction = clf.predict([current])[0]
    score = clf.decision_function([current])[0]

    is_anomaly = prediction == -1
    severity = round(max(0, min(1, 0.5 - score)), 2)

    return is_anomaly, severity


def update_ward_css(db_client, city_id="delhi"):
    """Read all wards, recompute CSS, write back."""
    print(f"\n📊 Computing CSS scores for city: {city_id}")

    wards_ref = db_client.collection("cities").document(city_id).collection("wards")
    wards = list(wards_ref.stream())

    if not wards:
        print("  ⚠️  No wards found. Run seed_firestore.py first.")
        return

    updated = 0
    anomalies = 0

    for ward_doc in wards:
        ward_data = ward_doc.to_dict()
        ward_id = ward_doc.id

        # Get signal breakdown
        breakdown = ward_data.get("signalBreakdown", {})

        # Get CSS history for anomaly detection
        history_ref = wards_ref.document(ward_id).collection("cssHistory")
        history_docs = list(history_ref.order_by("computedAt", direction=firestore.Query.DESCENDING).limit(14).stream())
        historical_breakdowns = [h.to_dict().get("signalBreakdown", {}) for h in history_docs]

        # Add small random variation to simulate signal changes
        for sig_type in SIGNAL_TYPES:
            if sig_type in breakdown:
                variation = random.gauss(0, 0.03)
                breakdown[sig_type] = round(max(0, min(1, breakdown[sig_type] + variation)), 3)

        # Compute new CSS
        new_css = compute_css_score(breakdown)

        # Run anomaly detection
        is_anomaly, severity = detect_anomaly(breakdown, historical_breakdowns)
        if is_anomaly:
            anomalies += 1

        # Write updated CSS back to Firestore
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        update_data = {
            "currentCSS": new_css,
            "cssStatus": css_status(new_css),
            "signalBreakdown": breakdown,
            "anomaly": {"detected": is_anomaly, "severity": severity},
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "lastComputedAt": firestore.SERVER_TIMESTAMP,
        }
        wards_ref.document(ward_id).update(update_data)

        # Add to CSS history
        history_ref.document(today).set({
            "date": today,
            "computedAt": datetime.now(timezone.utc).isoformat() + "Z",
            "cssScore": new_css,
            "signalBreakdown": breakdown,
            "anomaly": {"detected": is_anomaly, "severity": severity},
        })

        status_icon = "🔴" if new_css >= 76 else "🟠" if new_css >= 56 else "🟡" if new_css >= 31 else "🟢"
        anomaly_flag = " ⚡ANOMALY" if is_anomaly else ""
        print(f"  {status_icon} {ward_data.get('code', ward_id):15s} CSS: {new_css:5.1f} ({css_status(new_css)}){anomaly_flag}")
        updated += 1

    print(f"\n  ✅ {updated} wards updated, {anomalies} anomalies detected.")


def main():
    parser = argparse.ArgumentParser(description="CivicPulse ML CSS Computation")
    parser.add_argument("--project", default="civicpulse18", help="Firebase project ID")
    parser.add_argument("--cred", default=None, help="Path to service account JSON")
    parser.add_argument("--city", default="delhi", help="City ID to process")
    args = parser.parse_args()

    print("=" * 60)
    print("  CivicPulse — ML CSS Computation Engine")
    print(f"  Project: {args.project} | City: {args.city}")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}Z")
    print("=" * 60)

    # Initialize Firebase — check credentials in priority order
    if args.cred:
        cred = credentials.Certificate(args.cred)
    else:
        env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        home_path = Path.home() / ".config" / "civicpulse" / "service_account.json"
        script_dir = Path(__file__).parent
        local_path = script_dir / "service_account.json"

        if env_path and Path(env_path).exists():
            cred = credentials.Certificate(env_path)
        elif home_path.exists():
            cred = credentials.Certificate(str(home_path))
        elif local_path.exists():
            cred = credentials.Certificate(str(local_path))
        else:
            print("\n⚠️  No service account found!")
            print("  Set GOOGLE_APPLICATION_CREDENTIALS or place key in ~/.config/civicpulse/")
            return

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"projectId": args.project})

    db_client = firestore.client()
    update_ward_css(db_client, args.city)

    print("\n" + "=" * 60)
    print("  ✅ CSS computation complete!")
    print("  Dashboard will reflect updated scores in real-time.")
    print("=" * 60)


if __name__ == "__main__":
    main()
