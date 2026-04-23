"""
CivicPulse — Async Notification Service (API Layer)

Thin async wrapper for volunteer dispatch notifications.
Replaces the sys.path hack in routes/dispatch.py with a clean import.
Implements the same cascading fallback: WhatsApp → SMS → Manual Log.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

# ── Environment config ──
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
NOTIFICATION_PHONE = os.getenv("NOTIFICATION_PHONE", "")


async def notify_volunteer_async(
    volunteer_id: str,
    ward_name: str,
    css_score: float,
) -> dict:
    """
    Send dispatch notification to a volunteer via cascading fallback.
    Returns a dict with status and channel used.
    """
    message = _build_message(ward_name, css_score)

    # Channel 1: WhatsApp Business API
    if WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID and NOTIFICATION_PHONE:
        result = await _send_whatsapp(message)
        if result["success"]:
            return {"status": "sent", "channel": "whatsapp", "volunteer_id": volunteer_id}

    # Channel 2: Twilio SMS
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and NOTIFICATION_PHONE:
        result = await _send_sms(message)
        if result["success"]:
            return {"status": "sent", "channel": "sms", "volunteer_id": volunteer_id}

    # Channel 3: Manual log fallback
    logger.info(
        "DISPATCH_NOTIFICATION [manual_log] volunteer=%s ward=%s css=%.0f message=%s",
        volunteer_id, ward_name, css_score, message[:100],
    )
    return {"status": "logged", "channel": "manual_log", "volunteer_id": volunteer_id}


def _build_message(ward_name: str, css_score: float) -> str:
    """Build the dispatch notification message."""
    urgency = "CRITICAL" if css_score >= 76 else "HIGH" if css_score >= 56 else "ELEVATED"
    return (
        f"🚨 CivicPulse Dispatch Alert\n"
        f"Ward: {ward_name}\n"
        f"Stress Level: {css_score:.0f}/100\n"
        f"Urgency: {urgency}\n"
        f"You've been matched for a volunteer dispatch. "
        f"Please confirm your availability."
    )


async def _send_whatsapp(message: str) -> dict:
    """Send via WhatsApp Business API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": NOTIFICATION_PHONE,
                    "type": "text",
                    "text": {"body": message},
                },
            )
            resp.raise_for_status()
            return {"success": True}
    except httpx.HTTPStatusError as e:
        logger.warning("WhatsApp API error %d", e.response.status_code)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.warning("WhatsApp send failed: %s", e)
        return {"success": False, "error": str(e)}


async def _send_sms(message: str) -> dict:
    """Send via Twilio SMS API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={
                    "From": TWILIO_FROM_NUMBER,
                    "To": NOTIFICATION_PHONE,
                    "Body": message,
                },
            )
            resp.raise_for_status()
            return {"success": True}
    except httpx.HTTPStatusError as e:
        logger.warning("Twilio API error %d", e.response.status_code)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.warning("SMS send failed: %s", e)
        return {"success": False, "error": str(e)}
