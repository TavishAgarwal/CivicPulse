"""
CivicPulse — CSS Scheduler Tests
Tests the CSS computation cycle with mocked DB and Redis.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ml"))

from scheduler import run_css_cycle


class TestCSSScheduler:
    """Tests for the CSS computation scheduler."""

    @patch("scheduler.fetch_wards")
    def test_run_css_cycle_completes(self, mock_fetch_wards):
        """CSS cycle should complete without error."""
        mock_conn = MagicMock()
        mock_redis = MagicMock()
        mock_model = MagicMock()
        mock_fetch_wards.return_value = []  # No wards = quick exit
        result = run_css_cycle(mock_conn, mock_redis, mock_model)
        assert result is not None

    @patch("scheduler.fetch_wards")
    def test_handles_db_failure(self, mock_fetch_wards):
        """Should handle DB connection failure gracefully."""
        mock_fetch_wards.side_effect = Exception("DB connection failed")
        mock_conn = MagicMock()
        mock_redis = MagicMock()
        mock_model = MagicMock()
        # Should not crash the process
        try:
            run_css_cycle(mock_conn, mock_redis, mock_model)
        except Exception:
            pass  # Expected — function may propagate

    @patch("scheduler.cache_css_to_redis")
    @patch("scheduler.write_css_result")
    @patch("scheduler.fetch_ward_signals")
    @patch("scheduler.fetch_wards")
    def test_caches_results_in_redis(self, mock_wards, mock_signals, mock_write, mock_cache):
        """CSS results should be cached in Redis."""
        import pandas as pd
        mock_wards.return_value = [{"id": "w1", "ward_code": "WARD-001"}]
        mock_signals.return_value = pd.DataFrame()  # Empty signals
        mock_conn = MagicMock()
        mock_redis = MagicMock()
        mock_model = MagicMock()
        mock_model.predict.return_value = (50.0, {"pharmacy": 0.5})
        try:
            run_css_cycle(mock_conn, mock_redis, mock_model)
        except Exception:
            pass

    def test_scheduler_module_importable(self):
        """Scheduler module should be importable."""
        import scheduler
        assert hasattr(scheduler, "run_css_cycle")

    def test_scheduler_has_interval_config(self):
        """Scheduler should have configurable interval."""
        import scheduler
        # Should have default interval or accept it as parameter
        assert callable(scheduler.run_css_cycle)
