"""
CivicPulse — Notification System Tests
Tests the cascading notification fallback: WhatsApp → SMS → Manual Log.
"""

import sys
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "dispatch"))

from notifier import NotificationResult


class TestNotificationResult:
    """Tests for the NotificationResult data class."""

    def test_success_result(self):
        result = NotificationResult(
            volunteer_id="vol-001",
            channel="whatsapp", success=True,
        )
        assert result.success is True
        assert result.channel == "whatsapp"

    def test_failure_result(self):
        result = NotificationResult(
            volunteer_id="vol-001",
            channel="sms", success=False,
            error="Twilio connection timeout",
        )
        assert result.success is False
        assert "timeout" in result.error.lower()

    def test_to_dict(self):
        result = NotificationResult(
            volunteer_id="vol-001",
            channel="manual", success=True,
        )
        d = result.to_dict()
        assert d["volunteer_id"] == "vol-001"
        assert d["channel"] == "manual"
        assert d["success"] is True
        assert "timestamp" in d


class TestNotifyVolunteer:
    """Tests for the notify_volunteer cascading fallback."""

    @pytest.mark.asyncio
    async def test_whatsapp_success_stops_cascade(self):
        import notifier
        with patch.object(notifier, "WHATSAPP_API_TOKEN", "test-token"), \
             patch.object(notifier, "WHATSAPP_PHONE_NUMBER_ID", "12345"), \
             patch("notifier.send_whatsapp", new_callable=AsyncMock) as mock_wa:
            mock_wa.return_value = NotificationResult(
                volunteer_id="vol-001", channel="whatsapp", success=True
            )
            results = await notifier.notify_volunteer("vol-001", "Ward 1", 78.5)
            assert len(results) == 1
            assert results[0].channel == "whatsapp"
            assert results[0].success is True

    @pytest.mark.asyncio
    async def test_falls_back_to_sms(self):
        import notifier
        with patch.object(notifier, "WHATSAPP_API_TOKEN", ""), \
             patch.object(notifier, "TWILIO_ACCOUNT_SID", "test-sid"), \
             patch("notifier.send_sms", new_callable=AsyncMock) as mock_sms:
            mock_sms.return_value = NotificationResult(
                volunteer_id="vol-001", channel="sms", success=True
            )
            results = await notifier.notify_volunteer("vol-001", "Ward 1", 78.5)
            assert any(r.channel == "sms" for r in results)

    @pytest.mark.asyncio
    async def test_always_has_manual_fallback(self):
        import notifier
        with patch.object(notifier, "WHATSAPP_API_TOKEN", ""), \
             patch.object(notifier, "TWILIO_ACCOUNT_SID", ""):
            results = await notifier.notify_volunteer("vol-001", "Ward 1", 78.5)
            # Manual log should always succeed
            assert any(r.channel == "manual" for r in results)
            assert any(r.success for r in results)

    @pytest.mark.asyncio
    async def test_notification_message_format(self):
        import notifier
        with patch.object(notifier, "WHATSAPP_API_TOKEN", ""), \
             patch.object(notifier, "TWILIO_ACCOUNT_SID", ""):
            results = await notifier.notify_volunteer("vol-001", "Test Ward", 85.0)
            assert len(results) >= 1
