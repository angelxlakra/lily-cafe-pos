"""Build (and optionally email) the morning digest for one day.

The API process runs this on its own once a day — see app/ask/scheduler.py —
so this script is not required in normal operation. It exists for the two
cases the loop does not cover: backfilling a day that was missed while the
server was down, and checking what the digest actually says without waiting
until 08:00.

    uv run python -m scripts.send_digest                # yesterday, IST
    uv run python -m scripts.send_digest --date 2026-09-20
    uv run python -m scripts.send_digest --force        # rebuild and re-send
    uv run python -m scripts.send_digest --dry-run      # print, store nothing

Idempotent: without --force, a day that already has a digest is left alone.
"""

import argparse
import logging
import sys
from datetime import date

from app.ask.digest import build_digest, run_for, yesterday_ist
from app.core import settings_store
from app.db.session import SessionLocal, init_db


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the morning digest for one day.")
    parser.add_argument("--date", help="IST day to build for (YYYY-MM-DD). Default: yesterday.")
    parser.add_argument("--force", action="store_true", help="Rebuild even if one exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print the digest; store nothing.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        day = date.fromisoformat(args.date) if args.date else yesterday_ist()
    except ValueError:
        print(f"Not a date: {args.date!r} (expected YYYY-MM-DD)", file=sys.stderr)
        return 2

    init_db()
    db = SessionLocal()
    try:
        settings_store.load(db)

        if args.dry_run:
            digest = build_digest(db, day)
            if digest is None:
                print(f"No trading on {day} — no digest.")
                return 0
            for sentence in digest.sentences:
                print(f"  • {sentence}")
            return 0

        row = run_for(db, day, force=args.force)
        if row is None:
            print(f"No trading on {day} — no digest.")
            return 0
        sent = "emailed" if row.email_sent_at else "not emailed"
        print(f"Digest stored for {day} ({sent}).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
