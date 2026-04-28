#!/usr/bin/env python3
"""
CivicPulse — ML Model Training Script

Trains the CSS fusion model (XGBoost) and anomaly detector (Isolation Forest)
using synthetic data, then saves model artifacts for inference.

Usage:
  pip install xgboost scikit-learn numpy pandas joblib
  python train_models.py

Output:
  models/fusion_model.joblib        — Trained XGBoost CSS fusion model
  models/anomaly_detector.joblib    — Trained Isolation Forest detector
  models/training_report.json       — Training metrics and metadata

This script generates synthetic training data that mimics the statistical
properties of real civic signals. For production training, replace the
synthetic data generator with actual historical signal data from Firestore.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Ensure src modules are importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "ml"))
sys.path.insert(0, str(ROOT / "src" / "ingestion"))

try:
    import joblib
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import xgboost as xgb
    from sklearn.ensemble import IsolationForest
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install xgboost scikit-learn numpy joblib")
    sys.exit(1)


SIGNAL_TYPES = ["pharmacy", "school", "utility", "social", "foodbank", "health"]
SIGNAL_WEIGHTS = {
    "pharmacy": 0.20, "school": 0.18, "utility": 0.15,
    "social": 0.12, "foodbank": 0.20, "health": 0.15,
}


def generate_synthetic_dataset(n_samples=5000, n_days=90):
    """
    Generate synthetic training data mimicking civic signal patterns.
    Each sample represents one ward on one day with 6 signal intensities.
    """
    np.random.seed(42)

    X = np.zeros((n_samples, len(SIGNAL_TYPES) * 3))  # intensity, trend, volatility
    y = np.zeros(n_samples)

    for i in range(n_samples):
        # Base stress level for this sample
        base_stress = np.random.beta(2, 5) * 100  # Skewed toward lower stress

        intensities = []
        for j, sig_type in enumerate(SIGNAL_TYPES):
            weight = SIGNAL_WEIGHTS[sig_type]
            # Signal intensity correlated with stress
            intensity = np.clip(
                base_stress / 100 * weight * np.random.uniform(0.5, 2.0)
                + np.random.normal(0, 0.05),
                0, 1,
            )
            trend = np.random.normal(0, 0.1)  # 7-day trend
            volatility = abs(np.random.normal(0, 0.15))  # Signal stability

            X[i, j * 3] = intensity
            X[i, j * 3 + 1] = trend
            X[i, j * 3 + 2] = volatility
            intensities.append(intensity)

        # CSS is a noisy function of weighted signals
        weighted_sum = sum(
            intensities[j] * list(SIGNAL_WEIGHTS.values())[j]
            for j in range(len(SIGNAL_TYPES))
        )
        noise = np.random.normal(0, 3)
        y[i] = np.clip(weighted_sum / sum(SIGNAL_WEIGHTS.values()) * 100 + noise, 0, 100)

    feature_names = []
    for sig in SIGNAL_TYPES:
        feature_names.extend([f"{sig}_intensity", f"{sig}_trend", f"{sig}_volatility"])

    return X, y, feature_names


def train_fusion_model(X_train, y_train, X_val, y_val):
    """Train XGBoost CSS fusion model."""
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="reg:squarederror",
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # Evaluate
    y_pred = np.clip(model.predict(X_val), 0, 100)
    metrics = {
        "mae": round(float(mean_absolute_error(y_val, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_val, y_pred))), 4),
        "r2": round(float(r2_score(y_val, y_pred)), 4),
    }
    return model, metrics


def train_anomaly_detector(X_train):
    """Train Isolation Forest anomaly detector."""
    detector = IsolationForest(
        contamination=0.05,
        n_estimators=100,
        random_state=42,
    )
    detector.fit(X_train)
    return detector


def main():
    print("=" * 60)
    print("  CivicPulse — ML Model Training")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}Z")
    print("=" * 60)

    # Create output directory
    models_dir = ROOT / "models"
    models_dir.mkdir(exist_ok=True)

    # Generate data
    print("\n📊 Generating synthetic training data...")
    X, y, feature_names = generate_synthetic_dataset(n_samples=5000)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"   Training: {len(X_train)} samples | Validation: {len(X_val)} samples")

    # Train fusion model
    print("\n🧠 Training CSS fusion model (XGBoost)...")
    fusion_model, fusion_metrics = train_fusion_model(X_train, y_train, X_val, y_val)
    print(f"   MAE:  {fusion_metrics['mae']}")
    print(f"   RMSE: {fusion_metrics['rmse']}")
    print(f"   R²:   {fusion_metrics['r2']}")

    # Check precision floor
    if fusion_metrics["r2"] < 0.75:
        print("   ⚠️  WARNING: R² below 0.75 threshold — review training data quality")
    else:
        print("   ✅ Model meets accuracy threshold")

    # Train anomaly detector
    print("\n🔍 Training anomaly detector (Isolation Forest)...")
    anomaly_detector = train_anomaly_detector(X_train)
    print("   ✅ Detector trained")

    # Save models
    print("\n💾 Saving model artifacts...")
    fusion_path = models_dir / "fusion_model.joblib"
    anomaly_path = models_dir / "anomaly_detector.joblib"
    joblib.dump(fusion_model, fusion_path)
    joblib.dump(anomaly_detector, anomaly_path)
    print(f"   → {fusion_path}")
    print(f"   → {anomaly_path}")

    # Save training report
    report = {
        "trained_at": datetime.now(timezone.utc).isoformat() + "Z",
        "dataset": {
            "total_samples": len(X),
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "features": feature_names,
            "data_source": "synthetic (replace with Firestore historical data for production)",
        },
        "fusion_model": {
            "algorithm": "XGBoost (XGBRegressor)",
            "metrics": fusion_metrics,
            "hyperparameters": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
            },
        },
        "anomaly_detector": {
            "algorithm": "Isolation Forest",
            "contamination": 0.05,
            "n_estimators": 100,
        },
    }
    report_path = models_dir / "training_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"   → {report_path}")

    print("\n" + "=" * 60)
    print("  ✅ ALL MODELS TRAINED AND SAVED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
