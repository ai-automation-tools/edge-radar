"""
build_betting_diagram.py — build and drift-check the betting-logic data-flow diagram.

docs/diagrams/betting-data-flow.json is the only file to edit. Every node cites the
code it describes (path + line range) at the commit pinned in `meta.repository.revision`.
A build renders it with Archify (https://github.com/tt-a1i/archify) into
betting-data-flow.html (interactive, source links go to GitHub at that commit) and
betting-data-flow.png (the homepage image; both are copied into site/diagram/, which is
all the homepage deploys), and records the git blob of every cited file
at the pinned commit in betting-data-flow.sources.lock.json. The site copy of the HTML
gets Edge-Radar's chrome (site_page(): favicon, source bar with a link back to the
homepage, the homepage's theme choice, the house ground and type); docs/ keeps Archify's
page as built.

The check compares those blobs with the staged copies. Any cited file that changed since
the pin may have moved or changed the logic a node describes, so the diagram is stale
until someone re-reads the code, fixes the JSON and rebuilds with --pin-head.

Exit codes:
    0 — built / current (or --hook, which only warns)
    1 — stale, never built, or the build failed

Invocation:
    python scripts/diagrams/build_betting_diagram.py               # rebuild at the pinned commit
    python scripts/diagrams/build_betting_diagram.py --pin-head    # re-pin to HEAD, then rebuild
    python scripts/diagrams/build_betting_diagram.py --check       # drift only, changes nothing
    pre-commit hook `betting-diagram-drift` runs --hook: warns, never blocks

Building needs Node, Chrome and the archify skill (default
~/.claude/skills/archify/bin/archify.mjs; override with --archify <path to archify.mjs>).
The check needs only git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DIAGRAMS = ROOT / "docs" / "diagrams"
STEM = "betting-data-flow"
SOURCE = DIAGRAMS / f"{STEM}.json"
HTML = DIAGRAMS / f"{STEM}.html"
PNG = DIAGRAMS / f"{STEM}.png"
RECEIPT = DIAGRAMS / f"{STEM}.delivery.json"
LOCK = DIAGRAMS / f"{STEM}.sources.lock.json"
BUILD_DIR = DIAGRAMS / ".build"
HOMEPAGE = ROOT / "site" / "diagram"
SCREENSHOT = f"{STEM}.visual-check.2048x1320.dark.png"
DEFAULT_ARCHIFY = Path.home() / ".claude" / "skills" / "archify" / "bin" / "archify.mjs"
CHROME = Path(__file__).with_name("site_chrome.html")


def chrome() -> dict[str, str]:
    """The @head, @style and @bar sections of site_chrome.html."""
    text = CHROME.read_bytes().decode("utf-8").replace("\r\n", "\n")
    return dict(re.findall(r"<!-- @(\w+) -->(.*?)\n(?=<!-- @|\Z)", text, re.S))


def site_page(html: str) -> str:
    """Archify's page with Edge-Radar's chrome, as served from site/diagram/."""
    for marker in ("<head>", "</head>", "<body>", '<div class="container">'):
        if html.count(marker) != 1:
            raise ValueError(f"expected one {marker} in the Archify page")
    part = chrome()
    return (
        html.replace("<head>", "<head>" + part["head"], 1)
        .replace("</head>", part["style"] + "\n</head>", 1)
        .replace("<body>", "<body>" + part["bar"], 1)
        .replace('<div class="container">', '<div class="container" role="main">', 1)
    )


def site_bytes(built: Path) -> bytes:
    """The bytes site/diagram/ should hold for a built file."""
    if built.suffix != ".html":
        return built.read_bytes()
    return site_page(built.read_bytes().decode("utf-8")).encode("utf-8")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def blob(rev: str, path: str) -> str | None:
    """Blob id of `path` at `rev` (`""` = the index), or None if it doesn't exist there."""
    try:
        return git("rev-parse", f"{rev}:{path}")
    except subprocess.CalledProcessError:
        return None


def cited_paths(spec: dict) -> list[str]:
    paths = set()
    for node in spec.get("nodes", []):
        for src in node.get("sources", []):
            paths.add(src["path"])
    return sorted(paths)


