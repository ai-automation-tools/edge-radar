"""
trade_log.py
Centralized trade log and settlement log I/O.

Single source of truth for loading, saving, and querying trade history.
Used by kalshi_executor.py, kalshi_settler.py, and future prediction executor.
"""

import json
import logging
import os
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from paths import TRADE_LOG_PATH, SETTLEMENT_LOG_PATH

log = logging.getLogger("trade_log")

# ── Cross-process lock (M2) ───────────────────────────────────────────────────
#
# `_atomic_write_json` prevents corruption from an interrupted write, but not a
# *lost update* when two processes both do load→mutate→save: the second save
# clobbers the first's change. For the trade log a lost append = an untracked
# live position, so every writer that mutates the log must hold this lock across
# its read-modify-write cycle, re-reading fresh *inside* the lock.
#
# One lock file guards BOTH logs (the settler mutates them together). We use the
# `filelock` library when present (robust cross-platform advisory lock); if it's
# somehow unavailable we degrade to a no-op so a missing dependency can never
# block a live trade write — the atomic-write guarantee still holds, only the
# lost-update protection is lost, and that's logged once.
_LOCK_TIMEOUT_SECONDS = 30.0

try:
    from filelock import FileLock, Timeout as _FileLockTimeout

    _HAVE_FILELOCK = True
except ImportError:  # pragma: no cover - defensive fallback
    _HAVE_FILELOCK = False
    _warned_no_filelock = False


def _lock_path() -> Path:
    """Lock file path, derived from the current ``TRADE_LOG_PATH`` at call time
    so it follows a monkeypatched log location in tests."""
    return TRADE_LOG_PATH.parent / ".trade_log.lock"


@contextmanager
def trade_log_lock(timeout: float = _LOCK_TIMEOUT_SECONDS):
    """Hold a cross-process lock guarding the trade + settlement logs.

    Wrap any load→mutate→save cycle in this and re-read the log *inside* the
    ``with`` block, so a concurrent writer's changes are merged rather than
    clobbered. On lock-acquire timeout the write still proceeds (falling back to
    atomic-write-only semantics) rather than dropping a trade — a blocked write
    is worse than a rare lost-update, and it's logged.
    """
    if not _HAVE_FILELOCK:
        global _warned_no_filelock
        if not _warned_no_filelock:
            log.warning(
                "filelock not installed — trade-log writes fall back to "
                "atomic-write-only (no cross-process lost-update protection)."
            )
            _warned_no_filelock = True
        yield
        return

    lock_path = _lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path), timeout=timeout)
    try:
        lock.acquire()
    except _FileLockTimeout:
        log.warning(
            "trade_log_lock: timed out after %ss waiting for %s; proceeding "
            "without the lock (atomic write only).",
            timeout,
            lock_path,
        )
        yield
        return
    try:
        yield
    finally:
        lock.release()


