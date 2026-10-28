#!/usr/bin/env python
"""Integration drift probe: are the markets we fetch actually being scored?

    python scripts/kalshi/integration_drift.py            # print report
    python scripts/kalshi/integration_drift.py --save     # + reports/Maintenance/drift/

M1 (CHANGELOG 2026-10-03): Kalshi reworded NFL rules to "... Pro Football game"
and spread subtitles to "DEN Broncos wins by over 7.5 points". Team extraction
failed silently and 13 of 14 NFL games went unscored for ~2 weeks while every
scan printed "no opportunities" -- indistinguishable from a quiet slate. This
probe measures the gap directly, per series, before the day's first execution:

  - schema:   fields the detectors read are present on every market
  - parse:    team / both-teams / strike extract from subtitles and rules
  - suspect:  an extracted team name carrying league filler ("Pro Football")
  - match:    markets resolve to a cached Odds API event (only for game dates
              the cache covers, so an unposted line is not a miss)
  - wording:  rules_primary templates not seen before (data/cache/drift_baseline.json)
  - activity: last bet per sport from the trade log

Deterministic and read-only: Kalshi GETs only, and odds come from the file cache,
so it spends zero Odds API quota. New wording is auto-accepted into the baseline
only when its series still parses and matches cleanly; otherwise it stays flagged
every run until fixed.

Exit code: 0 OK, 10 WARN, 20 FAIL, 1 crash. The scheduler .bat keys on it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import paths  # noqa: F401 -- path setup
from dotenv import load_dotenv

load_dotenv(paths.PROJECT_ROOT / ".env")

import edge_detector as ed  # noqa: E402
from kalshi_client import KalshiClient  # noqa: E402
from ticker_display import _detect_sport  # noqa: E402
from trade_log import load_trade_log  # noqa: E402

ODDS_CACHE_DIR = paths.DATA_DIR / "cache" / "odds"
BASELINE_PATH = paths.DATA_DIR / "cache" / "drift_baseline.json"
REPORT_DIR = paths.PROJECT_ROOT / "reports" / "Maintenance" / "drift"

REQUIRED_FIELDS = (
    "ticker",
    "yes_ask_dollars",
    "no_ask_dollars",
    "yes_bid_dollars",
    "rules_primary",
)
SCORED_CATEGORIES = ("game", "spread", "total")
# League/format filler that should never end up inside a team name. Not
# "college": it is part of real names (Boston College); "College Football"
# filler still trips on "football".
SUSPECT_WORDS = re.compile(
    r"\b(pro|professional|football|basketball|baseball|hockey|soccer|game|match)\b",
    re.IGNORECASE,
)
MIN_SAMPLE = 5
PARSE_FAIL, MATCH_WARN, MATCH_FAIL, ODDS_MAX_AGE_H = 0.90, 0.80, 0.50, 48

OK, WARN, FAIL = "OK", "WARN", "FAIL"
_RANK = {OK: 0, WARN: 1, FAIL: 2}


def _worst(*levels: str) -> str:
    return max(levels, key=_RANK.__getitem__, default=OK)


def fetch_series(client: KalshiClient, prefix: str) -> list[dict]:
    out, cursor = [], None
    for _ in range(5):
        resp = client.get_markets(limit=1000, status="open", series_ticker=prefix, cursor=cursor)
        out.extend(resp.get("markets", []))
        cursor = resp.get("cursor", "")
        if not cursor:
            break
    return out


def load_cached_events(sport_key: str) -> tuple[list[dict], float | None]:
    """Newest cached game-odds payload for a sport; (events, age_hours)."""
    best, best_ts = None, None
    for f in ODDS_CACHE_DIR.glob(f"{sport_key}__*.json"):
        if "outright" in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            ts = datetime.fromisoformat(d["fetched_at"].replace("Z", "+00:00"))
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if d.get("events") and (best_ts is None or ts > best_ts):
            best, best_ts = d["events"], ts
    if best is None:
        return [], None
    return best, (datetime.now(timezone.utc) - best_ts).total_seconds() / 3600


def rules_template(market: dict, teams: tuple[str, str] | None, team: str | None) -> str:
    """rules_primary with names, numbers and dates abstracted away."""
    text = market.get("rules_primary", "") or ""
    text = re.split(r",?\s*then the market", text, maxsplit=1)[0]
    names = [n for n in (*(teams or ()), team) if n]
    for i, name in enumerate(sorted(set(names), key=len, reverse=True)):
        text = text.replace(name, f"<T{i}>")
    text = re.sub(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, \d{4}",
        "<DATE>",
        text,
    )
    text = re.sub(r"\d+(?:\.\d+)?", "N", text)
    if teams is None:
        text = "UNPARSED: " + text
    return re.sub(r"\s+", " ", text).strip()[:220]


def _game_in_feed(teams: tuple[str, str], day: str, events: list[dict]) -> bool:
    """Same-day event carrying both teams on opposite sides.

    One team is not enough: "Eastern Kentucky" nickname-matches "Kentucky
    Wildcats", which put unposted FCS games "in the feed". Garbled names that
    fail this are caught by the parse and league-filler checks instead.
    """
    return any(ed._commence_et_date(e) == day and ed._event_has_matchup(e, *teams) for e in events)


def probe_series(prefix: str, markets: list[dict], events: list[dict]) -> dict:
    cat = ed.categorize_market(prefix + "-")
    event_dates = {ed._commence_et_date(e) for e in events} - {None}
    missing = Counter()
    parsed = suspects = measurable = matched = 0
    templates: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    for m in markets:
        for f in REQUIRED_FIELDS:
            if m.get(f) in (None, ""):
                missing[f] += 1
        team = ed.extract_team_from_market(m)
        teams = ed.extract_event_teams(m)
        strike = ed.extract_strike(m) if cat in ("spread", "total") else 0.0
        ok = bool(teams) and strike is not None and (cat == "total" or bool(team))
        parsed += ok
        if not ok and len(examples["unparsed"]) < 3:
            examples["unparsed"].append(
                f"{m['ticker']}: team={team!r} teams={teams} strike={strike}"
            )
        if teams and any(SUSPECT_WORDS.search(t) for t in teams):
            suspects += 1
            if len(examples["suspect"]) < 3:
                examples["suspect"].append(f"{m['ticker']}: teams={teams}")
        templates[rules_template(m, teams, team)] += 1

        # A miss counts only when the feed carries this game -- some event that
        # day names one of the teams. Otherwise the line is simply not posted.
        day = ed._extract_game_date(m["ticker"])
        if events and teams and day in event_dates and _game_in_feed(teams, day, events):
            measurable += 1
            ev = ed.find_market_event(m, events)
            hit = ev is not None
            if hit and cat != "total" and team and team.lower() not in ("tie", "draw"):
                hit = any(
                    ed._team_match_strength(ev.get(side, "") or "", team) > 0
                    for side in ("home_team", "away_team")
                )
            matched += hit
            if not hit and len(examples["unmatched"]) < 3:
                examples["unmatched"].append(f"{m['ticker']}: team={team!r} teams={teams}")

    n = len(markets)
    parse_rate = parsed / n if n else None
    match_rate = matched / measurable if measurable >= MIN_SAMPLE else None
    level = OK
    reasons = []
    if missing:
        level = FAIL
        reasons.append(f"missing fields {dict(missing)}")
    if n >= MIN_SAMPLE and parse_rate < PARSE_FAIL:
        level = FAIL
        reasons.append(f"parse {parse_rate:.0%}")
    if suspects:
        level = _worst(level, WARN)
        reasons.append(f"{suspects} team names carry league filler")
    if match_rate is not None and match_rate < MATCH_WARN:
        level = _worst(level, FAIL if match_rate < MATCH_FAIL else WARN)
        reasons.append(f"odds match {match_rate:.0%} ({matched}/{measurable})")
    return {
        "prefix": prefix,
        "category": cat,
        "markets": n,
        "parse_rate": parse_rate,
        "measurable": measurable,
        "matched": matched,
        "match_rate": match_rate,
        "suspects": suspects,
        "missing": dict(missing),
        "templates": dict(templates),
        "examples": dict(examples),
        "level": level,
        "reasons": reasons,
    }


def last_bet_by_sport() -> dict[str, str]:
    last: dict[str, str] = {}
    for row in load_trade_log():
        if row.get("dry_run") or row.get("status") == "error":
            continue
        sport = _detect_sport(row.get("ticker", "")) or "other"
        ts = (row.get("timestamp") or "")[:10]
        if ts > last.get(sport, ""):
            last[sport] = ts
    return last


def run(
    save: bool, update_baseline: bool, analyze: str, autofix: bool = False, json_out: str = ""
) -> int:
    client = KalshiClient()
    try:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        baseline = {}
    first_run = not baseline

    by_sport: dict[str, list[str]] = defaultdict(list)
    for prefix, sport in ed.KALSHI_TO_ODDS_SPORT.items():
        if ed.categorize_market(prefix + "-") in SCORED_CATEGORIES:
            by_sport[sport].append(prefix)

    results, empty, odds_age, new_wording, dark = [], [], {}, [], []
    for sport, prefixes in sorted(by_sport.items()):
        events, age = load_cached_events(sport)
        if age is not None and age > ODDS_MAX_AGE_H:
            events = []
        odds_age[sport] = age
        sport_empty = []
        for prefix in prefixes:
            # Undated tickers (KXLALIGA-27-VIL) are season-winner futures that
            # share a game prefix; futures_edge.py scores those, not this path.
            markets = [
                m for m in fetch_series(client, prefix) if ed._extract_game_date(m["ticker"])
            ]
            if not markets:
                empty.append(prefix)
                sport_empty.append(prefix)
                continue
            r = probe_series(prefix, markets, events)
            r["sport"] = sport
            known = set(baseline.get(prefix, []))
            fresh = [t for t in r["templates"] if t not in known]
            healthy = r["level"] == OK
            if fresh and not first_run and not healthy:
                r["level"] = _worst(r["level"], WARN)
                r["reasons"].append(f"{len(fresh)} new rules wording(s)")
                new_wording.extend((prefix, t) for t in fresh)
            if fresh and (first_run or healthy or update_baseline):
                baseline[prefix] = sorted(known | set(fresh))
                if not first_run:
                    r.setdefault("accepted", fresh)
            results.append(r)
        # Every series for a sport empty while the books list games for it: the
        # prefixes are wrong, not the slate quiet. The six European leagues sat
        # here as "No open markets" all season on bare KX<LEAGUE> prefixes that
        # match no series. A sport with ANY open series is just between listings.
        upcoming = _upcoming_events(events)
        if sport_empty and len(sport_empty) == len(prefixes) and upcoming:
            dark.append((sport, sport_empty, upcoming))

    BASELINE_PATH.write_text(json.dumps(baseline, indent=1, sort_keys=True), encoding="utf-8")
    status = _worst(*(r["level"] for r in results), *(WARN for _ in dark))
    report = render(
        results, empty, odds_age, new_wording, last_bet_by_sport(), status, first_run, dark
    )
    print(report)
    payload = {
        "status": status,
        "series": results,
        "empty": empty,
        "dark": [{"sport": s, "prefixes": p, "upcoming_events": n} for s, p, n in dark],
    }
    if json_out:  # drift_autofix reads the probe on the fixed worktree this way
        Path(json_out).write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    if save:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d")
        md_path, json_path = REPORT_DIR / f"drift_{stamp}.md", REPORT_DIR / f"drift_{stamp}.json"
        md_path.write_text(report, encoding="utf-8")
        json_path.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
        # auto: model only when the probe flags something, plus a Monday sweep
        # for venue changes no probe can see (API changelog, new series).
        if analyze == "always" or (
            analyze == "auto" and (status != OK or datetime.now().weekday() == 0)
        ):
            analysis = run_analysis(status, md_path, json_path)
            report += "\n" + analysis
            md_path.write_text(report, encoding="utf-8")
            print(analysis)
            # Code changes only ever arrive as a DRAFT PR, and only when the
            # fix stage produced a diff that passed every check (drift_autofix).
            if autofix and status != OK:
                import drift_autofix

                section = drift_autofix.attempt(md_path, json_path, analysis)
                md_path.write_text(report + "\n" + section, encoding="utf-8")
                print(section)
    print(f"DRIFT_STATUS={status}")
    return {OK: 0, WARN: 10, FAIL: 20}[status]


ANALYSIS_PROMPT = """You are the Edge-Radar integration-drift analyst, running unattended.
Repo: the current directory. Read CLAUDE.md first, then the CHANGELOG entry
"2026-10-03 -- M1" for the failure class you are hunting: Kalshi changes its
market wording/fields/API and the scanner silently stops scoring markets.

