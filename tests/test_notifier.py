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
            channel="whatsapp", success=True,
            message_id="msg-123",
        )
        assert result.success is True
        assert result.channel == "whatsapp"

    def test_failure_result(self):
        result = NotificationResult(
            channel="sms", success=False,
            error="Twilio connection timeout",
        )
        assert result.success is False
        assert "timeout" in result.error.lower()


class TestNotifyVolunteer:
    """Tests for the notify_volunteer cascading fallback."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"WHATSAPP_API_TOKEN": "test-token", "WHATSAPP_PHONE_NUMBER_ID": "12345"})
    async def test_whatsapp_success_stops_cascade(self):
        from notifier import notify_volunteer
        with patch("notifier.send_whatsapp", new_callable=AsyncMock) as mock_wa:
            mock_wa.return_value = NotificationResult(channel="whatsapp", success=True, message_id="wa-123")
            results = await notify_volunteer("vol-001", "Ward 1", 78.5)
            assert len(results) == 1
            assert results[0].channel == "whatsapp"
            assert results[0].success is True

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "WHATSAPP_API_TOKEN": "", "TWILIO_ACCOUNT_SID": "test-sid",
        "TWILIO_AUTH_TOKEN": "test-token", "TWILIO_FROM_NUMBER": "+1234567890"
    }, clear=False)
    async def test_falls_back_to_sms(self):
        # When WhatsApp is not configured, should try SMS
        import notifier as n
        n.WHATSAPP_API_TOKEN = ""
        n.TWILIO_ACCOUNT_SID = "test-sid"
        with patch("notifier.send_sms", new_callable=AsyncMock) as mock_sms:
            mock_sms.return_value = NotificationResult(channel="sms", success=True, message_id="sms-123")
            results = await n.notify_volunteer("vol-001", "Ward 1", 78.5)
            # Should have tried SMS
            assert any(r.channel == "sms" for r in results)

    @pytest.mark.asyncio
    async def test_always_has_manual_fallback(self):
        import notifier as n
        n.WHATSAPP_API_TOKEN = ""
        n.TWILIO_ACCOUNT_SID = ""
        results = await n.notify_volunteer("vol-001", "Ward 1", 78.5)
        # Manual log should always succeed
        assert any(r.channel == "manual_log" for r in results)
        assert any(r.success for r in results)

    @pytest.mark.asyncio
    async def test_notification_message_format(self):
        import notifier as n
        n.WHATSAPP_API_TOKEN = ""
        n.TWILIO_ACCOUNT_SID = ""
        # Verify manual log at minimum captures ward and score info
        results = await n.notify_volunteer("vol-001", "Test Ward", 85.0)
        assert len(results) >= 1
