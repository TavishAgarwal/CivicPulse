"""
CivicPulse — CSS Threshold Logic

All thresholds loaded from environment variables — never hardcoded.
This module is the single source of truth for dispatch decisions.
"""

import os
import logging

logger = logging.getLogger(__name__)

# All thresholds from environment — never hardcoded
CSS_STABLE_MAX = int(os.environ.get("CSS_STABLE_MAX", "30"))
CSS_ELEVATED_MAX = int(os.environ.get("CSS_ELEVATED_MAX", "55"))
CSS_HIGH_THRESHOLD = int(os.environ.get("CSS_HIGH_THRESHOLD", "56"))
CSS_CRITICAL_THRESHOLD = int(os.environ.get("CSS_CRITICAL_THRESHOLD", "76"))
FEATURE_AUTO_DISPATCH = os.environ.get("FEATURE_AUTO_DISPATCH", "false").lower() == "true"


def get_status_label(css_score: float) -> str:
    """Map CSS score to status label."""
    if css_score >= CSS_CRITICAL_THRESHOLD:
        return "critical"
    elif css_score >= CSS_HIGH_THRESHOLD:
        return "high"
    elif css_score > CSS_STABLE_MAX:
        return "elevated"
    else:
        return "stable"


def requires_dispatch(css_score: float) -> bool:
    """Check if a CSS score requires dispatch action."""
    return css_score >= CSS_HIGH_THRESHOLD


def requires_human_approval(css_score: float) -> bool:
    """
    Check if dispatch requires human approval.
    CSS 56-75: always requires human approval
    CSS >= 76: auto-dispatch ONLY if FEATURE_AUTO_DISPATCH=true
    """
    if css_score < CSS_HIGH_THRESHOLD:
        return False  # No dispatch needed

    if css_score >= CSS_CRITICAL_THRESHOLD:
        if FEATURE_AUTO_DISPATCH:
            return False  # Auto-dispatch enabled for critical
        else:
            logger.warning(
                "CSS %.1f is critical but FEATURE_AUTO_DISPATCH is disabled — "
                "requiring human approval",
                css_score,
            )
            return True  # Default to requiring approval when flag is missing/false

    # CSS 56-75: always requires human approval
    return True


def can_auto_dispatch(css_score: float) -> bool:
    """
    Check if auto-dispatch is allowed for this CSS score.
    Only allowed when:
    1. CSS >= CSS_CRITICAL_THRESHOLD (76)
    2. FEATURE_AUTO_DISPATCH is explicitly set to true in env
    """
    if not FEATURE_AUTO_DISPATCH:
        return False

    if css_score < CSS_CRITICAL_THRESHOLD:
        return False

    return True


def get_threshold_config() -> dict:
    """Return current threshold configuration for display/API."""
    return {
        "stable_max": CSS_STABLE_MAX,
        "elevated_max": CSS_ELEVATED_MAX,
        "high_threshold": CSS_HIGH_THRESHOLD,
        "critical_threshold": CSS_CRITICAL_THRESHOLD,
        "auto_dispatch_enabled": FEATURE_AUTO_DISPATCH,
        "thresholds": [
            {"range": f"0-{CSS_STABLE_MAX}", "label": "stable", "action": "Monitor only"},
            {"range": f"{CSS_STABLE_MAX + 1}-{CSS_ELEVATED_MAX}", "label": "elevated", "action": "Alert NGO coordinator"},
            {"range": f"{CSS_HIGH_THRESHOLD}-{CSS_CRITICAL_THRESHOLD - 1}", "label": "high", "action": "Suggest dispatch (human approval)"},
            {"range": f"{CSS_CRITICAL_THRESHOLD}-100", "label": "critical",
             "action": "Auto-dispatch" if FEATURE_AUTO_DISPATCH else "Dispatch (human approval — auto-dispatch disabled)"},
        ],
    }