Today's deterministic probe status: {status}. Its report: {md}
Its full JSON (per-series parse/match rates, unparsed/unmatched examples,
rules templates): {js}

Do this:
1. For every WARN/FAIL series, find the root cause in scripts/kalshi/edge_detector.py
   (extract_event_teams, extract_team_from_market, _clean_team, find_market_event,
   _team_match_strength, TEAM_ALIASES) and state the exact fix (file, function,
   proposed diff). Say plainly if a flag is a probe false positive instead.
2. Check Kalshi's public API changelog / docs (docs.kalshi.com) for changes in the
   last ~14 days: renamed or removed market fields, new series tickers replacing
   ones in KALSHI_TO_ODDS_SPORT / FILTER_SHORTCUTS, deprecated endpoints, order or
   fee changes. Compare against what scripts/kalshi/kalshi_client.py actually uses.
3. Briefly note any Odds API (the-odds-api.com) changes that affect sport keys or
   response shape.

Rules: you are READ-ONLY. Do not edit files, run trades, or change .env -- you have
no tools for it. Output GitHub markdown only, starting with "## Analysis", ending with
"## Recommended actions" as a short checklist ordered by urgency. Under 600 words.
If nothing is wrong, say so in two lines.
"""


def run_analysis(status: str, md_path: Path, json_path: Path, timeout: int = 900) -> str:
    """Headless Claude pass over the probe output; returns markdown to append.

    Tool-restricted (read + web only) instead of --dangerously-skip-permissions,
    which the 2026-09-23 consolidation removed from every unattended job.
    """
    prompt = ANALYSIS_PROMPT.format(status=status, md=md_path, js=json_path)
    try:
        proc = subprocess.run(
            [
                "claude",
                "-p",
                prompt,
                "--allowedTools",
                "Read,Grep,Glob,WebFetch,WebSearch",
                "--max-turns",
                "40",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            cwd=paths.PROJECT_ROOT,
            check=False,
        )
    except FileNotFoundError:
        return "## Analysis\n\n_Skipped: `claude` CLI not on PATH._\n"
    except subprocess.TimeoutExpired:
        return f"## Analysis\n\n_Skipped: Claude session timed out after {timeout}s._\n"
    if proc.returncode != 0 or not proc.stdout.strip():
        err = (proc.stderr or "").strip()[-400:] or f"exit {proc.returncode}"
        return f"## Analysis\n\n_Claude session failed: {err}_\n"
    return proc.stdout.strip() + "\n"


def _pct(x: float | None) -> str:
    return "-" if x is None else f"{x:.0%}"


def _upcoming_events(events: list[dict], days: int = 7) -> int:
    """Count odds-feed events starting within the next `days`."""
    now = datetime.now(timezone.utc)
    n = 0
    for e in events:
        try:
            t = datetime.fromisoformat(str(e.get("commence_time", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if now <= t <= now + timedelta(days=days):
            n += 1
    return n


def render(results, empty, odds_age, new_wording, last_bet, status, first_run, dark=()) -> str:
    now = datetime.now()
    L = [f"# Integration Drift Check -- {now:%Y-%m-%d %H:%M}", "", f"**Status: {status}**", ""]
    if first_run:
        L += ["_First run: wording baseline seeded from today's markets._", ""]
    if dark:
        L += ["## Sports with live odds but no open Kalshi series", ""]
        for sport, prefixes, n in dark:
            L.append(
                f"- **{sport}** (WARN): {n} upcoming event(s) in the odds feed, but "
                f"{', '.join(prefixes)} return no open markets -- check the series tickers"
            )
        L.append("")
    flagged = [r for r in results if r["level"] != OK]
    if flagged:
        L += ["## Flagged series", ""]
        for r in flagged:
            L.append(f"- **{r['prefix']}** ({r['level']}): {'; '.join(r['reasons'])}")
            for kind, exs in r["examples"].items():
                for e in exs:
                    L.append(f"    - {kind}: `{e}`")
        L.append("")
    if new_wording:
        L += ["## New rules wording (not yet accepted)", ""]
        L += [f"- `{p}`: {t}" for p, t in new_wording]
        L.append("")
    L += [
        "## Series",
        "",
        "| Series | Cat | Open | Parsed | Odds-matched | Suspect | Status |",
        "|:--|:--|--:|--:|--:|--:|:--|",
    ]
    for r in sorted(results, key=lambda r: (-_RANK[r["level"]], r["prefix"])):
        mt = (
            f"{_pct(r['match_rate'])} ({r['matched']}/{r['measurable']})"
            if r["measurable"]
            else "n/a"
        )
        L.append(
            f"| {r['prefix']} | {r['category']} | {r['markets']} | {_pct(r['parse_rate'])} "
            f"| {mt} | {r['suspects']} | {r['level']} |"
        )
    accepted = [(r["prefix"], t) for r in results for t in r.get("accepted", [])]
    if accepted:
        L += ["", "## Wording changes auto-accepted (series still healthy)", ""]
        L += [f"- `{p}`: {t}" for p, t in accepted]
    L += ["", "## Context", ""]
    L.append("- No open markets: " + (", ".join(sorted(empty)) or "none"))
    # Open markets with no fresh odds for their sport are fetched but can never
    # be scored -- the M1 outcome by another route (e.g. tennis outside Wimbledon).
    blind = sorted(
        r["prefix"]
        for r in results
        if odds_age.get(r["sport"]) is None or odds_age[r["sport"]] > ODDS_MAX_AGE_H
    )
    L.append(
        "- **Open markets, no fresh odds feed (never scored):** " + (", ".join(blind) or "none")
    )
    ages = ", ".join(
        f"{s.split('_', 1)[-1]} {'none' if a is None else f'{a:.0f}h'}"
        for s, a in sorted(odds_age.items())
    )
    L.append(f"- Odds cache age (match measured only if <= {ODDS_MAX_AGE_H}h): {ages}")
    cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    bets = ", ".join(
        f"{s} {d}{' (7d+)' if d < cutoff else ''}" for s, d in sorted(last_bet.items())
    )
    L.append(f"- Last live bet by sport: {bets}")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--save", action="store_true", help="write md + json to reports/Maintenance/drift/"
    )
    ap.add_argument(
        "--update-baseline",
        action="store_true",
        help="accept every current rules wording into the baseline (after verifying a fix)",
    )
    ap.add_argument(
        "--analyze",
        choices=("auto", "always", "never"),
        default="never",
        help="headless Claude pass (needs --save); auto = on WARN/FAIL or Mondays",
    )
    ap.add_argument(
        "--autofix",
        action="store_true",
        help="on WARN/FAIL, let Claude try a fix in a worktree; opens a DRAFT PR only if "
        "it changed code and passed tests + a better probe (drift_autofix.py)",
    )
    ap.add_argument("--json-out", default="", help=argparse.SUPPRESS)
    args = ap.parse_args()
    try:
        return run(args.save, args.update_baseline, args.analyze, args.autofix, args.json_out)
    except Exception as e:  # noqa: BLE001 -- crash must surface as exit 1, not a WARN
        print(f"integration_drift crashed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
