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
    import json as _json

    parser = argparse.ArgumentParser(description="CivicPulse CSS Fusion Model")
    parser.add_argument("--train", action="store_true", help="Train the fusion model")
    parser.add_argument("--predict", action="store_true", help="Predict CSS for a ward")
    parser.add_argument("--data-path", type=str, default=None, help="Path to training data JSON")
    parser.add_argument("--ward-id", type=str, default=None, help="Ward ID for prediction")
    parser.add_argument("--save-dir", type=str, default="./models/fusion", help="Directory to save model")
    args = parser.parse_args()

    model = CSSFusionModel()

    if args.train:
        if not args.data_path:
            print("Error: --data-path is required for training")
            sys.exit(1)

        print(f"Loading training data from {args.data_path}...")
        try:
            with open(args.data_path) as f:
                data = _json.load(f)

            import numpy as np
            if isinstance(data, list):
                # Assume list of feature dicts or arrays
                features = np.array([list(d.values()) if isinstance(d, dict) else d for d in data])
                # Generate synthetic labels for demo
                labels = np.random.rand(len(features)) * 100
            else:
                print("Error: Expected JSON array of feature objects")
                sys.exit(1)

            model.train(features, labels)
            save_path = model.save(args.save_dir)
            print(f"Model trained and saved to {save_path}")

        except Exception as e:
            print(f"Training failed: {e}")
            sys.exit(1)

    elif args.predict:
        if not args.ward_id:
            print("Error: --ward-id is required for prediction")
            sys.exit(1)

        print(f"Predicting CSS for ward {args.ward_id}...")
        try:
            model.load(args.save_dir)
            # Generate sample features for demo prediction
            import numpy as np
            sample_features = np.random.rand(1, len(model.feature_names))
            score = model.predict(sample_features)
            print(f"Predicted CSS score for {args.ward_id}: {score[0]:.1f}")
        except FileNotFoundError:
            print("No trained model found. Run with --train first.")
            sys.exit(1)
        except Exception as e:
            print(f"Prediction failed: {e}")
            sys.exit(1)

    else:
        parser.print_help()

