"""
CivicPulse — CSS Fusion Model

XGBoost regressor that computes Community Stress Scores (0-100).
Trained on labeled distress events from synthetic/historical data.

Key rules:
- If < 60 days of data exist, refuse to predict and log a warning
- On prediction failure, return {"css": None, "error": "insufficient_data"}
- Never return 0 by default
- Model is versioned with timestamp
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

from feature_engineering import build_feature_vector, get_feature_names

logger = logging.getLogger(__name__)

ML_MODEL_PATH = os.environ.get("ML_MODEL_PATH", "/models/fusion/latest/")
ML_TRAINING_MIN_DAYS = int(os.environ.get("ML_TRAINING_MIN_DAYS", "60"))
ML_MIN_PRECISION_THRESHOLD = float(os.environ.get("ML_MIN_PRECISION_THRESHOLD", "0.75"))


class CSSFusionModel:
    """XGBoost-based Community Stress Score fusion model."""

    def __init__(self):
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names = get_feature_names()
        self.version: Optional[str] = None
        self.trained_at: Optional[datetime] = None

    def train(
        self,
        features_df: pd.DataFrame,
        labels: np.ndarray,
        data_days: int,
    ) -> dict:
        """
        Train the CSS fusion model.

        Args:
            features_df: DataFrame with feature columns
            labels: CSS scores (0-100) as training labels
            data_days: Number of days of data available

        Returns:
            Training metrics dictionary

        Raises:
            ValueError: If insufficient training data
        """
        if data_days < ML_TRAINING_MIN_DAYS:
            raise ValueError(
                f"Insufficient training data: {data_days} days available, "
                f"minimum {ML_TRAINING_MIN_DAYS} days required. "
                f"Generate more synthetic data or wait for more real data."
            )

        logger.info(
            "Training CSS fusion model with %d samples (%d days of data)",
            len(features_df), data_days,
        )

        # Temporal split to avoid data leakage (80/20)
        X_train, X_val, y_train, y_val = train_test_split(
            features_df, labels, test_size=0.2, shuffle=False,
        )

        self.model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective="reg:squarederror",
            random_state=42,
        )

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # Evaluate
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_mae = float(np.mean(np.abs(train_pred - y_train)))
        val_mae = float(np.mean(np.abs(val_pred - y_val)))
        train_rmse = float(np.sqrt(np.mean((train_pred - y_train) ** 2)))
        val_rmse = float(np.sqrt(np.mean((val_pred - y_val) ** 2)))

        # Feature importance
        importance = dict(zip(self.feature_names, self.model.feature_importances_.tolist()))

        self.version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.trained_at = datetime.now(timezone.utc)

        metrics = {
            "version": self.version,
            "trained_at": self.trained_at.isoformat(),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "train_mae": round(train_mae, 4),
            "val_mae": round(val_mae, 4),
            "train_rmse": round(train_rmse, 4),
            "val_rmse": round(val_rmse, 4),
            "data_days": data_days,
            "feature_importance": importance,
        }

        logger.info(
            "Model trained: version=%s, train_mae=%.4f, val_mae=%.4f",
            self.version, train_mae, val_mae,
        )

        return metrics

    def predict(self, features: dict[str, float], data_days: int) -> dict:
        """
        Predict CSS score for a ward.

        Args:
            features: Feature dictionary from build_feature_vector()
            data_days: Number of days of data available for this ward

        Returns:
            {"css": float, "confidence": float} on success
            {"css": None, "error": str} on failure
        """
        if self.model is None:
            return {"css": None, "error": "model_not_loaded"}

        if data_days < ML_TRAINING_MIN_DAYS:
            logger.warning(
                "Insufficient data for prediction: %d days (minimum: %d)",
                data_days, ML_TRAINING_MIN_DAYS,
            )
            return {
                "css": None,
                "error": "insufficient_data",
                "message": f"Need {ML_TRAINING_MIN_DAYS} days of data, have {data_days}",
            }

        try:
            # Build feature array in correct order
            feature_array = np.array(
                [[features.get(name, 0.0) for name in self.feature_names]]
            )

            prediction = float(self.model.predict(feature_array)[0])

            # Clamp to valid CSS range
            css_score = max(0.0, min(100.0, prediction))

            return {
                "css": round(css_score, 2),
                "confidence": self._compute_prediction_confidence(features),
                "model_version": self.version,
            }
        except Exception as e:
            logger.error("Prediction failed: %s", e, exc_info=True)
            return {"css": None, "error": f"prediction_failed: {str(e)}"}

    def _compute_prediction_confidence(self, features: dict[str, float]) -> float:
        """
        Estimate prediction confidence based on input signal coverage.
        More signal types present → higher confidence.
        """
        signal_types = [
            "pharmacy_intensity_24h", "school_intensity_24h",
            "utility_intensity_24h", "social_intensity_24h",
            "foodbank_intensity_24h", "health_intensity_24h",
        ]
        active_signals = sum(1 for st in signal_types if features.get(st, 0) > 0.01)
        return round(min(1.0, 0.3 + (active_signals / len(signal_types)) * 0.7), 2)

    def save(self, path: Optional[str] = None) -> str:
        """Save model to disk."""
        if self.model is None:
            raise ValueError("No model to save — train first")

        save_dir = path or os.path.join(ML_MODEL_PATH, self.version or "latest")
        os.makedirs(save_dir, exist_ok=True)

        model_path = os.path.join(save_dir, "model.joblib")
        joblib.dump(self.model, model_path)

        meta_path = os.path.join(save_dir, "metadata.json")
        metadata = {
            "version": self.version,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "feature_names": self.feature_names,
            "algorithm": "XGBRegressor",
        }
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info("Model saved to %s", save_dir)
        return save_dir

    def load(self, path: Optional[str] = None) -> None:
        """Load model from disk."""
        load_dir = path or os.path.join(ML_MODEL_PATH, "latest")
        model_path = os.path.join(load_dir, "model.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No model found at {model_path}")

        self.model = joblib.load(model_path)

        meta_path = os.path.join(load_dir, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                metadata = json.load(f)
            self.version = metadata.get("version")
            self.feature_names = metadata.get("feature_names", get_feature_names())

        logger.info("Model loaded from %s (version=%s)", load_dir, self.version)


# ── CLI Entry Point ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    import sys
    import json as _json
    from collections import defaultdict
    from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score,
        precision_score, recall_score,
    )

    parser = argparse.ArgumentParser(description="CivicPulse CSS Fusion Model")
    parser.add_argument("--train", action="store_true", help="Train the fusion model")
    parser.add_argument("--predict", action="store_true", help="Predict CSS for a ward")
    parser.add_argument("--data-path", type=str, default=None, help="Path to signals JSON")
    parser.add_argument("--labels-path", type=str, default=None, help="Path to CSS labels JSON")
    parser.add_argument("--ward-id", type=str, default=None, help="Ward ID for prediction")
    parser.add_argument("--save-dir", type=str, default="./models/fusion", help="Directory to save model")
    parser.add_argument("--report-dir", type=str, default="./docs", help="Directory to save performance report")
    args = parser.parse_args()

    model = CSSFusionModel()

    if args.train:
        data_path = args.data_path or "data/synthetic/signals_sample.json"
        labels_path = args.labels_path or "data/synthetic/css_labels.json"

        print(f"📊 Loading signals from {data_path}...")
        with open(data_path) as f:
            signals = _json.load(f)

        print(f"🏷️  Loading ground-truth CSS labels from {labels_path}...")
        with open(labels_path) as f:
            css_labels = _json.load(f)

        # Build ward-day label lookup
        label_lookup = {}
        for lbl in css_labels:
            key = f"{lbl['ward_code']}_{lbl['date']}"
            label_lookup[key] = lbl["css"]

        # Group signals by ward+date and build feature vectors
        buckets = defaultdict(lambda: defaultdict(list))
        for sig in signals:
            date_str = sig["timestamp"][:10]
            buckets[sig["location_pin"]][date_str].append(sig)

        feature_rows = []
        label_values = []

        for ward_code, day_map in buckets.items():
            for date_str, day_signals in day_map.items():
                key = f"{ward_code}_{date_str}"
                if key not in label_lookup:
                    continue

                # Build feature dict from day's signals
                type_intensities = defaultdict(list)
                for sig in day_signals:
                    type_intensities[sig["signal_type"]].append(sig["intensity_score"])

                features = {}
                signal_types = ["pharmacy", "school", "utility", "social", "foodbank", "health"]
                for stype in signal_types:
                    vals = type_intensities.get(stype, [0.0])
                    avg_intensity = sum(vals) / len(vals) if vals else 0.0
                    features[f"{stype}_intensity_24h"] = avg_intensity
                    features[f"{stype}_count_24h"] = float(len(type_intensities.get(stype, [])))

                # Simple trend features (placeholder for full temporal features)
                features["total_signal_count"] = float(len(day_signals))
                features["active_signal_types"] = float(len(type_intensities))
                features["max_intensity"] = max(
                    (sum(v)/len(v) for v in type_intensities.values()), default=0.0
                )
                features["mean_intensity"] = sum(
                    sum(v)/len(v) for v in type_intensities.values()
                ) / max(len(type_intensities), 1)

                feature_rows.append(features)
                label_values.append(label_lookup[key])

        print(f"   → {len(feature_rows)} training samples built")

        if len(feature_rows) < 100:
            print("⚠️  Too few samples. Generate more synthetic data first.")
            sys.exit(1)

        features_df = pd.DataFrame(feature_rows).fillna(0)
        labels = np.array(label_values)
        data_days = len(set(lbl["date"] for lbl in css_labels))

        print(f"🚀 Training model ({data_days} days of data)...")
        metrics = model.train(features_df, labels, data_days)

        # Compute extended evaluation metrics
        X_train, X_val, y_train, y_val = train_test_split(
            features_df, labels, test_size=0.2, shuffle=False,
        )
        val_pred = model.model.predict(X_val)

        mae = mean_absolute_error(y_val, val_pred)
        rmse = float(np.sqrt(mean_squared_error(y_val, val_pred)))
        r2 = r2_score(y_val, val_pred)

        # Precision/Recall at CSS thresholds
        def threshold_metrics(y_true, y_pred, threshold):
            y_true_bin = (y_true >= threshold).astype(int)
            y_pred_bin = (y_pred >= threshold).astype(int)
            if y_true_bin.sum() == 0:
                return 0.0, 0.0
            prec = precision_score(y_true_bin, y_pred_bin, zero_division=0)
            rec = recall_score(y_true_bin, y_pred_bin, zero_division=0)
            return round(prec, 4), round(rec, 4)

        p56, r56 = threshold_metrics(y_val, val_pred, 56)
        p76, r76 = threshold_metrics(y_val, val_pred, 76)

        # Feature importance ranking
        importance = sorted(
            zip(features_df.columns, model.model.feature_importances_),
            key=lambda x: x[1], reverse=True,
        )

        # Save model
        save_path = model.save(args.save_dir)

        # Print results
        print(f"\n{'='*50}")
        print(f"✅ Model Performance Report")
        print(f"{'='*50}")
        print(f"  MAE:  {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  R²:   {r2:.4f}")
        print(f"\n  CSS ≥ 56 — Precision: {p56:.2%}, Recall: {r56:.2%}")
        print(f"  CSS ≥ 76 — Precision: {p76:.2%}, Recall: {r76:.2%}")
        print(f"\n  Top 5 Features:")
        for fname, fimp in importance[:5]:
            print(f"    {fname}: {fimp:.4f}")
        print(f"\n  Model saved to: {save_path}")

        # Write model-performance.md
        report_path = os.path.join(args.report_dir, "model-performance.md")
        os.makedirs(args.report_dir, exist_ok=True)
        with open(report_path, "w") as f:
            f.write("# Model Performance Report\n\n")
            f.write(f"> Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
            f.write("## Regression Metrics (20% Holdout)\n\n")
            f.write(f"| Metric | Value |\n|---|---|\n")
            f.write(f"| MAE | {mae:.2f} |\n")
            f.write(f"| RMSE | {rmse:.2f} |\n")
            f.write(f"| R² | {r2:.4f} |\n\n")
            f.write("## Classification Metrics at Dispatch Thresholds\n\n")
            f.write(f"| Threshold | Precision | Recall |\n|---|---|---|\n")
            f.write(f"| CSS ≥ 56 (High) | {p56:.2%} | {r56:.2%} |\n")
            f.write(f"| CSS ≥ 76 (Critical) | {p76:.2%} | {r76:.2%} |\n\n")
            f.write("## Top 5 Feature Importances\n\n")
            f.write(f"| Rank | Feature | Importance |\n|---|---|---|\n")
            for i, (fname, fimp) in enumerate(importance[:5], 1):
                f.write(f"| {i} | `{fname}` | {fimp:.4f} |\n")
            f.write(f"\n## Training Details\n\n")
            f.write(f"- **Samples**: {len(feature_rows)} ({data_days} days)\n")
            f.write(f"- **Train/Val Split**: 80/20 temporal\n")
            f.write(f"- **Algorithm**: XGBoost (n_estimators=200, max_depth=6)\n")
            f.write(f"- **Version**: {model.version}\n")
        print(f"  Report saved to: {report_path}")

    elif args.predict:
        if not args.ward_id:
            print("Error: --ward-id is required for prediction")
            sys.exit(1)

        print(f"Predicting CSS for ward {args.ward_id}...")
        try:
            model.load(args.save_dir)
            # Generate sample features for demo prediction
            sample_features = {name: np.random.rand() for name in model.feature_names}
            result = model.predict(sample_features, data_days=60)
            if result.get("css") is not None:
                print(f"Predicted CSS score for {args.ward_id}: {result['css']:.1f}")
            else:
                print(f"Prediction error: {result.get('error', 'unknown')}")
        except FileNotFoundError:
            print("No trained model found. Run with --train first.")
            sys.exit(1)
        except Exception as e:
            print(f"Prediction failed: {e}")
            sys.exit(1)

    else:
        parser.print_help()
