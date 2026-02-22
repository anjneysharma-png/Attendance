"""
Send message to CEO's WhatsApp via Twilio.
"""
import os
import logging
from twilio.rest import Client

from .format_message import split_message

logger = logging.getLogger(__name__)


def _get_twilio_config() -> tuple[str, str, str, str]:
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    from_num = os.environ.get("TWILIO_WHATSAPP_FROM", "").strip()
    to_num = os.environ.get("CEO_WHATSAPP_TO", "").strip()
    if not sid or not token or not from_num or not to_num:
        raise ValueError(
            "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, "
            "and CEO_WHATSAPP_TO must be set"
        )
    # Ensure whatsapp: prefix for Twilio
    if not from_num.startswith("whatsapp:"):
        from_num = f"whatsapp:{from_num}"
    if not to_num.startswith("whatsapp:"):
        to_num = f"whatsapp:{to_num}"
    return sid, token, from_num, to_num


def send_whatsapp(message: str) -> bool:
    """
    Send message to CEO via Twilio WhatsApp. Splits into multiple messages if needed.
    Returns True if sent successfully.
    """
    sid, token, from_num, to_num = _get_twilio_config()
    client = Client(sid, token)
    chunks = split_message(message)
    for i, chunk in enumerate(chunks):
        client.messages.create(
            body=chunk,
            from_=from_num,
            to=to_num,
        )
        logger.info("Sent WhatsApp chunk %d/%d to %s", i + 1, len(chunks), to_num)
    return True
