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
REPO_HREF = 'href="https://github.com/ai-automation-tools/edge-radar"'


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


def test_public_headers_allow_every_external_origin(public: str) -> None:
    """ER-23: site/vercel.json sends a CSP; every origin the page loads from must be in it."""
    import json

    rules = json.loads((ROOT / "site" / "vercel.json").read_text(encoding="utf-8"))["headers"]
    hdrs = {h["key"]: h["value"] for h in rules[0]["headers"]}
    assert rules[0]["source"] == "/(.*)"
    assert hdrs["X-Content-Type-Options"] == "nosniff"
    csp = dict(d.strip().split(" ", 1) for d in hdrs["Content-Security-Policy"].split(";"))
    assert csp["frame-ancestors"] == "'self'" and csp["object-src"] == "'none'"
    sheets = [
        t for t in re.findall(r"<link\b[^>]*>", public, re.I) if 'rel="stylesheet"' in t.lower()
    ]
    for tags, directive in (
        (re.findall(r"<script\b[^>]*>", public, re.I), "script-src"),
        (sheets, "style-src"),
    ):
        for url in re.findall(r'(?:src|href)="(https://[^"/]+)', " ".join(tags), re.I):
            assert url in csp[directive], f"{url} missing from {directive}"


@pytest.mark.parametrize("page", [PUBLIC, OPS], ids=["public", "ops"])
def test_reduced_motion_and_tokens(page: Path) -> None:
    html = page.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in html
    assert "--accent: #34d399" in html, "Edge-Radar's org accent is emerald-400"
    assert "JetBrains+Mono" in html and "Inter:wght" in html


# ── Source bar: on every site built from this public repo (ER-24 added the ops deck) ──


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


def test_ops_deck_carries_the_source_bar_and_no_posture(ops: str) -> None:
    """ER-24: the deck is served from a public repo, so it states no live/dry posture,
    no Task Scheduler path and no copy-to-run trigger, and it links to the public
    explainer instead of copying it."""
    assert ops.index('<div class="src-bar">') < ops.index('<header class="topbar">')
    assert "View source" in ops
    assert 'name="robots" content="noindex"' in ops
    for leak in (
        "DRY_RUN=false",
        "schtasks",
        "Start-ScheduledTask",
        "Edge-Radar-MikesAILab",
        ">live<",
    ):
        assert leak not in ops, leak
    assert 'id="how"' not in ops and 'id="pipeline"' not in ops
    assert "https://edge-radar.ai-automation-tools.dev/#how" in ops


def test_ops_timeline_markers_have_a_24px_hit_area(ops: str) -> None:
    rule = re.search(r"^    \.tl \.mk::before \{[^}]*\}", ops, re.M)
    assert rule and "inset: -6px" in rule.group(0)  # 12px dot + 2 x 6px


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
    assert len(expected) == 22
    script = public[
        public.index("const GATES = [") : public.index("];", public.index("const GATES = ["))
    ]
    ids = re.findall(r"\{ id: '([0-9][0-9.b]*)'", script)
    assert ids == expected, "GATES in site/index.html must list AGENTS.md's gates, in order"
    assert f"{len(expected)} risk gates" in public


def test_pipeline_has_seven_steps() -> None:
    html = PUBLIC.read_text(encoding="utf-8")
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


# ── ER-10: risk and eligibility notice ──────────────────────────────────────

_RISK_PHRASES = (
    "Risk and eligibility.",
    "lose the whole stake",
    "not a forecast",
    "age and",
    "1-800-GAMBLER",
    "not affiliated with",
)


@pytest.mark.parametrize("path", [PUBLIC, README], ids=["site", "readme"])
def test_risk_and_eligibility_block(path: Path) -> None:
    text = path.read_text(encoding="utf-8").replace("&#39;", "'")
    missing = [p for p in _RISK_PHRASES if p not in text]
    assert not missing, f"{path.name} lost its risk notice: {missing}"


def _luminance(hex_colour: str) -> float:
    rgb = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def test_disclaimer_text_meets_contrast(public: str) -> None:
    for rule in (".fine {", "footer .fine {"):
        assert re.search(re.escape(rule) + r"[^}]*color: var\(--fg-3\)", public), rule
    # Dark tokens come first, light (`.light`) second.
    fgs = re.findall(r"--fg-3: (#[0-9a-f]{6});", public)
    bgs = re.findall(r"--bg: (#[0-9a-f]{6});", public)
    assert len(fgs) >= 2 and len(bgs) >= 2
    for fg, bg in zip(fgs[:2], bgs[:2]):
        hi, lo = sorted((_luminance(fg), _luminance(bg)), reverse=True)
        assert (hi + 0.05) / (lo + 0.05) >= 4.5, (fg, bg)


# ── ER-30: accessibility of the public page ─────────────────────────────────


