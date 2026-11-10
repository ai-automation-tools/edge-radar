"""Consistency checks for the two static pages.

``site/index.html`` is the public page (edge-radar.ai-automation-tools.dev, Vercel) and
``.claude/html/index.html`` is the personal ops deck (edge-radar.mikesailab.com, GitHub Pages).
Both were rebuilt on 2026-10-05 in the ai-automation-tools.dev design vocabulary. These tests pin
the parts that drift by hand: the org source-bar convention, the numbers the pages quote, the
quick-start commands, and the scheduler inventory the ops deck renders.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "site" / "index.html"
OPS = ROOT / ".claude" / "html" / "index.html"
AGENTS_MD = ROOT / "AGENTS.md"
README = ROOT / "README.md"
SCHEDULES = ROOT / "docs" / "task-schedules" / "README.md"


@pytest.fixture(scope="module")
def public() -> str:
    return PUBLIC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ops() -> str:
    return OPS.read_text(encoding="utf-8")


# ── Shared wiring ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("page", [PUBLIC, OPS], ids=["public", "ops"])
def test_no_tailwind_cdn_and_consent_loads(page: Path) -> None:
    html = page.read_text(encoding="utf-8")
    assert "cdn.tailwindcss.com" not in html, "the redesign dropped the Tailwind play CDN"
    assert 'src="https://ai-automation-tools.dev/consent.js" defer' in html
    assert 'data-ail-consent="manage"' in html, "Cookie settings hook"
    assert 'href="https://ai-automation-tools.dev/cookies.html"' in html


@pytest.mark.parametrize("page", [PUBLIC, OPS], ids=["public", "ops"])
def test_reduced_motion_and_tokens(page: Path) -> None:
    html = page.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in html
    assert "--accent: #34d399" in html, "Edge-Radar's org accent is emerald-400"
    assert "JetBrains+Mono" in html and "Inter:wght" in html


# ── Source bar: required on every *.ai-automation-tools.dev site, absent on the ops deck ──


def test_public_page_carries_the_org_source_bar(public: str) -> None:
    bar = re.search(r'<div class="src-bar">(.*?)</div>', public, re.S)
    assert bar, "source bar markup"
    assert "View source" in bar.group(1)
    assert 'href="https://github.com/ai-automation-tools/edge-radar"' in bar.group(1)
    # The bar sits above every other piece of chrome.
    assert public.index('<div class="src-bar">') < public.index('<header class="topbar">')
    # Edge-Radar also carries the optional hero repo button
    # (org README: "the bar is the constant, the button is the invitation").
    assert "Source on GitHub" in public


def test_ops_deck_has_no_source_bar(ops: str) -> None:
    assert "src-bar" not in ops and "View source" not in ops
    assert 'name="robots" content="noindex"' in ops


# ── Numbers the pages quote ──────────────────────────────────────────────────


def _gate_rows() -> list[str]:
    text = AGENTS_MD.read_text(encoding="utf-8")
    block = text[text.index("### Execution gates") : text.index("### Sizing rules")]
    return re.findall(r"^\| ([0-9][0-9.b]*) \|", block, re.M)


def test_public_page_links_every_template_to_cronsole(public: str) -> None:
    """The Schedule section renders registry/index.json live and links each card to the gallery."""
    assert 'id="schedule"' in public and 'href="#schedule"' in public
    assert "fetch('registry/index.json')" in public
    assert "${GALLERY}#/t/${encodeURIComponent(t.id)}" in public
    assert "https://cronsole.ai-automation-tools.dev/#/collection/edge-radar" in public
    assert (
        ROOT / "site" / "registry" / "index.json"
    ).is_file(), "the section reads the published registry"


def test_public_gate_grid_matches_claude_md(public: str) -> None:
    expected = _gate_rows()
    assert len(expected) == 21
    script = public[
        public.index("const GATES = [") : public.index("];", public.index("const GATES = ["))
    ]
    ids = re.findall(r"\{ id: '([0-9][0-9.b]*)'", script)
    assert ids == expected, "GATES in site/index.html must list AGENTS.md's gates, in order"
    assert f"{len(expected)} risk gates" in public


@pytest.mark.parametrize("page", [PUBLIC, OPS], ids=["public", "ops"])
def test_pipeline_has_seven_steps(page: Path) -> None:
    html = page.read_text(encoding="utf-8")
    assert len(re.findall(r'<div class="step">', html)) == 7
    assert "7 pipeline stages" in html


def test_gate_lab_defaults_match_risk_limits(public: str) -> None:
    text = AGENTS_MD.read_text(encoding="utf-8")
    defaults = {
        "feeRate": re.search(r"^KALSHI_FEE_RATE=([0-9.]+)", text, re.M).group(1),
        "maxEdge": re.search(r"^MAX_EDGE=([0-9.]+)", text, re.M).group(1),
        "minPrice": re.search(r"^MIN_MARKET_PRICE=([0-9.]+)", text, re.M).group(1),
        "kelly": re.search(r"^KELLY_FRACTION=([0-9.]+)", text, re.M).group(1),
        "noFavThreshold": re.search(r"^NO_SIDE_FAVORITE_THRESHOLD=([0-9.]+)", text, re.M).group(1),
        "noMinEdge": re.search(r"^NO_SIDE_MIN_EDGE=([0-9.]+)", text, re.M).group(1),
        "noMinEdgeGlobal": re.search(r"^NO_SIDE_MIN_EDGE_GLOBAL=([0-9.]+)", text, re.M).group(1),
    }
    lab = re.search(r"const D = \{(.*?)\};", public).group(1)
    for key, value in defaults.items():
        found = re.search(rf"{key}: ([0-9.]+)", lab)
        assert found, key
        assert float(found.group(1)) == float(
            value
        ), f"{key}: lab {found.group(1)} vs AGENTS.md {value}"


# ── Quick start: every command the terminal shows is one the README or AGENTS.md documents ──


def test_quick_start_commands_come_from_the_docs(public: str) -> None:
    docs = README.read_text(encoding="utf-8") + AGENTS_MD.read_text(encoding="utf-8")
    script = public[public.index("const SCRIPTS = {") : public.index("const termOut")]
    cmds = {c for c in re.findall(r"\['cmd', '([^']+)'\]", script)}
    assert cmds, "terminal has commands"
    allowed_pwsh = {".venv\\\\Scripts\\\\Activate.ps1", "Copy-Item .env.example .env"}
    for cmd in cmds:
        if cmd in allowed_pwsh:
            continue
        assert cmd.replace("\\\\", "\\") in docs, f"not in README/AGENTS.md: {cmd}"


# ── Ops deck: the schedule mirrors docs/task-schedules/README.md ─────────────


def _readme_tasks() -> list[tuple[int, str]]:
    text = SCHEDULES.read_text(encoding="utf-8")
    block = text[text.index("## At a Glance") : text.index("### Daily fire sequence")]
    return [(int(n), name) for n, name in re.findall(r"^\| (\d+) \| `([^`]+)`", block, re.M)]


def test_ops_schedule_matches_task_schedules_readme(ops: str) -> None:
    expected = _readme_tasks()
    assert len(expected) == 16
    script = ops[ops.index("const SCHED = [") : ops.index("];", ops.index("const SCHED = ["))]
    found = [(int(n), name) for n, name in re.findall(r"\{ n: (\d+),\s+id: '([^']+)'", script)]
    assert (
        found == expected
    ), "SCHED in .claude/html/index.html must list the README's tasks, in order"
    orders = len(re.findall(r"kind: 'orders'", script))
    assert orders == 5 and "5 place orders" in ops
    assert f"{len(expected)} scheduled tasks" in ops


def test_ops_schedule_times_match_readme(ops: str) -> None:
    text = SCHEDULES.read_text(encoding="utf-8")
    block = text[text.index("## At a Glance") : text.index("### Daily fire sequence")]
    pattern = r"^\| \d+ \| `([^`]+)`[^|]*\| (?:Daily|Sat|Sun|Sun–Thu) (\d{1,2}:\d{2} [AP]M)"
    readme_times = dict(re.findall(pattern, block, re.M))
    script = ops[ops.index("const SCHED = [") : ops.index("];", ops.index("const SCHED = ["))]
    for task, t24 in re.findall(r"id: '([^']+)'.*?time: '(\d{2}:\d{2})'", script):
        hour, minute = (int(x) for x in t24.split(":"))
        twelve = f"{(hour + 11) % 12 + 1}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
        assert (
            readme_times.get(task) == twelve
        ), f"{task}: page {twelve} vs README {readme_times.get(task)}"
