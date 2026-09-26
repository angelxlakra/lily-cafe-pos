"""The daily digest trigger, running inside the API process.

The backend is already a permanently-running process — `fly.toml` pins
`auto_stop_machines = false` and `min_machines_running = 1` so the cafe gets
an instant response at 6am — which means a daily job needs no scheduler
library, no second machine and no external caller. It needs a sleep.

Keeping the trigger in-process also keeps the clock here: `digest.send_at`
is an IST wall-clock time, resolved against IST below, regardless of the
machine's timezone.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, time, timedelta

from starlette.concurrency import run_in_threadpool

from app.ask.digest import run_for, yesterday_ist
from app.ask.periods import IST
from app.core import settings_store

logger = logging.getLogger(__name__)

DEFAULT_SEND_AT = "08:00"


def parse_send_at(raw: str) -> time:
    """"HH:MM" → time, falling back to 08:00 rather than killing the loop."""
    try:
        hour, minute = (int(part) for part in raw.strip().split(":", 1))
        return time(hour=hour, minute=minute)
    except (ValueError, AttributeError):
        logger.warning("Invalid digest.send_at %r — using %s", raw, DEFAULT_SEND_AT)
        hour, minute = (int(p) for p in DEFAULT_SEND_AT.split(":"))
        return time(hour=hour, minute=minute)


def seconds_until(send_at: time, now: datetime) -> float:
    """Seconds from `now` to the next occurrence of `send_at`, in IST."""
    target = now.replace(
        hour=send_at.hour, minute=send_at.minute, second=0, microsecond=0
    )
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_once(day: date) -> None:
    """Open a session, run the digest, always close. Runs in a worker thread."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        row = run_for(db, day)
        if row is None:
            logger.info("Digest skipped for %s (no trading)", day)
        else:
            logger.info("Digest ready for %s", day)
    finally:
        db.close()


def _should_catch_up(send_at: time, now: datetime) -> bool:
    """True when today's send time has already passed, so a restart at 10am
    still produces the morning's digest instead of skipping the day."""
    return now.time() >= send_at


async def digest_loop() -> None:
    """Run the digest once a day at `digest.send_at`, forever."""
    now = datetime.now(IST)
    if _should_catch_up(parse_send_at(settings_store.get("digest.send_at", DEFAULT_SEND_AT)), now):
        await _tick(catch_up=True)

    while True:
        send_at = parse_send_at(settings_store.get("digest.send_at", DEFAULT_SEND_AT))
        delay = seconds_until(send_at, datetime.now(IST))
        logger.info("Next digest in %.0f minutes", delay / 60)
        await asyncio.sleep(delay)
        await _tick()


async def _tick(catch_up: bool = False) -> None:
    """One digest attempt. Never raises — a bad day must not end the loop."""
    if not settings_store.get_bool("digest.enabled", True):
        logger.info("Digest disabled — skipping")
        return
    try:
        # run_for is idempotent on its unique date, so a catch-up on every
        # restart costs one lookup and cannot re-send an email.
        await run_in_threadpool(_run_once, yesterday_ist())
    except Exception:
        logger.exception("Digest run failed%s", " (catch-up)" if catch_up else "")


def start(app) -> asyncio.Task | None:
    """Start the loop as a background task, unless disabled at boot."""
    if not settings_store.get_bool("digest.enabled", True):
        logger.info("Digest disabled at startup — scheduler not started")
        return None
    task = asyncio.create_task(digest_loop(), name="digest-loop")
    logger.info("Digest scheduler started")
    return task
