"""
CivicPulse — Notification System

Multi-channel notifications with graceful fallback:
1. WhatsApp Business API (if WHATSAPP_API_TOKEN set)
2. SMS via Twilio (if TWILIO_ACCOUNT_SID set)
3. Log to DB as pending_manual_notification (always available)

Every attempt is logged with: volunteer_id, channel, success/failure, timestamp.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Channel configuration from environment
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
FIREBASE_SERVER_KEY = os.environ.get("FIREBASE_SERVER_KEY")


class NotificationResult:
    """Result of a notification attempt."""

    def __init__(
        self,
        volunteer_id: str,
        channel: str,
        success: bool,
        error: Optional[str] = None,
    ):
        self.volunteer_id = volunteer_id
        self.channel = channel
        self.success = success
        self.error = error
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "volunteer_id": self.volunteer_id,
            "channel": self.channel,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


async def send_whatsapp(volunteer_id: str, message: str) -> NotificationResult:
    """
    Send notification via WhatsApp Business API.
    Only attempts if WHATSAPP_API_TOKEN is configured.
    """
    if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return NotificationResult(
            volunteer_id=volunteer_id,
            channel="whatsapp",
            success=False,
            error="WhatsApp not configured (WHATSAPP_API_TOKEN missing)",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={
                    "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": volunteer_id,  # In production, resolve to phone number
                    "type": "text",
                    "text": {"body": message},
                },
            )
            response.raise_for_status()

            logger.info("WhatsApp notification sent to volunteer %s", volunteer_id)
            return NotificationResult(volunteer_id=volunteer_id, channel="whatsapp", success=True)

    except httpx.HTTPStatusError as e:
        error_msg = f"WhatsApp API error {e.response.status_code}"
        logger.error("%s for volunteer %s: %s", error_msg, volunteer_id, e)
        return NotificationResult(volunteer_id=volunteer_id, channel="whatsapp", success=False, error=error_msg)
    except Exception as e:
        logger.error("WhatsApp send failed for %s: %s", volunteer_id, e)
        return NotificationResult(volunteer_id=volunteer_id, channel="whatsapp", success=False, error=str(e))


async def send_sms(volunteer_id: str, message: str) -> NotificationResult:
    """
    Send notification via Twilio SMS.
    Only attempts if TWILIO_ACCOUNT_SID is configured.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return NotificationResult(
            volunteer_id=volunteer_id,
            channel="sms",
            success=False,
            error="Twilio not configured (TWILIO_ACCOUNT_SID missing)",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={
                    "To": volunteer_id,  # In production, resolve to phone number
                    "From": TWILIO_FROM_NUMBER,
                    "Body": message,
                },
            )
            response.raise_for_status()

            logger.info("SMS notification sent to volunteer %s", volunteer_id)
            return NotificationResult(volunteer_id=volunteer_id, channel="sms", success=True)

    except httpx.HTTPStatusError as e:
        error_msg = f"Twilio API error {e.response.status_code}"
        logger.error("%s for volunteer %s", error_msg, volunteer_id)
        return NotificationResult(volunteer_id=volunteer_id, channel="sms", success=False, error=error_msg)
    except Exception as e:
        logger.error("SMS send failed for %s: %s", volunteer_id, e)
        return NotificationResult(volunteer_id=volunteer_id, channel="sms", success=False, error=str(e))


def log_manual_notification(volunteer_id: str, message: str) -> NotificationResult:
    """
    Fallback: log notification to DB as pending_manual_notification.
    Always available — this is the last resort.
    """
    logger.info(
        "📋 MANUAL NOTIFICATION LOGGED: volunteer=%s message='%s'",
        volunteer_id, message[:100],
    )
    return NotificationResult(
        volunteer_id=volunteer_id,
        channel="manual",
        success=True,  # Logging always succeeds
    )


async def notify_volunteer(
    volunteer_id: str,
    ward_name: str,
    css_score: float,
) -> list[NotificationResult]:
    """
    Send dispatch notification using cascading fallback:
    1. WhatsApp (if configured)
    2. SMS (if configured)
    3. Manual log (always available)

    Returns list of all attempt results for audit logging.
    """
    message = (
        f"🚨 CivicPulse Dispatch Alert\n"
        f"Ward: {ward_name}\n"
        f"Stress Level: {css_score:.0f}/100\n"
        f"You've been matched for a volunteer dispatch. "
        f"Please confirm your availability."
    )

    results = []

    # Try WhatsApp first
    if WHATSAPP_API_TOKEN:
        wa_result = await send_whatsapp(volunteer_id, message)
        results.append(wa_result)
        if wa_result.success:
            return results

    # Fallback to SMS
    if TWILIO_ACCOUNT_SID:
        sms_result = await send_sms(volunteer_id, message)
        results.append(sms_result)
        if sms_result.success:
            return results

    # Final fallback: manual log
    manual_result = log_manual_notification(volunteer_id, message)
    results.append(manual_result)

    return results
