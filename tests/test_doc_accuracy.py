"""ER-29: the numbers and links the docs quote match the code."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _tracked_md() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [
        ROOT / f for f in out.split() if f != "docs/CHANGELOG.md"
    ]  # history may cite removed files


def _exists_exact(p: Path) -> bool:
    """Exists with this exact case: Windows ignores case, Linux CI does not."""
    p = Path(os.path.normpath(p))
    return p.exists() and (p.name in ("", ".", "..") or p.name in os.listdir(p.parent))


def _gate_ids() -> list[str]:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    block = text[text.index("### Execution gates") : text.index("### Sizing rules")]
    return re.findall(r"^\| ([0-9][0-9.b]*) \|", block, re.M)


def test_relative_links_resolve():
    link = re.compile(r"\]\(([^)\s]+)\)|href=\"([^\"]+)\"")
    broken = []
    for md in _tracked_md():
        text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
        for m in link.finditer(text):
            url = (m.group(1) or m.group(2)).split("#")[0]
            if url and not re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I) and not url.startswith("<"):
                if not _exists_exact(md.parent / url):
                    broken.append(f"{md.relative_to(ROOT)}: {url}")
    assert not broken


def test_every_gate_count_is_the_agents_table():
    n = len(_gate_ids())
    wrong = []
    for md in _tracked_md() + [ROOT / "site" / "index.html"]:
        text = md.read_text(encoding="utf-8")
        for m in re.finditer(r"\b(\d+) (?:risk )?gates\b", text):
            if int(m.group(1)) > 9 and int(m.group(1)) != n:  # "gates 8-9" etc. are gate numbers
                wrong.append(f"{md.relative_to(ROOT)}: {m.group(0)}")
        wrong += [
            f"{md.relative_to(ROOT)}: {m.group(0)}"
            for m in re.finditer(
                r"\b(?:fifteen|sixteen|eighteen|nineteen|twenty)\b[- ](?:risk )?gates", text, re.I
            )
        ]
    assert not wrong, f"AGENTS.md lists {n} gates"


@pytest.mark.parametrize(
    "doc, start",
    [
        ("docs/setup/ARCHITECTURE.md", "### Risk Gate Pipeline"),
        ("docs/scripts/per-script/kalshi_executor.md", "### Risk Gates"),
    ],
)
def test_gate_tables_list_every_gate(doc, start):
    text = (ROOT / doc).read_text(encoding="utf-8")
    block = text[text.index(start) :]
    block = block[: block.index("\n#", 1)]
    assert re.findall(r"^\| ([0-9][0-9.b]*) \|", block, re.M) == _gate_ids()


def test_sportsbook_claims_match_book_weights():
    src = (ROOT / "scripts" / "kalshi" / "edge_detector.py").read_text(encoding="utf-8")
    block = src[src.index("BOOK_WEIGHTS = {") : src.index("}", src.index("BOOK_WEIGHTS = {"))]
    us_books = [k for k in re.findall(r'"(\w+)":', block) if k != "pinnacle"]
    assert len(us_books) == 9
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "nine US sportsbooks" in readme
    for md in _tracked_md():
        text = md.read_text(encoding="utf-8")
        assert not re.search(r"\b(?:12|8-12|5-12) (?:US )?sportsbooks?\b", text), md
        assert not re.search(r"\bCirca\b", text), f"{md}: Circa never arrives (B7)"


def test_env_example_lists_every_config_key():
    config = (ROOT / "app" / "config.py").read_text(encoding="utf-8")
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    keys = set(
        re.findall(r'(?:_str|_float|_int|_bool|_list|getenv)\(\s*"([A-Z][A-Z0-9_]+)"', config)
    )
    assert len(keys) > 50
    assert not sorted(k for k in keys if not re.search(rf"\b{k}\b", example))
    assert "MIN_EDGE_THRESHOLD_<SPORT>_<CATEGORY>" in example
