#!/usr/bin/env python3
"""
Pre-fetch on-this-day JSON caches for cron / manual warm-up.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault("WIKIDATA_TEST_MODE", "false")

from app import app  # noqa: E402
import today as tl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Warm on-this-day JSON caches via the Wikidata entity API.")
    parser.add_argument("--today", action="store_true", help="Use today's month/day")
    parser.add_argument("--month", type=int, help="Month 1-12")
    parser.add_argument("--day", type=int, help="Day 1-31")
    parser.add_argument("--locales", nargs="+", default=["en"], help="Locale list")
    parser.add_argument("--force", action="store_true", help="Ignore TTL and refresh")
    args = parser.parse_args()

    if args.today:
        d = dt.date.today()
        month, day = d.month, d.day
    elif args.month is not None and args.day is not None:
        month, day = args.month, args.day
        dt.date(2024, month, day)
    else:
        parser.error("Provide --today or both --month and --day")

    cache_root = os.path.join(app.root_path, "cache", "today")
    ua = app.config.get("USER_AGENT", "")

    with app.app_context():
        for loc in args.locales:
            tl.get_literature_today(
                month,
                day,
                loc,
                ua,
                cache_root,
                allow_remote_fetch=True,
                force_refresh=args.force,
            )
            print(f"Warmed {month:02d}-{day:02d} ({loc}) -> {cache_root}")


if __name__ == "__main__":
    main()
