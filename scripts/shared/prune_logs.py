#!/usr/bin/env python
"""Keep logs/ bounded: drop dated logs past N days, trim fixed-name logs (ER-28).

    python scripts/shared/prune_logs.py [--keep-days 90] [--max-mb 5]

Two kinds of file live in logs/. Scripts write `<name>_<YYYY-MM-DD>.log` through
logging_setup; those are deleted once the date in the name is older than
--keep-days. The scheduled wrappers append to fixed names (`clv_capture.log`,
`shadow_book.log`, `scan_same_day.log`, ...); one over --max-mb keeps its newest
fifth, cut at a line break, so the last run the email step reads survives.
Reconcile runs it nightly.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

_SHARED = Path(__file__).resolve().parent
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import paths  # noqa: E402,F401  (puts the repo root on sys.path for app.config)
from logging_setup import LOG_DIR, setup_logging  # noqa: E402

log = setup_logging("prune_logs")
DATED = re.compile(r"_(\d{4}-\d{2}-\d{2})\.log$")


def prune(
    log_dir: Path, keep_days: int = 90, max_mb: float = 5, today: date | None = None
) -> tuple[int, int]:
    """Return (deleted, trimmed). A file another process holds open is skipped."""
    cutoff = (today or date.today()) - timedelta(days=keep_days)
    cap = int(max_mb * 1024 * 1024)
    deleted = trimmed = 0
    for f in sorted(log_dir.glob("*.log")):
        try:
            m = DATED.search(f.name)
            if m:
                if date.fromisoformat(m.group(1)) < cutoff:
                    f.unlink()
                    deleted += 1
            elif f.stat().st_size > cap:
                tail = f.read_bytes()[-cap // 5 :]
                f.write_bytes(tail[tail.find(b"\n") + 1 :])
                trimmed += 1
        except (OSError, ValueError) as e:
            log.warning("skipped %s: %s", f.name, e)
    return deleted, trimmed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keep-days", type=int, default=90)
    ap.add_argument("--max-mb", type=float, default=5)
    a = ap.parse_args()
    deleted, trimmed = prune(LOG_DIR, a.keep_days, a.max_mb)
    log.info(
        "prune_logs: deleted %d dated logs older than %d days, trimmed %d",
        deleted,
        a.keep_days,
        trimmed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
