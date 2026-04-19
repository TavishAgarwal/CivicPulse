"""
CivicPulse — Threshold Logic Unit Tests

Tests the CSS threshold and dispatch decision logic.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "dispatch"))

# Set env vars BEFORE importing thresholds
os.environ["CSS_STABLE_MAX"] = "30"
os.environ["CSS_ELEVATED_MAX"] = "55"
os.environ["CSS_HIGH_THRESHOLD"] = "56"
os.environ["CSS_CRITICAL_THRESHOLD"] = "76"
os.environ["FEATURE_AUTO_DISPATCH"] = "false"

from thresholds import (
    get_status_label,
    requires_dispatch,
    requires_human_approval,
    can_auto_dispatch,
    get_threshold_config,
)


class TestStatusLabels:
    def test_stable(self):
        assert get_status_label(0) == "stable"
        assert get_status_label(25) == "stable"
        assert get_status_label(30) == "stable"

    def test_elevated(self):
        assert get_status_label(31) == "elevated"
        assert get_status_label(45) == "elevated"
        assert get_status_label(55) == "elevated"

    def test_high(self):
        assert get_status_label(56) == "high"
        assert get_status_label(70) == "high"
        assert get_status_label(75) == "high"

    def test_critical(self):
        assert get_status_label(76) == "critical"
        assert get_status_label(90) == "critical"
        assert get_status_label(100) == "critical"


class TestDispatchDecisions:
    def test_stable_no_dispatch(self):
        assert requires_dispatch(25) is False

    def test_elevated_no_dispatch(self):
        assert requires_dispatch(45) is False

    def test_high_requires_dispatch(self):
        assert requires_dispatch(60) is True

    def test_critical_requires_dispatch(self):
        assert requires_dispatch(80) is True


class TestHumanApproval:
    def test_below_threshold_no_approval(self):
        assert requires_human_approval(30) is False

    def test_high_requires_approval(self):
        assert requires_human_approval(60) is True

    def test_critical_requires_approval_when_auto_disabled(self):
        # FEATURE_AUTO_DISPATCH is set to false above
        assert requires_human_approval(80) is True


class TestAutoDispatch:
    def test_auto_dispatch_disabled_by_default(self):
        assert can_auto_dispatch(80) is False

    def test_below_critical_never_auto(self):
        assert can_auto_dispatch(60) is False
        assert can_auto_dispatch(30) is False


class TestThresholdConfig:
    def test_config_returns_all_thresholds(self):
        config = get_threshold_config()
        assert config["stable_max"] == 30
        assert config["elevated_max"] == 55
        assert config["high_threshold"] == 56
        assert config["critical_threshold"] == 76
        assert config["auto_dispatch_enabled"] is False
        assert len(config["thresholds"]) == 4
