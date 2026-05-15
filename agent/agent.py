# agent/agent.py
"""
Lily Cafe POS — Print Relay Agent
Runs on the Windows PC at the cafe. Polls the backend for pending print
jobs and sends them to the thermal printer.

Usage:
    python agent.py

Config via .env (copy from .env.example and fill in your values).
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Resolve paths relative to this script so they work regardless of cwd or who runs it
AGENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(AGENT_DIR))  # ensure chit_renderer is importable
load_dotenv(AGENT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(AGENT_DIR / "agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "change-me-in-production")
PAPER_SIZE = os.getenv("PAPER_SIZE", "80mm")
CAFE_OPEN_HOUR = int(os.getenv("CAFE_OPEN_HOUR", "6"))    # 6 am
CAFE_CLOSE_HOUR = int(os.getenv("CAFE_CLOSE_HOUR", "16")) # 4 pm

HEADERS = {"X-Agent-Key": AGENT_API_KEY}

PRINTER_CFG = {
    "type":     os.getenv("PRINTER_TYPE", "usb"),
    "vendor_id":  os.getenv("PRINTER_VENDOR_ID", ""),
    "product_id": os.getenv("PRINTER_PRODUCT_ID", ""),
    "port":     os.getenv("PRINTER_PORT", "COM1"),
    "baudrate": os.getenv("PRINTER_BAUDRATE", "9600"),
    "host":     os.getenv("PRINTER_HOST", ""),
    "name":     os.getenv("PRINTER_NAME", ""),
    "port_num": os.getenv("PRINTER_NETWORK_PORT", "9100"),
}


def is_cafe_hours() -> bool:
    hour = datetime.now().hour
    return CAFE_OPEN_HOUR <= hour < CAFE_CLOSE_HOUR


def poll_interval() -> float:
    """1 second during cafe hours → <1s average latency. 30s overnight."""
    return 1.0 if is_cafe_hours() else 30.0


def fetch_next_job() -> dict | None:
    try:
        r = requests.get(
            f"{BACKEND_URL}/api/v1/print-jobs/next",
            headers=HEADERS,
            timeout=5,
        )
        r.raise_for_status()
        return r.json()  # None when queue is empty
    except requests.exceptions.ConnectionError:
        logger.warning("Cannot reach backend — will retry")
        return None
    except Exception as e:
        logger.error(f"Error fetching job: {e}")
        return None


def ack_job(job_id: int, success: bool, error: str | None = None) -> None:
    try:
        body: dict = {"success": success}
        if error:
            body["error"] = error
        requests.put(
            f"{BACKEND_URL}/api/v1/print-jobs/{job_id}/ack",
            headers=HEADERS,
            json=body,
            timeout=5,
        )
    except Exception as e:
        logger.error(f"Error acking job {job_id}: {e}")


def run() -> None:
    from chit_renderer import print_chit

    logger.info(f"Print agent started — backend: {BACKEND_URL}")
    logger.info(f"Cafe hours {CAFE_OPEN_HOUR:02d}:00–{CAFE_CLOSE_HOUR:02d}:00 → 1 s poll")
    logger.info(f"Outside hours → 30 s poll")

    while True:
        job = fetch_next_job()

        if job:
            job_id = job["id"]
            payload = job["payload"]
            station = job.get("station", "kitchen")
            logger.info(f"Job {job_id}: table {payload.get('table_number')} [{station}]")

            error_msg = None
            try:
                success = print_chit(payload, PRINTER_CFG, PAPER_SIZE)
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"Print exception: {e}")

            ack_job(job_id, success, error_msg)
            # Immediately poll again — more jobs may be waiting
            continue

        time.sleep(poll_interval())


if __name__ == "__main__":
    run()
