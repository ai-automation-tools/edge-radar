#!/usr/bin/env python3
"""Weekly betting audit: the /betting-logic-review battery, made mechanical.

The 2026-10-26 and 2026-10-27 reviews found, by hand, defects no scheduled job
would have surfaced:

  - a sport scanned at zero markets all season (dead series prefixes),
  - context data (rest days) leaking between sports that share a team code,
  - spread/total models that over-claim in one direction while outcomes track
    the market, found only after each sport had already lost money.

This script runs those checks across EVERY sport each week, deterministically,
from local data (settlement log, trade log, shadow book, logs, the latest drift
probe). It writes nothing but its own report, places no orders, and never
touches `.env`. With `--analyze` it appends a tool-restricted, read-only
`claude -p` pass (the same pattern as integration_drift.py).

    python scripts/backtest/betting_audit.py --save
    python scripts/backtest/betting_audit.py --save --analyze auto

Exit: 0 when the audit ran (the verdict is in the report), 1 if it crashed.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paths  # noqa: F401 -- configures sys.path

from trade_log import load_settlement_log, load_trade_log  # noqa: E402

ROOT = paths.PROJECT_ROOT
REPORT_DIR = ROOT / "reports" / "Maintenance" / "betting-audit"
DRIFT_DIR = ROOT / "reports" / "Maintenance" / "drift"
SHADOW_PATH = paths.DATA_DIR / "history" / "shadow_book.json"
STDEV_PATH = paths.DATA_DIR / "cache" / "calibration_stdevs.json"

# Rest-day data is an NBA/NHL input; on any other sport it is a leak (2026-10-27).
REST_SPORTS = ("KXNBA", "KXNHL")
REST_LEAK_FIXED = "2026-10-28"  # first detector log written with the fix
MIN_N = 8  # smallest series/side sample worth a z-score
Z_FLAG = -1.5  # wins this many sigma under the model's own expectation
SKEW_FLAG = 0.90  # pre-gate candidates this one-directional
SKEW_MIN_N = 20

OK, WARN = "OK", "WARN"


def _iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _series(ticker: str) -> str:
    return (ticker or "").split("-")[0]


def _floors() -> dict[str, float]:
    # The executor loads .env and snapshots the per-sport floors at import.
    import kalshi_executor

    return dict(kalshi_executor._PER_SPORT_MIN_EDGE)


def _floor_for(ticker: str, category: str | None, floors: dict[str, float]) -> float | None:
    from ticker_display import _detect_sport

    sport = _detect_sport(ticker)
    if not sport:
        return None
    return floors.get(f"{sport}_{category}", floors.get(sport))


def _direction(row: dict) -> str:
    """Human direction of a bet: Over/Under for totals, cover/not for spreads."""
    cat, side = row.get("category"), row.get("side")
    if cat == "total":
        return "over" if side == "yes" else "under"
    if cat == "spread":
        return "cover" if side == "yes" else "no-cover"
    return side or "?"


# ── 1. Model vs market vs outcome, every series and side ─────────────────────


def calibration_by_series(settlements: list[dict], since: datetime | None) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for s in settlements:
        if s.get("fair_value") is None or s.get("market_price_at_entry") is None:
            continue
        if float(s.get("contracts") or 0) <= 0:
            continue
        settled = _iso(s.get("settled_at"))
        if since and (settled is None or settled < since):
            continue
        groups[(_series(s["ticker"]), s.get("side") or "?")].append(s)

    out = []
    for (series, side), rows in groups.items():
        n = len(rows)
        wins = sum(1 for r in rows if r.get("won"))
        fv = [float(r["fair_value"]) for r in rows]
        px = [float(r["market_price_at_entry"]) for r in rows]
        var_m = sum(p * (1 - p) for p in fv)
        var_k = sum(p * (1 - p) for p in px)
        cost = sum(float(r.get("cost") or 0) for r in rows)
        pnl = sum(float(r.get("net_pnl") or 0) for r in rows)
        out.append(
            {
                "series": series,
                "side": side,
                "n": n,
                "wins": wins,
                "model_ew": sum(fv),
                "market_ew": sum(px),
                "z_model": (wins - sum(fv)) / math.sqrt(var_m) if var_m else 0.0,
                "z_market": (wins - sum(px)) / math.sqrt(var_k) if var_k else 0.0,
                "roi": pnl / cost if cost else 0.0,
            }
        )
    out.sort(key=lambda r: r["z_model"])
    return out


# ── 2. Pre-gate direction skew (shadow book) ─────────────────────────────────


def load_shadow() -> list[dict]:
    try:
        d = json.loads(SHADOW_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return d if isinstance(d, list) else []


def candidate_skew(shadow: list[dict], since: datetime, min_edge: float = 0.03) -> list[dict]:
    """Share of the model's candidate edges pointing one way, per series.

    A model that likes only Unders (or only big covers) is the S21 one-sided
    book BEFORE any money is placed. The 10-27 review saw every MLS/European
    total candidate land on Under 4.5/5.5.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for r in shadow:
        seen = _iso(r.get("observed_at"))
        if seen is None or seen < since or float(r.get("edge") or 0) < min_edge:
            continue
        groups[_series(r.get("ticker", ""))].append(_direction(r))
    out = []
    for series, dirs in groups.items():
        top = max(set(dirs), key=dirs.count)
        out.append(
            {"series": series, "n": len(dirs), "top": top, "share": dirs.count(top) / len(dirs)}
        )
    out.sort(key=lambda r: (-r["share"], -r["n"]))
    return out


