"""
CivicPulse — Feature Engineering

Computes the feature vector for each ward to feed the CSS fusion model.
Features include signal intensities, temporal decay, spatial context,
historical baselines, and cyclical time encodings.
"""

import math
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Temporal decay parameter (configurable)
DECAY_LAMBDA = 0.05

# Signal types expected
SIGNAL_TYPES = ["pharmacy", "school", "utility", "social", "foodbank", "health"]


def compute_temporal_decay(hours_since: float, decay_lambda: float = DECAY_LAMBDA) -> float:
    """
    Compute exponential temporal decay weight.
    weight(t) = exp(-λ × hours_since_signal)
    """
    return math.exp(-decay_lambda * max(0, hours_since))


def compute_cyclic_encoding(value: float, period: float) -> tuple[float, float]:
    """
    Encode a cyclical feature using sin/cos encoding.
    Returns (sin_component, cos_component).
    """
    angle = 2 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


def compute_signal_intensity_24h(
    signals_df: pd.DataFrame,
    signal_type: str,
    now: Optional[datetime] = None,
) -> float:
    """
    Compute weighted average intensity for a signal type over past 24 hours.
    More recent signals get higher weight via temporal decay.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)
    type_signals = signals_df[
        (signals_df["signal_type"] == signal_type)
        & (signals_df["signal_timestamp"] >= cutoff)
    ]

    if type_signals.empty:
        return 0.0

    weights = []
    intensities = []

    for _, row in type_signals.iterrows():
        hours_since = (now - row["signal_timestamp"]).total_seconds() / 3600.0
        weight = compute_temporal_decay(hours_since) * float(row.get("confidence", 0.5))
        weights.append(weight)
        intensities.append(float(row["intensity_score"]))

    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0

    return sum(w * i for w, i in zip(weights, intensities)) / total_weight


def compute_signal_recency_score(
    signals_df: pd.DataFrame,
    now: Optional[datetime] = None,
) -> float:
    """
    Compute overall recency score based on most recent signal across all types.
    Returns 1.0 if a signal arrived in the last hour, decays after that.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if signals_df.empty:
        return 0.0

    most_recent = signals_df["signal_timestamp"].max()
    hours_since = (now - most_recent).total_seconds() / 3600.0
    return compute_temporal_decay(hours_since)


def compute_css_rolling_average(
    css_history_df: pd.DataFrame,
    days: int,
    now: Optional[datetime] = None,
) -> float:
    """Compute rolling average CSS score over N days."""
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff = now - timedelta(days=days)
    recent = css_history_df[css_history_df["computed_at"] >= cutoff]

    if recent.empty:
        return 0.0

    return float(recent["css_score"].mean())


def compute_css_trend_slope(
    css_history_df: pd.DataFrame,
    days: int = 7,
    now: Optional[datetime] = None,
) -> float:
    """
    Compute linear trend slope of CSS over past N days.
    Positive = worsening, Negative = improving.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff = now - timedelta(days=days)
    recent = css_history_df[css_history_df["computed_at"] >= cutoff].copy()

    if len(recent) < 2:
        return 0.0

    recent = recent.sort_values("computed_at")
    x = np.arange(len(recent), dtype=float)
    y = recent["css_score"].values.astype(float)

    # Simple linear regression
    x_mean = x.mean()
    y_mean = y.mean()
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)

    if denominator == 0:
        return 0.0

    return float(numerator / denominator)


def build_feature_vector(
    ward_id: str,
    signals_df: pd.DataFrame,
    css_history_df: pd.DataFrame,
    neighbor_css_scores: list[float],
    now: Optional[datetime] = None,
) -> dict[str, float]:
    """
    Build the complete feature vector for a ward.

    Args:
        ward_id: UUID of the ward
        signals_df: DataFrame of signals for this ward
        css_history_df: DataFrame of CSS history for this ward
        neighbor_css_scores: List of CSS scores of neighboring wards
        now: Current timestamp

    Returns:
        Dictionary of feature name -> value
    """
    if now is None:
        now = datetime.now(timezone.utc)

    features = {}

    # Signal intensities (per type, past 24h weighted average)
    for signal_type in SIGNAL_TYPES:
        key = f"{signal_type}_intensity_24h"
        features[key] = compute_signal_intensity_24h(signals_df, signal_type, now)

    # Temporal decay — overall signal recency
    features["signal_recency_score"] = compute_signal_recency_score(signals_df, now)

    # Spatial context — neighboring ward CSS
    if neighbor_css_scores:
        features["neighbor_avg_css"] = float(np.mean(neighbor_css_scores))
        features["neighbor_max_css"] = float(np.max(neighbor_css_scores))
    else:
        features["neighbor_avg_css"] = 0.0
        features["neighbor_max_css"] = 0.0

    # Historical baseline
    features["css_rolling_7d_avg"] = compute_css_rolling_average(css_history_df, 7, now)
    features["css_rolling_30d_avg"] = compute_css_rolling_average(css_history_df, 30, now)
    features["css_trend_slope"] = compute_css_trend_slope(css_history_df, 7, now)

    # Cyclical encodings
    day_of_week = now.weekday()
    hour_of_day = now.hour

    dow_sin, dow_cos = compute_cyclic_encoding(day_of_week, 7.0)
    hod_sin, hod_cos = compute_cyclic_encoding(hour_of_day, 24.0)

    features["day_of_week_sin"] = dow_sin
    features["day_of_week_cos"] = dow_cos
    features["hour_of_day_sin"] = hod_sin
    features["hour_of_day_cos"] = hod_cos

    return features


def get_feature_names() -> list[str]:
    """Return ordered list of feature names for model input."""
    names = []
    for st in SIGNAL_TYPES:
        names.append(f"{st}_intensity_24h")
    names.extend([
        "signal_recency_score",
        "neighbor_avg_css",
        "neighbor_max_css",
        "css_rolling_7d_avg",
        "css_rolling_30d_avg",
        "css_trend_slope",
        "day_of_week_sin",
        "day_of_week_cos",
        "hour_of_day_sin",
        "hour_of_day_cos",
    ])
    return names
