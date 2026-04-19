"""
CivicPulse — Feature Engineering Unit Tests
"""

import sys
import os
import pytest
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ml"))

from feature_engineering import (
    compute_temporal_decay,
    compute_cyclic_encoding,
    compute_signal_intensity_24h,
    compute_signal_recency_score,
    compute_css_rolling_average,
    compute_css_trend_slope,
    build_feature_vector,
    get_feature_names,
)


class TestTemporalDecay:
    def test_zero_hours(self):
        assert compute_temporal_decay(0) == 1.0

    def test_positive_hours(self):
        decay = compute_temporal_decay(10)
        assert 0 < decay < 1.0

    def test_large_hours(self):
        decay = compute_temporal_decay(100)
        assert decay < 0.01

    def test_negative_clipped(self):
        assert compute_temporal_decay(-5) == 1.0


class TestCyclicEncoding:
    def test_sin_cos_range(self):
        s, c = compute_cyclic_encoding(3.5, 7.0)
        assert -1 <= s <= 1
        assert -1 <= c <= 1

    def test_period_wrap(self):
        s0, c0 = compute_cyclic_encoding(0, 7.0)
        s7, c7 = compute_cyclic_encoding(7.0, 7.0)
        assert abs(s0 - s7) < 1e-10
        assert abs(c0 - c7) < 1e-10


class TestSignalIntensity24h:
    def test_empty_signals(self):
        df = pd.DataFrame(columns=["signal_type", "intensity_score", "confidence", "signal_timestamp"])
        result = compute_signal_intensity_24h(df, "pharmacy")
        assert result == 0.0

    def test_with_signals(self):
        now = datetime.now(timezone.utc)
        df = pd.DataFrame({
            "signal_type": ["pharmacy", "pharmacy", "school"],
            "intensity_score": [0.7, 0.5, 0.3],
            "confidence": [0.8, 0.9, 0.7],
            "signal_timestamp": [
                now - timedelta(hours=1),
                now - timedelta(hours=12),
                now - timedelta(hours=2),
            ],
        })
        result = compute_signal_intensity_24h(df, "pharmacy", now)
        assert 0 < result <= 1.0


class TestFeatureVector:
    def test_all_features_present(self):
        now = datetime.now(timezone.utc)
        signals_df = pd.DataFrame({
            "signal_type": ["pharmacy"],
            "intensity_score": [0.5],
            "confidence": [0.8],
            "signal_timestamp": [now - timedelta(hours=2)],
        })
        css_df = pd.DataFrame({
            "css_score": [45.0],
            "computed_at": [now - timedelta(days=1)],
        })
        features = build_feature_vector("ward-1", signals_df, css_df, [40.0, 50.0], now)

        expected_names = get_feature_names()
        for name in expected_names:
            assert name in features, f"Missing feature: {name}"

    def test_feature_count(self):
        names = get_feature_names()
        assert len(names) == 16  # 6 signals + recency + 2 neighbor + 3 historical + 4 cyclic
