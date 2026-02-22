"""
Daily job: fetch absent list from etimeoffice -> format -> send to CEO via Twilio WhatsApp.
Exit 0 on success, 1 on failure (for GitHub Actions).
"""
import logging
import os
import sys

# Allow running as script: python src/run_daily.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.fetch_absent_list import fetch_absent_list
from src.format_message import format_message
from src.send_whatsapp import send_whatsapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Retry once on fetch failure
MAX_FETCH_RETRIES = 2


def run() -> int:
    """Fetch -> format -> send. Returns 0 on success, 1 on failure."""
    headless = os.environ.get("HEADLESS", "true").lower() in ("1", "true", "yes")

    for attempt in range(1, MAX_FETCH_RETRIES + 1):
        try:
            rows = fetch_absent_list(headless=headless)
            break
        except Exception as e:
            logger.warning("Fetch attempt %d failed: %s", attempt, e)
            if attempt == MAX_FETCH_RETRIES:
                try:
                    send_whatsapp("Absent list could not be fetched today. Please check etimeoffice.")
                except Exception as send_err:
                    logger.error("Failed to send failure notification: %s", send_err)
                return 1
            continue

    message = format_message(rows)
    try:
        send_whatsapp(message)
    except Exception as e:
        logger.exception("Failed to send WhatsApp: %s", e)
        return 1

    logger.info("Daily absentee report sent successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
