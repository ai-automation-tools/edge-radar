#!/usr/bin/env python3
"""
build_cronsole_registry.py
Build the Cronsole template catalog for Edge-Radar's scheduled jobs.

Writes a Registry v1 catalog into site/registry/ (index.json, templates/<id>.json,
packs/edge-radar.json), which Vercel serves at
https://edge-radar.ai-automation-tools.dev/registry/ and the Cronsole gallery lists beside
its own templates. Files are LF and deterministic (no timestamps), because Cronsole checks
each file's sha256 over its exact bytes.

One template per installer profile in install_windows_task.py, except `account-graph`: its
script lives under docs/my-documents/, which is gitignored, so it exists on no clone but the
owner's. The two that place orders (LIVE_PROFILES) take a Mode parameter that defaults to
`preview`; only an explicit `execute` adds --execute (see _apply_mode in scripts/scan.py).

These templates are the tracked definition of the scheduled jobs. The .bat files the installer
points at are gitignored (scripts/schedulers/* — many hardcode local paths), so a clone has none
of them; where they exist, tests/test_cronsole_registry.py checks the scan flags still agree.

    python scripts/schedulers/automation/build_cronsole_registry.py [--check]

--check rebuilds in memory and exits 1 if site/registry/ is stale. CI runs it through
tests/test_cronsole_registry.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # automation -> schedulers -> scripts -> root
OUT = ROOT / "site" / "registry"
HOSTED = "https://edge-radar.ai-automation-tools.dev/registry/"
GALLERY = "https://cronsole.ai-automation-tools.dev/"

PY = r'"{{repoPath}}\.venv\Scripts\python.exe"'
# The flags the .bat files pass, kept identical (tests/test_cronsole_registry.py compares them).
LIVE_PROFILES = {"execute", "next-day"}


def scan_cmd(max_bets: int, date: str, folder: str, live: bool) -> str:
    cmd = (
        PY + r' "{{repoPath}}\scripts\scan.py" sports'
        f" --unit-size 1 --max-bets {max_bets} --min-bets 1 --budget 12% --date {date}"
        " --exclude-open --save"
        + r' --report-dir "{{repoPath}}\reports\Sports\schedulers'
        + "\\"
        + folder
        + '"'
    )
    return cmd + " --mode {{mode}}" if live else cmd


def script_cmd(script: str, args: str) -> str:
    return PY + r' "{{repoPath}}\scripts' + "\\" + script + '" ' + args


NEEDS = (
    "Needs a clone of ai-automation-tools/edge-radar on the machine the task runs on, "
    "with its .venv and a .env holding your Kalshi and Odds API keys "
    "(python scripts/doctor.py checks both)."
)
LIVE = (
    "Starts in preview: no orders until you set Mode to execute, and even then only when "
    "DRY_RUN=false in your .env. In execute mode it places REAL Kalshi orders, Kelly-sized, "
    "through every risk gate (daily loss limit, exposure caps, per-event limits). "
    "Read docs/setup/AUTOMATION_GUIDE.md first."
)

REPO_PARAM = {
    "key": "repoPath",
    "label": "Edge-Radar clone",
    "type": "path",
    "required": True,
    "help": r"Absolute path to your clone, e.g. C:\Users\you\edge-radar. "
    "Its .venv and .env are used.",
}
MODE_PARAM = {
    "key": "mode",
    "label": "Mode",
    "type": "select",
    "default": "preview",
    "required": True,
    "options": ["preview", "execute"],
    "help": "preview saves the report and places no orders. execute places real Kalshi orders "
    "(only when DRY_RUN=false in .env).",
}

# (profile, id, name, cron UTC, category, tags, command, params, description)
TEMPLATES = [
    (
        "scan",
        "edge-radar-scan",
        "Edge-Radar: Morning Scan (preview)",
        "0 12 * * *",
        "other",
        ["kalshi", "sports-betting", "scan", "preview"],
        scan_cmd(7, "today", "same-day-executions", live=False),
        [REPO_PARAM],
        "Scans today's Kalshi sports markets against 12 sportsbooks and saves a ranked report "
        "of edges. Preview only: never places an order. "
        "Default 12:00 UTC (8 AM US Eastern in summer).",
    ),
    (
        "execute",
        "edge-radar-execute",
        "Edge-Radar: Morning Scan + Execute",
        "0 12 * * *",
        "other",
        ["kalshi", "sports-betting", "execute", "live-orders"],
        scan_cmd(5, "today", "same-day-executions", live=True),
        [REPO_PARAM, MODE_PARAM],
        "Scans today's games and sizes up to 5 bets with Kelly, skipping markets you already "
        f"hold. {LIVE} Default 12:00 UTC (8 AM US Eastern in summer).",
    ),
    (
        "next-day",
        "edge-radar-next-day",
        "Edge-Radar: Next-Day Scan + Execute",
        "0 1 * * *",
        "other",
        ["kalshi", "sports-betting", "execute", "live-orders"],
        scan_cmd(5, "tomorrow", "next-day-executions", live=True),
        [REPO_PARAM, MODE_PARAM],
        "Scans tomorrow's games the night before, to catch early lines; not every market is "
        f"posted yet. {LIVE} Default 01:00 UTC (9 PM US Eastern in summer).",
    ),
    (
        "settle",
        "edge-radar-settle",
        "Edge-Radar: Hourly Settlement",
        "35 * * * *",
        "data-sync",
        ["kalshi", "settlement", "pnl", "clv"],
        script_cmd(r"kalshi\kalshi_settler.py", "settle"),
        [REPO_PARAM],
        "Settles finished trades against Kalshi, records realized P&L and closing-line value, "
        "and keeps the daily-loss gate's view current. Idempotent, places no orders. "
        "Hourly at :35.",
    ),
    (
        "calibration",
        "edge-radar-calibration",
        "Edge-Radar: Weekly Calibration",
        "0 23 * * 0",
        "monitoring",
        ["kalshi", "calibration", "model", "report"],
        script_cmd(r"kalshi\model_calibration.py", "--days 30 --save"),
        [REPO_PARAM],
        "30-day calibration report (Brier score, calibration curve, recommendations) saved to "
        "reports/Calibration/. Places no orders. "
        "Default Sunday 23:00 UTC (7 PM US Eastern in summer).",
    ),
    (
        "odds-keys",
        "edge-radar-odds-keys",
        "Edge-Radar: Weekly Odds API Key Probe",
        "0 22 * * 0",
        "monitoring",
        ["odds-api", "quota", "health-check"],
        script_cmd(r"shared\check_odds_keys.py", "--live"),
        [REPO_PARAM],
        "Probes each Odds API key's remaining quota, so a drained or dead key shows up before "
        "a scan needs it. One request per key. "
        "Default Sunday 22:00 UTC (6 PM US Eastern in summer).",
    ),
]
EXCLUDED = {"account-graph": "its script lives under docs/my-documents/, which is gitignored"}

PACK = {
    "id": "edge-radar",
    "name": "Edge-Radar",
    "description": "Scheduled scans, settlement and upkeep for Edge-Radar's Kalshi "
    "edge-detection system. The two that can place orders start in preview.",
}


def template(profile, tid, name, cron, category, tags, command, params, desc) -> dict:
    return {
        "schemaVersion": "1.0",
        "id": tid,
        "name": name,
        "description": f"{desc} {NEEDS}",
        "runtime": "python",
        "os": "windows",
        "category": category,
        "tags": sorted({"edge-radar", *tags}),
        "trigger": {"kind": "schedule", "cron": cron},
        "commandTemplate": command,
        "parameters": params,
        "compatibleTargets": ["windows", "cronsole-native"],
        "execution": {"timeoutSec": 1800},
        "author": "ai-automation-tools",
    }


def dump(obj: object) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build() -> dict[Path, bytes]:
    files: dict[Path, bytes] = {}
    entries = []
    built = [template(*t) for t in TEMPLATES]
    for t in built:
        rel = f"templates/{t['id']}.json"
        body = dump(t)
        files[OUT / rel] = body
        entries.append(
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
                "tags": t["tags"],
                "runtime": t["runtime"],
                "os": t["os"],
                "compatibleTargets": t["compatibleTargets"],
                "path": rel,
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    rel = f"packs/{PACK['id']}.json"
    body = dump({"cronsoleCatalogVersion": "1.0", "pack": PACK, "templates": built})
    files[OUT / rel] = body
    pack_entry = {
        **PACK,
        "templateIds": [t["id"] for t in built],
        "path": rel,
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    files[OUT / "index.json"] = dump(
        {"registryVersion": "1.0", "templates": entries, "packs": [pack_entry]}
    )
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[1])
    ap.add_argument("--check", action="store_true", help="Exit 1 if site/registry/ is out of date.")
    args = ap.parse_args()
    files = build()
    existing = set(OUT.rglob("*.json")) if OUT.exists() else set()
    stale = [p for p, b in files.items() if not p.exists() or p.read_bytes() != b]
    orphans = existing - set(files)
    if args.check:
        for p in stale + sorted(orphans):
            print(f"stale: {p.relative_to(ROOT)}")
        return 1 if stale or orphans else 0
    for p in orphans:
        p.unlink()
    for p, body in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    print(f"registry: {len(TEMPLATES)} templates, 1 pack -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