@pytest.mark.parametrize("page", [PUBLIC, OPS], ids=["public", "ops"])
def test_no_text_in_fg5_and_fg4_meets_aa(page: Path) -> None:
    html = page.read_text(encoding="utf-8")
    assert (
        "color: var(--fg-5)" not in html
    ), "--fg-5 is for dots and rules; text uses --fg-4 or above"
    fg4 = re.findall(r"--fg-4: (#[0-9a-f]{6});", html)
    bgs = re.findall(r"--bg: (#[0-9a-f]{6});", html)
    for fg, bg in zip(fg4, bgs):
        hi, lo = sorted((_luminance(fg), _luminance(bg)), reverse=True)
        assert (hi + 0.05) / (lo + 0.05) >= 4.5, (fg, bg)


def test_public_page_widgets_use_native_semantics(public: str) -> None:
    # palette: a native modal dialog with a combobox and listbox, not a hand-rolled overlay
    assert '<dialog class="pal" id="pal"' in public and "pal.showModal()" in public
    assert 'role="dialog"' not in public and "aria-modal" not in public
    assert 'role="combobox"' in public and 'role="listbox"' in public
    # the tablist holds only tabs, and the panel is labelled by the selected one
    tablist = re.search(r'role="tablist"[^>]*>(.*?)\n\s*</div>', public, re.S).group(1)
    tags = re.findall(r"<(\w+)\b", tablist)
    assert tags.count("button") == 4 and set(tags) == {"button", "i"}, tags  # <i> is each tab's dot
    assert tablist.count('role="tab"') == 4
    assert 'role="tabpanel"' in public
    # visible focus on the sliders; no listitem outside a list; no label wrapping buttons
    assert re.search(r"input\[type=range\] \{[^}]*outline: none", public) is None
    assert "input[type=range]:focus-visible" in public
    assert 'role="listitem"' not in public
    assert not re.search(r"<label>(?:(?!</label>).)*<button", public, re.S)
    # motion: a pause control, and the diagram's motion choice is never overwritten
    assert 'id="motionBtn"' in public and "IntersectionObserver" in public
    assert "localStorage.getItem('archify-motion') === null" in public


def test_public_page_first_paint_stays_light(public: str) -> None:
    """ER-32: nothing external blocks the first paint, the fallback font cannot reflow the hero,
    and the 845 KB interactive diagram loads only on request."""
    blocking = re.findall(
        r'<link\b[^>]*rel="stylesheet"[^>]*>',
        re.sub(r"<noscript>.*?</noscript>", "", public, flags=re.S),
    )
    assert not [tag for tag in blocking if "https://" in tag], blocking
    assert "font-size-adjust:" in public
    # ch widths follow whichever font is showing, so they moved text on the swap
    assert not re.search(r"max-width:\s*[\d.]+ch", public)
    # ER-31: the picture links to the diagram page; no inline frame to trap scroll
    assert "<iframe" not in public
    assert re.search(
        r'<img src="diagram/betting-data-flow\.png" width="\d+" height="\d+" loading="lazy"', public
    )
    assert '<a class="btn btn-primary" href="diagram/betting-data-flow.html">' in public


def _rules(public: str) -> str:
    """The stylesheet below the dark and light token blocks."""
    css = public.split("<style>", 1)[1].split("</style>", 1)[0]
    css = re.sub(r"\n    :root \{.*?\n    \}\n", "\n", css, count=1, flags=re.S)
    return re.sub(r"\n    :root\.light \{.*?\n    \}\n", "\n", css, count=1, flags=re.S)


def test_public_page_follows_web_house_style(public: str) -> None:
    """ER-31: tokens not literals, the app icon as the mark, the switch last, one repo link."""
    rules = _rules(public)
    rules = re.sub(r"/\*.*?\*/", "", rules, flags=re.S)
    rules = re.sub(r"\.btn-gh(:hover)? \{[^}]*\}", "", rules)  # black in both themes, by design
    rules = rules.replace("linear-gradient(#000 0 0)", "").replace("linear-gradient(#000 60%", "")
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", rules)
    assert not re.search(r'style="--c:#', public)
    favicon = (ROOT / "site" / "favicon.svg").read_text(encoding="utf-8")
    glyph = re.search(r"<g transform.*?</g>", favicon).group(0)
    brand = public.split('<a class="brand"', 1)[1].split("</a>", 1)[0]
    assert glyph in brand, "the top-bar mark is the app icon"
    right = public.split('<div class="topbar-right">', 1)[1].split('<div class="mobile-nav"', 1)[0]
    order = [right.index(k) for k in ('id="palOpen"', 'class="theme-tg"', 'id="menuBtn"')]
    assert order == sorted(order), "theme switch is the last control before the phone menu"
    footer = public.split("<footer>", 1)[1]
    assert REPO_HREF not in footer.split('class="fine"', 1)[0]
    assert (
        "@media (min-width: 760px) { .nav { display: flex; } .menu-btn { display: none; } }"
        in public
    )


def test_diagram_page_carries_edge_radar_chrome() -> None:
    """ER-31: the served diagram has the favicon, a source bar with a way back and a landmark."""
    page = (ROOT / "site" / "diagram" / "betting-data-flow.html").read_text(encoding="utf-8")
    assert '<link rel="icon" href="../favicon.svg"' in page
    assert '<a class="er-back" href="../">' in page and REPO_HREF in page
    assert '<div class="container" role="main">' in page
    assert "localStorage.getItem('edge-radar.theme')" in page