def find_issues() -> list[str]:
    if not RECEIPT.exists() or not LOCK.exists():
        return ["the diagram has never been built; run build_betting_diagram.py"]
    issues = []
    built = json.loads(RECEIPT.read_text(encoding="utf-8"))["specification"]["sha256"]
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != built:
        issues.append(f"{SOURCE.name} changed since the last build; rebuild it")
    spec = json.loads(SOURCE.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock.get("revision") != spec["meta"]["repository"]["revision"]:
        issues.append("the pinned revision changed since the last build; rebuild it")
    for built_file in (HTML, PNG):
        copy = HOMEPAGE / built_file.name
        if not copy.exists() or copy.read_bytes() != site_bytes(built_file):
            issues.append(f"site/diagram/{built_file.name} differs from the build; rebuild it")
    changed = []
    for path in cited_paths(spec):
        now = blob("", path)
        if now is None:
            issues.append(f"cited file {path} no longer exists")
        elif now != lock["files"].get(path):
            changed.append(path)
    if changed:
        issues.append(
            "cited code changed since the diagram was pinned to "
            f"{lock['revision'][:8]}: {', '.join(changed)}. Re-read it, update the nodes, "
            "line ranges and cards in the JSON, then rebuild with --pin-head"
        )
    return issues


def archify(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(script), *args], cwd=ROOT, capture_output=True, text=True)


def build(pin_head: bool, script: Path) -> None:
    if not script.exists():
        sys.exit(f"Archify not found at {script}; install the archify skill or pass --archify")
    spec = json.loads(SOURCE.read_text(encoding="utf-8"))
    cited = cited_paths(spec)
    if pin_head:
        dirty = git("status", "--porcelain", "--", *cited)
        if dirty:
            sys.exit(
                "Commit the cited files first; evidence is pinned to committed bytes:\n" + dirty
            )
        spec["meta"]["repository"]["revision"] = git("rev-parse", "HEAD")
        SOURCE.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", "utf-8")
    revision = spec["meta"]["repository"]["revision"]

    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    rel = lambda p: str(p.relative_to(ROOT))  # noqa: E731
    result = archify(
        script,
        "finalize",
        "dataflow",
        rel(SOURCE),
        rel(HTML),
        "--repo-root",
        ".",
        "--quality",
        "showcase",
        "--json",
        "--out-dir",
        rel(BUILD_DIR),
    )
    if result.returncode != 0:
        sys.exit(
            f"Archify finalize failed; see {rel(BUILD_DIR)}/{STEM}.finalize-summary.json\n"
            + result.stdout[-2000:]
        )
    visual = archify(
        script, "visual-check", rel(HTML), "--summary", "--out-dir", rel(BUILD_DIR / "visual")
    )
    shot = BUILD_DIR / "visual" / SCREENSHOT
    if visual.returncode != 0 or not shot.exists():
        sys.exit(f"Archify visual-check failed:\n{visual.stdout[-2000:]}")
    shutil.copyfile(shot, PNG)
    HOMEPAGE.mkdir(exist_ok=True)
    for built_file in (HTML, PNG):
        (HOMEPAGE / built_file.name).write_bytes(site_bytes(built_file))

    lock = {"revision": revision, "files": {p: blob(revision, p) for p in cited}}
    LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Built {rel(HTML)} and {rel(PNG)} at {revision[:8]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report drift, change nothing")
    mode.add_argument("--hook", action="store_true", help="like --check, but always exit 0")
    mode.add_argument("--pin-head", action="store_true", help="re-pin to HEAD, then build")
    parser.add_argument("--archify", type=Path, default=DEFAULT_ARCHIFY, help="path to archify.mjs")
    args = parser.parse_args()

    if args.check or args.hook:
        issues = find_issues()
        for issue in issues:
            print(f"ISSUE: betting-diagram: {issue}")
        if not issues:
            print("OK: betting-diagram is current")
        return 1 if issues and args.check else 0
    build(args.pin_head, args.archify)
    return 0


if __name__ == "__main__":
    sys.exit(main())
