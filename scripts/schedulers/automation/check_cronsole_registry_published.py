#!/usr/bin/env python3
"""
check_cronsole_registry_published.py
Check that the Cronsole catalog Vercel serves matches site/registry/ on this checkout.

Fetches index.json from https://edge-radar.ai-automation-tools.dev/registry/, compares every
template and pack id and sha256 with site/registry/index.json, then downloads each file and
hashes what is actually served. Exits 1 on any difference. A merge that never deployed looks
fine from inside the repo; this is the check that can see it. Runs daily in registry-drift.yml.

    python scripts/schedulers/automation/check_cronsole_registry_published.py [base-url]
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_cronsole_registry import HOSTED, OUT  # noqa: E402


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "edge-radar-registry-check"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def entries(index: dict) -> dict[str, str]:
    return {e["path"]: e["sha256"] for e in index.get("templates", []) + index.get("packs", [])}


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else HOSTED).rstrip("/") + "/"
    local = entries(json.loads((OUT / "index.json").read_text(encoding="utf-8")))
    live = entries(json.loads(fetch(base + "index.json")))
    problems = [f"missing from the host: {p}" for p in sorted(local.keys() - live.keys())]
    problems += [
        f"on the host but not in site/registry/: {p}" for p in sorted(live.keys() - local.keys())
    ]
    problems += [
        f"different sha256 in the hosted index: {p}"
        for p in sorted(local.keys() & live.keys())
        if local[p] != live[p]
    ]
    for path, digest in sorted(live.items()):
        if hashlib.sha256(fetch(base + path)).hexdigest() != digest:
            problems.append(f"served bytes don't match the hosted index: {path}")
    for p in problems:
        print(f"DRIFT {p}")
    print(f"{base}: {len(live)} files checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
