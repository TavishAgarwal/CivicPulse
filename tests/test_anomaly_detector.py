"""
CivicPulse — Anomaly Detector Tests
Tests Isolation Forest anomaly detection, severity scoring, and edge cases.
"""

import sys
import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ml"))

from anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """Tests for the AnomalyDetector class."""

    def test_initialization(self):
        """AnomalyDetector should instantiate without error."""
        detector = AnomalyDetector()
        assert detector is not None

    def test_has_train_method(self):
        """Must have a train method."""
        detector = AnomalyDetector()
        assert hasattr(detector, "train")
        assert callable(detector.train)

    def test_has_detect_method(self):
        """Must have a detect method."""
        detector = AnomalyDetector()
        assert hasattr(detector, "detect")
        assert callable(detector.detect)

    def test_train_with_data(self):
        """Train should accept numpy array or list of feature vectors."""
        detector = AnomalyDetector()
        # Normal data distribution
        data = np.random.randn(100, 6)
        detector.train(data)
        assert detector.model is not None

    def test_detect_returns_results(self):
        """Detect should return anomaly detection results."""
        detector = AnomalyDetector()
        train_data = np.random.randn(100, 6)
        detector.train(train_data)

        test_features = {
            "pharmacy_intensity_24h": 0.5,
            "school_intensity_24h": 0.3,
            "utility_intensity_24h": 0.2,
            "social_intensity_24h": 0.4,
            "foodbank_intensity_24h": 0.1,
            "health_intensity_24h": 0.6,
        }
        result = detector.detect("ward-001", test_features)
        assert result is not None
        assert "anomaly" in result

    def test_severity_score_bounded(self):
        """Severity scores should be between 0 and 1."""
        detector = AnomalyDetector()
        train_data = np.random.randn(200, 6)
        detector.train(train_data)

        test_features = {
            "pharmacy_intensity_24h": 0.1,
            "school_intensity_24h": 0.1,
            "utility_intensity_24h": 0.1,
            "social_intensity_24h": 0.1,
            "foodbank_intensity_24h": 0.1,
            "health_intensity_24h": 0.1,
        }
        result = detector.detect("ward-002", test_features)
        assert 0.0 <= result["severity"] <= 1.0

    def test_detects_extreme_outlier(self):
        """Extreme outliers should be detected as anomalous."""
        detector = AnomalyDetector()
        train_data = np.random.randn(200, 6) * 0.1
        detector.train(train_data)

        outlier_features = {
            "pharmacy_intensity_24h": 100.0,
            "school_intensity_24h": 100.0,
            "utility_intensity_24h": 100.0,
            "social_intensity_24h": 100.0,
            "foodbank_intensity_24h": 100.0,
            "health_intensity_24h": 100.0,
        }
        result = detector.detect("ward-003", outlier_features)
        assert result["anomaly"] is True