def _atomic_write_json(path: Path, data) -> None:
    """Serialize ``data`` to ``path`` atomically.

    Writes to a temp file in the same directory, flushes+fsyncs it, then
    ``os.replace``s it over the target. ``os.replace`` is atomic on both POSIX
    and Windows when source and destination share a filesystem, so a reader
    (or a crash) never observes a half-written trade/settlement log — the file
    is either the old contents or the complete new contents.

    NOTE: this closes the *corruption-on-interrupted-write* hole. Serializing
    concurrent read-modify-write cycles across processes is a separate concern
    handled by ``trade_log_lock`` (M2) — hold that lock and re-read inside it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        # Never leave a stray temp file behind on failure.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def load_trade_log() -> list[dict]:
    """Load the trade log from disk."""
    if TRADE_LOG_PATH.exists():
        with open(TRADE_LOG_PATH) as f:
            return json.load(f)
    return []


def save_trade_log(trades: list[dict]) -> None:
    """Save the trade log to disk (atomic write — see ``_atomic_write_json``).

    This overwrites the whole file. To append without clobbering a concurrent
    writer's records, use ``append_trades`` (which re-reads under the lock).
    """
    _atomic_write_json(TRADE_LOG_PATH, trades)


def append_trades(records: list[dict]) -> list[dict]:
    """Append ``records`` to the trade log without losing concurrent writes.

    Acquires the cross-process lock, re-reads the current log from disk, extends
    it with ``records``, and saves atomically — so a trade written by another
    process between our caller's load and this call is preserved instead of
    clobbered. Returns the full, freshly-persisted log.
    """
    if not records:
        return load_trade_log()
    with trade_log_lock():
        trades = load_trade_log()
        trades.extend(records)
        save_trade_log(trades)
        return trades


def persist_trade(record: dict, attempts: int = 8, delay: float = 0.1) -> bool:
    """Append one accepted order to the log, retrying, then journaling (BUG-03).

    On Windows `os.replace` onto a file another process holds open raises
    `PermissionError`, and CLV-Capture reads the log every 5 minutes. A venue-
    accepted order must never be lost to that, so retry with backoff (~3 s in
    all), then append it to the JSONL journal, which `recover_journal` merges
    back on the next settle. Returns False when it had to journal.
    """
    for attempt in range(1, attempts + 1):
        try:
            append_trades([record])
            return True
        except OSError as e:
            last = e
            time.sleep(delay * attempt)
    log.error(
        "Trade log write failed %d times (%s); journaling accepted order %s to %s",
        attempts,
        last,
        record.get("order_id"),
        journal_path(),
    )
    journal_trade(record)
    return False


def journal_path() -> Path:
    return TRADE_LOG_PATH.parent / "trade_journal.jsonl"


def journal_trade(record: dict) -> None:
    """Last-resort append-only record of an accepted order the log couldn't take."""
    path = journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def recover_journal() -> int:
    """Merge journaled trades into the log (by `trade_id`); return how many were added.

    The journal is removed only after the log is saved. A line that doesn't parse
    (a crash mid-write) is kept in the journal for a human to look at.
    """
    path = journal_path()
    if not path.exists():
        return 0
    with trade_log_lock():
        records, bad = [], []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                bad.append(line)
        trades = load_trade_log()
        have = {t.get("trade_id") for t in trades}
        new = [r for r in records if r.get("trade_id") not in have]
        if new:
            trades.extend(new)
            save_trade_log(trades)
        if bad:
            path.write_text("\n".join(bad) + "\n", encoding="utf-8")
            log.error("trade journal: %d unparseable line(s) left in %s", len(bad), path)
        else:
            path.unlink()
    if new:
        log.warning("Recovered %d journaled trade(s) into the trade log", len(new))
    return len(new)


def set_row_fills(trade: dict, fill: float, remaining: float) -> bool:
    """Bring a row's fill fields up to the venue's count; True if anything changed.

    One rule for the settler's pre-settle refresh (BUG-01) and the janitors'
    cancel write-back (BUG-02). Never lowers a recorded fill. Cost uses
    `market_price_at_entry`, the same convention as `log_trade`.
    """
    fill = max(float(fill), get_filled_contracts(trade))
    remaining = max(float(remaining), 0.0)
    requested = float(trade.get("requested_contracts") or 0)
    if fill > 0:
        status = "partial" if remaining > 0 or (requested and fill < requested) else "filled"
    else:
        status = trade.get("fill_status") or "resting"
    cost = round(fill * float(trade.get("market_price_at_entry") or 0), 4)
    new = {
        "filled_contracts": fill,
        "contracts": fill,
        "fill_count": fill,
        "filled_cost": cost,
        "cost_dollars": cost,
        "remaining_count": remaining,
        "fill_status": status,
    }
    changed = any(trade.get(k) != v for k, v in new.items())
    trade.update(new)
    return changed


def mark_cancelled(venue_fills: dict[str, float] | set[str], now: datetime | None = None) -> int:
    """Write venue cancels back to the log; return how many rows were closed.

    ``venue_fills`` maps order_id -> contracts the venue had filled when the
    order was cancelled (a bare set means 0 for each). A zero-fill row is closed
    as cancelled at $0. A row with any fill stays open with the venue's count
    (BUG-02): the filled part is real exposure the settler settles; only the
    unfilled remainder was cancelled. Deciding from the log's own count was the
    bug, because the log isn't updated after a late fill.
    """
    if not venue_fills:
        return 0
    if not isinstance(venue_fills, dict):
        venue_fills = {oid: 0.0 for oid in venue_fills}
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    n = 0
    changed = False
    with trade_log_lock():
        trades = load_trade_log()
        for t in trades:
            oid = t.get("order_id")
            if oid not in venue_fills or t.get("closed_at"):
                continue
            if venue_fills[oid] > 0 or t.get("filled_contracts") or t.get("fill_count"):
                changed |= set_row_fills(t, venue_fills[oid], 0)
                if t["fill_status"] != "partial":  # a remainder was cancelled: never fully filled
                    t["fill_status"] = "partial"
                    changed = True
                continue
            t.update(fill_status="cancelled", closed_at=stamp, net_pnl=0, remaining_count=0)
            n += 1
        if n or changed:
            save_trade_log(trades)
    return n