def shadow_brier(shadow: list[dict]) -> list[dict]:
    """Settled pre-gate rows: model vs market Brier per series (S18: always the pair)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in shadow:
        if r.get("won") is None or r.get("fair_value") is None:
            continue
        groups[_series(r.get("ticker", ""))].append(r)
    out = []
    for series, rows in groups.items():
        ys = [1.0 if r["won"] else 0.0 for r in rows]
        bm = sum((float(r["fair_value"]) - y) ** 2 for r, y in zip(rows, ys)) / len(rows)
        bk = sum((float(r["market_price"]) - y) ** 2 for r, y in zip(rows, ys)) / len(rows)
        out.append({"series": series, "n": len(rows), "model": bm, "market": bk})
    out.sort(key=lambda r: r["market"] - r["model"])
    return out


# ── 3. Context-data leaks ─────────────────────────────────────────────────────


def context_leaks(shadow: list[dict], since: datetime, log_days: int = 7) -> dict:
    """Rest data on a non-NBA/NHL ticker, in the shadow book or the detector log."""
    shadow_hits = sorted(
        {
            r["ticker"]
            for r in shadow
            if (r.get("details") or {}).get("rest")
            and not r.get("ticker", "").startswith(REST_SPORTS)
            and (_iso(r.get("observed_at")) or since) >= since
        }
    )
    cutoff = max((datetime.now() - timedelta(days=log_days)).strftime("%Y-%m-%d"), REST_LEAK_FIXED)
    log_hits: dict[str, int] = defaultdict(int)
    pat = re.compile(r"Rest day signal for (KX[A-Z0-9]+)-")
    for f in glob.glob(str(ROOT / "logs" / "edge_detector_*.log")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f)
        if not m or m.group(1) < cutoff:
            continue
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                hit = pat.search(line)
                if hit and not hit.group(1).startswith(REST_SPORTS):
                    log_hits[hit.group(1)] += 1
    return {"shadow": shadow_hits, "log": dict(log_hits)}


# ── 4. Order and gate health ──────────────────────────────────────────────────


def order_health(trades: list[dict], since: datetime) -> dict:
    live = [
        t for t in trades if not t.get("dry_run") and (_iso(t.get("timestamp")) or since) >= since
    ]
    filled = [t for t in live if float(t.get("filled_contracts") or 0) > 0]
    post_kickoff = [
        t["ticker"]
        for t in live
        if t.get("event_start_time") and t["timestamp"] > t["event_start_time"]
    ]
    no_start = [t["ticker"] for t in live if not t.get("event_start_time")]
    # Fees are stamped from the fills API at settlement, so only settled rows count.
    zero_fee = [
        t["ticker"] for t in filled if t.get("closed_at") and not float(t.get("taker_fees") or 0)
    ]
    errors = [
        f"{t['ticker']}: {(t.get('error') or t.get('status'))}"
        for t in live
        if t.get("error") or t.get("status") in ("error", "rejected")
    ]
    by_series: dict[str, int] = defaultdict(int)
    for t in filled:
        by_series[_series(t["ticker"])] += 1
    return {
        "orders": len(live),
        "filled": len(filled),
        "post_kickoff": post_kickoff,
        "no_start_time": no_start,
        "zero_fee_filled": zero_fee,
        "errors": errors,
        "by_series": dict(sorted(by_series.items(), key=lambda kv: -kv[1])),
    }


# ── 5. Coverage (from the latest drift probe) and stdev provenance ────────────


def latest_drift() -> dict:
    files = sorted(DRIFT_DIR.glob("drift_*.json"))
    if not files:
        return {}
    try:
        d = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    d["_file"] = files[-1].name
    return d


def unfitted_stdevs() -> list[str]:
    """Calibration-file entries identical to the code fallback -- never fitted."""
    import edge_detector as ed

    try:
        cal = json.loads(STDEV_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ["calibration_stdevs.json unreadable -- every sport is on the code fallback"]
    out = []
    for kind, code in (
        ("margin_stdev", ed.SPORT_MARGIN_STDEV),
        ("total_stdev", ed.SPORT_TOTAL_STDEV),
    ):
        for sport, val in (cal.get(kind) or {}).items():
            if sport in code and abs(float(val) - float(code[sport])) < 1e-9:
                out.append(f"{kind}.{sport}={val}")
    return out


# ── Report ────────────────────────────────────────────────────────────────────


def build(now: datetime, days: int = 60, recent: int = 14) -> tuple[str, str, dict]:
    settlements = load_settlement_log()
    trades = load_trade_log()
    shadow = load_shadow()
    floors = _floors()
    since, since_recent = now - timedelta(days=days), now - timedelta(days=recent)

    calib = calibration_by_series(settlements, since)
    lifetime = {(r["series"], r["side"]): r for r in calibration_by_series(settlements, None)}
    skew = candidate_skew(shadow, since_recent)
    sbrier = shadow_brier(shadow)
    leaks = context_leaks(shadow, since_recent)
    health = order_health(trades, since_recent)
    drift = latest_drift()
    unfit = unfitted_stdevs()

    def live_floor(series: str) -> float | None:
        cat = next((c for c in ("SPREAD", "TOTAL", "GAME") if series.endswith(c)), "GAME").lower()
        return _floor_for(series + "-X", cat, floors)

    flags: list[str] = []
    over_claim = [
        r
        for r in calib
        if r["n"] >= MIN_N and r["z_model"] <= Z_FLAG and (live_floor(r["series"]) or 0) < 1.0
    ]
    for r in over_claim:
        flags.append(
            f"`{r['series']}` {r['side'].upper()}: {r['wins']} wins vs {r['model_ew']:.1f} model / "
            f"{r['market_ew']:.1f} market over {days}d (z {r['z_model']:+.1f}), still live"
        )
    for r in skew:
        if r["n"] >= SKEW_MIN_N and r["share"] >= SKEW_FLAG:
            flags.append(
                f"`{r['series']}` pre-gate candidates {r['share']:.0%} `{r['top']}` "
                f"(n={r['n']}, {recent}d) -- one-directional before any money is placed"
            )
    if leaks["shadow"] or leaks["log"]:
        flags.append(
            f"Rest-day data on non-NBA/NHL markets: {len(leaks['shadow'])} shadow rows, "
            f"{sum(leaks['log'].values())} log lines -- the 10-27 leak is back"
        )
    if health["post_kickoff"]:
        flags.append(f"{len(health['post_kickoff'])} order(s) placed after start time (Gate 4.8)")
    if health["zero_fee_filled"]:
        flags.append(f"{len(health['zero_fee_filled'])} filled order(s) with no recorded fee")
    if health["errors"]:
        flags.append(f"{len(health['errors'])} order error(s) in {recent}d")
    for d in drift.get("dark") or []:
        flags.append(
            f"`{d['sport']}`: odds feed has {d['upcoming_events']} games, every Kalshi series empty"
        )
    if not drift:
        flags.append("No drift probe found -- coverage unverified")

    status = WARN if flags else OK
    L = [
        f"# Betting Audit -- {now.astimezone():%Y-%m-%d}",
        "",
        f"**Status: {status}** · window {days}d (calibration), {recent}d (candidates, orders)",
        "",
        "Deterministic battery from `/betting-logic-review`, run across every sport. Read-only:",
        "no orders, no `.env` writes.",
        "",
        "## Flags",
        "",
    ]
    L += [f"- {f}" for f in flags] or ["- None."]

    L += [
        "",
        f"## Model vs market vs outcome, by series and side ({days}d, n >= {MIN_N})",
        "",
        "z = (wins − expected) / σ. A negative model z with a market z near 0 means outcomes",
        "track the market, not the model.",
        "",
        "| Series | Side | n | Wins | Model E[W] | Market E[W] | z model | z market | ROI | Lifetime n/W | Floor |",  # noqa: E501
        "|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for r in calib:
        if r["n"] < MIN_N:
            continue
        life = lifetime.get((r["series"], r["side"]), {})
        fl = live_floor(r["series"])
        L.append(
            f"| {r['series']} | {r['side']} | {r['n']} | {r['wins']} | {r['model_ew']:.1f} "
            f"| {r['market_ew']:.1f} | {r['z_model']:+.1f} | {r['z_market']:+.1f} "
            f"| {r['roi']:+.0%} | {life.get('n', 0)}/{life.get('wins', 0)} "
            f"| {'off' if fl is not None and fl >= 1 else (fl if fl is not None else 'global')} |"
        )

    L += [
        "",
        f"## Pre-gate candidate direction (shadow book, {recent}d, edge >= 0.03)",
        "",
        "| Series | Candidates | Top direction | Share |",
        "|:--|--:|:--|--:|",
    ]
    L += [f"| {r['series']} | {r['n']} | {r['top']} | {r['share']:.0%} |" for r in skew] or [
        "| (no shadow rows in window) | | | |"
    ]

    L += ["", "## Shadow book Brier pair (settled pre-gate rows)", ""]
    if sbrier:
        L += ["| Series | n | Model Brier | Market Brier |", "|:--|--:|--:|--:|"]
        L += [
            f"| {r['series']} | {r['n']} | {r['model']:.4f} | {r['market']:.4f} |" for r in sbrier
        ]
    else:
        L.append("No settled shadow rows.")

    L += [
        "",
        f"## Orders ({recent}d)",
        "",
        f"- Live orders {health['orders']}, filled {health['filled']}: "
        + (", ".join(f"{k} {v}" for k, v in health["by_series"].items()) or "none"),
        f"- After start time: {len(health['post_kickoff'])} · missing start time: "
        f"{len(health['no_start_time'])} · filled with no fee: {len(health['zero_fee_filled'])} · "
        f"errors: {len(health['errors'])}",
    ]
    L += [f"    - {e}" for e in health["errors"][:10]]

    L += ["", "## Coverage (latest drift probe)", ""]
    if drift:
        flagged = [s for s in drift.get("series", []) if s.get("level") != OK]
        L.append(
            f"- `{drift['_file']}`: status {drift.get('status')}, {len(drift.get('series', []))} "
            f"series probed, {len(flagged)} flagged, {len(drift.get('dark') or [])} dark sport(s)"
        )
        L.append("- Empty series: " + (", ".join(sorted(drift.get("empty") or [])) or "none"))
    else:
        L.append("- No drift report found.")

    L += ["", "## Context-data scoping", ""]
    L.append(
        f"- Rest data on non-NBA/NHL markets: shadow {len(leaks['shadow'])}, "
        f"log {dict(leaks['log']) or 0}"
    )
    L += ["", "## Stdevs never fitted (calibration file equals code fallback)", ""]
    L += [f"- `{u}`" for u in unfit] or ["- None."]

    payload = {
        "status": status,
        "flags": flags,
        "calibration": calib,
        "skew": skew,
        "shadow_brier": sbrier,
        "leaks": leaks,
        "orders": health,
        "unfitted": unfit,
    }
    return status, "\n".join(L) + "\n", payload


ANALYSIS_PROMPT = """You are reviewing Edge-Radar's weekly betting audit (status {status}).
Report: {md}. Raw data: {js}. Repo root is the current directory; AGENTS.md holds the
rules and docs/CHANGELOG.md the reasoning behind each one. The newest
docs/my-documents/repo-reviews/*-betting-logic-review.md says what was already found.

For each flag: trace it to the code (scripts/kalshi/edge_detector.py,
scripts/kalshi/kalshi_executor.py, the per-sport stdev tables) and say whether it is
a model defect, a selection artifact (S21c: never fit a parameter on gate-selected
bets), variance, or already handled by an existing floor. Name the exact file and
function and the smallest fix. Do not re-litigate CHANGELOG decisions without new
numbers.

Rules: you are READ-ONLY -- you have no tools to edit files, run trades, or change
.env. Output GitHub markdown only, starting with "## Analysis" and ending with
"## Recommended actions" as a short checklist ordered by money at risk. Under 700
words. If nothing is wrong, say so in two lines.
"""


def run_analysis(status: str, md_path: Path, json_path: Path, timeout: int = 1200) -> str:
    prompt = ANALYSIS_PROMPT.format(status=status, md=md_path, js=json_path)
    try:
        proc = subprocess.run(
            [
                "claude",
                "-p",
                prompt,
                "--allowedTools",
                "Read,Grep,Glob",
                "--max-turns",
                "40",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            cwd=ROOT,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"## Analysis\n\n_Analysis pass failed: {e}_\n"
    out = (proc.stdout or "").strip()
    if proc.returncode != 0 or not out:
        return f"## Analysis\n\n_Analysis pass failed (exit {proc.returncode})._\n"
    return out + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--save", action="store_true", help="write the report under reports/")
    ap.add_argument("--days", type=int, default=60, help="calibration window")
    ap.add_argument("--recent", type=int, default=14, help="candidate/order window")
    ap.add_argument(
        "--analyze",
        choices=("never", "auto", "always"),
        default="never",
        help="append a read-only claude -p pass (auto = only when flagged)",
    )
    a = ap.parse_args(argv)

    now = datetime.now(timezone.utc)
    status, report, payload = build(now, a.days, a.recent)
    if a.save:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = now.astimezone().strftime("%Y-%m-%d")
        md_path = REPORT_DIR / f"betting_audit_{stamp}.md"
        json_path = REPORT_DIR / f"betting_audit_{stamp}.json"
        md_path.write_text(report, encoding="utf-8")
        json_path.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
        if a.analyze == "always" or (a.analyze == "auto" and status != OK):
            report += "\n" + run_analysis(status, md_path, json_path)
            md_path.write_text(report, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    print(f"AUDIT_STATUS={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
