#!/usr/bin/env python
"""Zip the trade ledger to a backed-up folder, keeping N days of versions (ER-08).

    python scripts/shared/backup_ledger.py --dest <folder> [--keep-days 30]

`data/history/` is gitignored, and the trade-side context in it (edge, fair
value, score, sizing) can't be rebuilt from Kalshi: `recover_trade_log.py` only
restores what the venue knows. The log was clobbered once (2026-06-03). Point
`--dest` at a folder something else backs up (a synced cloud folder).

The trade and settlement logs and the journal are read under `trade_log_lock`,
so a settle or an order write can't leave a half-written file in the zip. Every
JSON member is re-parsed from the finished zip; a source that doesn't parse is
still kept (it's the newest copy there is) but the run exits 1.

Restore steps: data/history/README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

_SHARED = Path(__file__).resolve().parent
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import paths  # noqa: E402
import trade_log  # noqa: E402
from logging_setup import setup_logging  # noqa: E402

log = setup_logging("backup_ledger")
PREFIX = "edge-radar-ledger_"


def ledger_files() -> tuple[list[Path], list[Path]]:
    """(files written under trade_log_lock, other history files)."""
    locked = [trade_log.TRADE_LOG_PATH, trade_log.SETTLEMENT_LOG_PATH, trade_log.journal_path()]
    other = [paths.DATA_DIR / "history" / "shadow_book.json"]
    return [p for p in locked if p.exists()], [p for p in other if p.exists()]


def backup(dest: Path, keep_days: float, now: float | None = None) -> tuple[Path, list[str]]:
    """Write one dated zip into `dest`, prune old ones. Returns (zip, unparseable members)."""
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = dest / f"{PREFIX}{stamp}.zip"
    tmp = out.with_suffix(".zip.tmp")  # a sync client never sees a partial zip
    locked, other = ledger_files()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        with trade_log.trade_log_lock():
            for p in locked:
                zf.write(p, p.name)
        for p in other:
            zf.write(p, p.name)
    tmp.replace(out)

    bad = []
    with zipfile.ZipFile(out) as zf:
        if zf.testzip() is not None:
            bad.append("zip CRC")
        for name in zf.namelist():
            if name.endswith(".json"):
                try:
                    json.loads(zf.read(name))
                except ValueError:
                    bad.append(name)

    cutoff = (now or time.time()) - keep_days * 86400
    for old in dest.glob(f"{PREFIX}*.zip"):
        if old != out and old.stat().st_mtime < cutoff:
            old.unlink()
            log.info("pruned %s", old.name)
    return out, bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", required=True, type=Path, help="Folder to write the zips to.")
    ap.add_argument(
        "--keep-days", type=float, default=30, help="Delete zips older than this (default 30)."
    )
    args = ap.parse_args()
    out, bad = backup(args.dest, args.keep_days)
    log.info("wrote %s (%.1f MB)", out, out.stat().st_size / 1e6)
    if bad:
        log.error("unparseable in backup: %s", ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
