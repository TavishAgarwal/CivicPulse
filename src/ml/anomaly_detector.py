"""
CivicPulse — Anomaly Detector (Early Warning Pulse)

Isolation Forest running every 4 hours on the 6 signal intensity features.
Detects sudden spike events that CSS hasn't yet reflected.

Output: {"anomaly": bool, "severity": float, "ward_id": str}
Severity 0.0-1.0 (higher = more anomalous)
Anomalies above 0.7 severity trigger an "Early Warning Pulse" even if CSS < 56
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

ANOMALY_MODEL_PATH = os.environ.get("ANOMALY_MODEL_PATH", "/models/anomaly/latest/")
ANOMALY_SEVERITY_THRESHOLD = float(os.environ.get("ANOMALY_SEVERITY_THRESHOLD", "0.7"))
CONTAMINATION_RATE = float(os.environ.get("ANOMALY_CONTAMINATION_RATE", "0.05"))

SIGNAL_FEATURES = [
    "pharmacy_intensity_24h",
    "school_intensity_24h",
    "utility_intensity_24h",
    "social_intensity_24h",
    "foodbank_intensity_24h",
    "health_intensity_24h",
]


class AnomalyDetector:
    """Isolation Forest anomaly detector for early warning pulses."""

    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.version: Optional[str] = None

    def train(self, features_array: np.ndarray) -> dict:
        """
        Train the anomaly detector on historical signal intensity data.

        Args:
            features_array: 2D array of shape (n_samples, 6) with signal intensities

        Returns:
            Training info dictionary
        """
        if features_array.shape[1] != len(SIGNAL_FEATURES):
            raise ValueError(
                f"Expected {len(SIGNAL_FEATURES)} features, got {features_array.shape[1]}"
            )

        logger.info("Training anomaly detector with %d samples", len(features_array))

        self.model = IsolationForest(
            n_estimators=100,
            contamination=CONTAMINATION_RATE,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )

        self.model.fit(features_array)
        self.version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        logger.info("Anomaly detector trained: version=%s", self.version)

        return {
            "version": self.version,
            "n_samples": len(features_array),
            "contamination": CONTAMINATION_RATE,
            "n_features": len(SIGNAL_FEATURES),
        }

    def detect(self, ward_id: str, features: dict[str, float]) -> dict:
        """
        Run anomaly detection for a single ward.

        Args:
            ward_id: UUID of the ward
            features: Feature dictionary with signal intensity values

        Returns:
            {"anomaly": bool, "severity": float, "ward_id": str}
        """
        if self.model is None:
            logger.warning("Anomaly detector not trained/loaded — skipping detection")
            return {
                "anomaly": False,
                "severity": 0.0,
                "ward_id": ward_id,
                "error": "model_not_loaded",
            }

        try:
            # Extract signal features in correct order
            feature_values = [features.get(f, 0.0) for f in SIGNAL_FEATURES]
            feature_array = np.array([feature_values])

            # Isolation Forest score: lower = more anomalous
            # decision_function returns negative for anomalies, positive for normal
            raw_score = self.model.decision_function(feature_array)[0]
            prediction = self.model.predict(feature_array)[0]

            # Convert to severity (0-1, higher = more anomalous)
            # Normalize decision function output
            severity = max(0.0, min(1.0, 0.5 - float(raw_score)))

            is_anomaly = prediction == -1 or severity >= ANOMALY_SEVERITY_THRESHOLD

            result = {
                "anomaly": bool(is_anomaly),
                "severity": round(float(severity), 3),
                "ward_id": ward_id,
                "triggering_signals": self._get_triggering_signals(features, feature_values),
            }

            if is_anomaly and severity >= ANOMALY_SEVERITY_THRESHOLD:
                logger.warning(
                    "🚨 EARLY WARNING PULSE: ward=%s severity=%.3f",
                    ward_id, severity,
                )

            return result

        except Exception as e:
            logger.error("Anomaly detection failed for ward %s: %s", ward_id, e)
            return {
                "anomaly": False,
                "severity": 0.0,
                "ward_id": ward_id,
                "error": str(e),
            }

    def _get_triggering_signals(
        self, features: dict, feature_values: list[float]
    ) -> list[dict]:
        """Identify which signal types are contributing to the anomaly."""
        triggering = []
        mean_intensity = np.mean(feature_values) if feature_values else 0

        for i, fname in enumerate(SIGNAL_FEATURES):
            value = feature_values[i]
            if value > mean_intensity + 0.2:  # Significantly above average
                signal_type = fname.replace("_intensity_24h", "")
                triggering.append({
                    "signal_type": signal_type,
                    "intensity": round(value, 3),
                    "deviation": round(value - mean_intensity, 3),
                })

        return sorted(triggering, key=lambda x: x["deviation"], reverse=True)

    def save(self, path: Optional[str] = None) -> str:
        """Save model to disk."""
        if self.model is None:
            raise ValueError("No model to save")

        save_dir = path or os.path.join(ANOMALY_MODEL_PATH, self.version or "latest")
        os.makedirs(save_dir, exist_ok=True)

        model_path = os.path.join(save_dir, "anomaly_model.joblib")
        joblib.dump(self.model, model_path)

        logger.info("Anomaly model saved to %s", save_dir)
        return save_dir

    def load(self, path: Optional[str] = None) -> None:
        """Load model from disk."""
        load_dir = path or os.path.join(ANOMALY_MODEL_PATH, "latest")
        model_path = os.path.join(load_dir, "anomaly_model.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No anomaly model found at {model_path}")

        self.model = joblib.load(model_path)
        logger.info("Anomaly model loaded from %s", load_dir)


# ── CLI Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CivicPulse Anomaly Detector")
    parser.add_argument("--train", action="store_true", help="Train the anomaly detector")
    parser.add_argument("--detect", action="store_true", help="Run anomaly detection on a ward")
    parser.add_argument("--ward-id", type=str, default=None, help="Ward ID for detection")
    parser.add_argument("--data-path", type=str, default=None, help="Path to training data")
    parser.add_argument("--save-dir", type=str, default="./models/anomaly", help="Directory to save/load model")
    args = parser.parse_args()

    detector = AnomalyDetector()

    if args.train:
        print("Training anomaly detector...")
        import numpy as np
        if args.data_path:
            import json as _json
            with open(args.data_path) as f:
                data = _json.load(f)
            features = np.array([list(d.values()) if isinstance(d, dict) else d for d in data])
        else:
            # Generate sample data for demo training
            features = np.random.randn(200, 5) * 0.5
            print("Using synthetic data for training (no --data-path provided)")

        detector.train(features)
        save_path = detector.save(args.save_dir)
        print(f"Anomaly model saved to {save_path}")

    elif args.detect:
        if not args.ward_id:
            print("Error: --ward-id is required for detection")
            import sys
            sys.exit(1)

        print(f"Running anomaly detection for ward {args.ward_id}...")
        try:
            detector.load(args.save_dir)
            import numpy as np
            sample = np.random.randn(1, 5)
            result = detector.detect(sample)
            print(f"Detection result: {result}")
        except FileNotFoundError:
            print("No trained model found. Run with --train first.")
            import sys
            sys.exit(1)

    else:
        parser.print_help()

