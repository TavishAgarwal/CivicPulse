"""
CivicPulse — Fusion Model Unit Tests
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ml"))

from fusion_model import CSSFusionModel
from feature_engineering import get_feature_names


class TestCSSFusionModel:
    def test_insufficient_data_raises(self):
        model = CSSFusionModel()
        features = pd.DataFrame(np.random.rand(10, 16), columns=get_feature_names())
        labels = np.random.rand(10) * 100

        with pytest.raises(ValueError, match="Insufficient training data"):
            model.train(features, labels, data_days=30)

    def test_train_and_predict(self):
        model = CSSFusionModel()
        n_samples = 200
        features = pd.DataFrame(
            np.random.rand(n_samples, 16), columns=get_feature_names()
        )
        labels = np.random.rand(n_samples) * 100

        metrics = model.train(features, labels, data_days=60)

        assert "version" in metrics
        assert "val_mae" in metrics
        assert metrics["train_samples"] > 0

        # Test prediction
        feature_dict = {name: 0.5 for name in get_feature_names()}
        result = model.predict(feature_dict, data_days=60)
        assert result["css"] is not None
        assert 0 <= result["css"] <= 100
        assert "confidence" in result

    def test_predict_without_training(self):
        model = CSSFusionModel()
        feature_dict = {name: 0.5 for name in get_feature_names()}
        result = model.predict(feature_dict, data_days=60)
        assert result["css"] is None
        assert result["error"] == "model_not_loaded"

    def test_predict_insufficient_data(self):
        model = CSSFusionModel()
        # Train first
        features = pd.DataFrame(
            np.random.rand(100, 16), columns=get_feature_names()
        )
        labels = np.random.rand(100) * 100
        model.train(features, labels, data_days=60)

        # Predict with insufficient data
        feature_dict = {name: 0.5 for name in get_feature_names()}
        result = model.predict(feature_dict, data_days=30)
        assert result["css"] is None
        assert result["error"] == "insufficient_data"

    def test_css_clamped_to_range(self):
        model = CSSFusionModel()
        features = pd.DataFrame(
            np.random.rand(200, 16), columns=get_feature_names()
        )
        labels = np.random.rand(200) * 100
        model.train(features, labels, data_days=60)

        feature_dict = {name: 0.5 for name in get_feature_names()}
        result = model.predict(feature_dict, data_days=60)
        assert 0 <= result["css"] <= 100
