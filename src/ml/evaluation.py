"""
CivicPulse — Model Evaluation

Evaluation metrics for CSS fusion model and anomaly detector.
"""

import logging
from typing import Optional

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def evaluate_css_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    threshold_high: float = 56.0,
    threshold_critical: float = 76.0,
) -> dict:
    """
    Evaluate CSS fusion model performance.

    Args:
        y_true: True CSS scores
        y_pred: Predicted CSS scores
        threshold_high: CSS high-stress threshold
        threshold_critical: CSS critical threshold

    Returns:
        Dictionary of evaluation metrics
    """
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    # Classification metrics at threshold boundaries
    true_high = y_true >= threshold_high
    pred_high = y_pred >= threshold_high

    if true_high.sum() > 0:
        precision_high = float(np.sum(true_high & pred_high) / max(pred_high.sum(), 1))
        recall_high = float(np.sum(true_high & pred_high) / true_high.sum())
    else:
        precision_high = 0.0
        recall_high = 0.0

    true_critical = y_true >= threshold_critical
    pred_critical = y_pred >= threshold_critical

    if true_critical.sum() > 0:
        precision_critical = float(np.sum(true_critical & pred_critical) / max(pred_critical.sum(), 1))
        recall_critical = float(np.sum(true_critical & pred_critical) / true_critical.sum())
    else:
        precision_critical = 0.0
        recall_critical = 0.0

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "precision_high": round(precision_high, 4),
        "recall_high": round(recall_high, 4),
        "precision_critical": round(precision_critical, 4),
        "recall_critical": round(recall_critical, 4),
        "n_samples": len(y_true),
        "n_true_high": int(true_high.sum()),
        "n_true_critical": int(true_critical.sum()),
    }


def check_fairness(
    ward_ids: np.ndarray,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    threshold: float = 56.0,
    max_disparity: float = 0.15,
) -> dict:
    """
    Check for fairness issues in CSS predictions.
    No ward cluster should have >15% higher false-positive rate than city average.

    Returns:
        Dictionary with fairness metrics and pass/fail result
    """
    pred_positive = y_pred >= threshold
    true_positive = y_true >= threshold
    false_positives = pred_positive & ~true_positive

    if true_positive.sum() == 0 or len(y_true) == 0:
        return {"status": "insufficient_data", "passed": True}

    city_fp_rate = float(false_positives.sum() / max(len(y_true), 1))

    # Check per-ward FP rates
    unique_wards = np.unique(ward_ids)
    ward_fp_rates = {}
    violations = []

    for ward_id in unique_wards:
        mask = ward_ids == ward_id
        ward_fp = false_positives[mask]
        ward_fp_rate = float(ward_fp.sum() / max(len(ward_fp), 1))
        ward_fp_rates[str(ward_id)] = round(ward_fp_rate, 4)

        if ward_fp_rate > city_fp_rate + max_disparity:
            violations.append({
                "ward_id": str(ward_id),
                "ward_fp_rate": round(ward_fp_rate, 4),
                "city_fp_rate": round(city_fp_rate, 4),
                "disparity": round(ward_fp_rate - city_fp_rate, 4),
            })

    return {
        "passed": len(violations) == 0,
        "city_false_positive_rate": round(city_fp_rate, 4),
        "max_disparity_threshold": max_disparity,
        "violations": violations,
        "wards_checked": len(unique_wards),
    }