def load_settlement_log() -> list[dict]:
    """Load the settlement log from disk."""
    if SETTLEMENT_LOG_PATH.exists():
        with open(SETTLEMENT_LOG_PATH) as f:
            return json.load(f)
    return []


def save_settlement_log(settlements: list[dict]) -> None:
    """Save the settlement log to disk (atomic write — see ``_atomic_write_json``)."""
    _atomic_write_json(SETTLEMENT_LOG_PATH, settlements)


def for_profile(trades: list[dict], profile: str | None = None) -> list[dict]:
    """Rows belonging to one strategy profile (P1).

    The trade log is shared across profiles, so any gate that reads *history*
    rather than the venue has to be scoped or it measures the wrong book. Two
    gates do: **Gate 1** (daily loss limit, via `get_today_pnl`) and **Gate 7**
    (series dedup, via `recent_matchups_from_log`). Gates 5 and 6 read live
    venue positions, which Kalshi already scopes by subaccount, so they need
    nothing.

    Getting this wrong is not cosmetic: unscoped, a bad day on `main` halts
    `longshot` and vice versa, and a matchup one profile bet blocks the other
    from betting it -- across two genuinely separate wallets. The forked repo
    this replaced had the mirror-image bug, and its own ROADMAP named it: with
    a trade log each, "each repo's own MAX_DAILY_LOSS/exposure gates only see
    their own activity, not the combined draw-down." One log plus this filter
    is what makes each profile see exactly its own.

    Rows written before P1 have no `profile` key and are all `main`'s.

    Settlement and reporting deliberately do NOT call this -- they want the
    whole book, split by profile where it matters.
    """
    if profile is None:
        from app.config import get_config

        profile = get_config().system.profile
    return [t for t in trades if t.get("profile", "main") == profile]


def get_today_pnl(trades: list[dict] | None = None) -> float:
    """Calculate today's realized P&L from the trade log."""
    if trades is None:
        trades = load_trade_log()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return sum(t.get("net_pnl", 0) for t in trades if (t.get("closed_at") or "").startswith(today))


def get_filled_contracts(trade: dict) -> float:
    """Return the number of contracts actually filled for a trade record.

    Handles both old format (only ``contracts`` + ``fill_count``) and the new
    format (explicit ``filled_contracts`` field).  For old records that lack
    ``filled_contracts``, falls back to ``fill_count`` (from the Kalshi API
    response) then ``contracts`` (legacy requested value).
    """
    if trade.get("filled_contracts") is not None:  # ER-43: a null field falls through
        return float(trade["filled_contracts"])
    fc = trade.get("fill_count")
    if fc is not None and str(fc) not in ("", "0"):
        return float(fc)
    # Legacy fallback: assume fully filled (pre-X5 records)
    return float(trade.get("contracts") or 0)


def get_filled_cost(trade: dict) -> float:
    """Return the dollar cost of contracts actually filled.

    Uses ``filled_cost`` when present (new format).  For old records, derives
    cost from ``fill_count * market_price_at_entry`` if available, otherwise
    falls back to ``cost_dollars`` (legacy requested value).
    """
    if trade.get("filled_cost") is not None:  # ER-43: a null field falls through
        return float(trade["filled_cost"])
    fc = trade.get("fill_count")
    price = trade.get("market_price_at_entry", 0)
    if fc is not None and str(fc) not in ("", "0") and price:
        return round(float(fc) * float(price), 4)
    # Legacy fallback
    return float(trade.get("cost_dollars") or 0)


def settlement_revenue_dollars(raw) -> float:
    """Normalize a Kalshi settlement ``revenue`` field to dollars.

    Kalshi returns ``revenue`` as an integer number of **cents**, so any int is
    divided by 100. A non-int (already a float dollar value in some records) is
    passed through unchanged. Single source of truth so the settler report and
    ``risk_check`` agree — they previously disagreed on the 1-cent case (review
    #9: one used a ``> 1`` guard that mis-read 1¢ as $1.00).

    ER-43: None (or "") is $0, and a digits-only string is cents like an int,
    so ``"56"`` is $0.56, not $56. A string with a decimal point is dollars.
    """
    if raw is None or raw == "":
        return 0.0
    if isinstance(raw, int) or (isinstance(raw, str) and raw.strip().lstrip("-").isdigit()):
        return int(raw) / 100
    return float(raw)


def get_open_trade_count(trades: list[dict] | None = None) -> int:
    """Count trades that haven't been settled yet."""
    if trades is None:
        trades = load_trade_log()
    return sum(1 for t in trades if not t.get("closed_at"))
