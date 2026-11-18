"""ER-47: the files every agent session loads stay small.

Rules go in AGENTS.md in a line or two; the evidence goes in docs/RULES-RATIONALE.md.
Skill detail goes in skills/edge-radar/references/. Changelog months before the
current quarter move to docs/changelog/<YYYY-MM>.md.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "path, limit_kb",
    [
        ("AGENTS.md", 20),
        ("skills/edge-radar/SKILL.md", 15),
        ("docs/CHANGELOG.md", 150),
    ],
)
def test_loaded_docs_stay_under_their_limit(path, limit_kb):
    size = (ROOT / path).stat().st_size
    assert size < limit_kb * 1024, f"{path} is {size / 1024:.1f} KB; move detail out (see ER-47)"


def test_every_skill_reference_is_indexed_by_the_skill():
    skill = (ROOT / "skills/edge-radar/SKILL.md").read_text(encoding="utf-8")
    for ref in (ROOT / "skills/edge-radar/references").glob("*.md"):
        assert f"(references/{ref.name})" in skill, ref.name
