"""ER-25: every prompt that can place orders previews first and waits for "go".

Six execute prompts ran a fresh `--execute` straight away, and one placed bets
on rows nobody had seen. The rule: any `scripts/scan.py ... --execute` line in
a prompt names the rows it places (`--pick` replays the sports preview,
`--ticker` for scanners without a cache), and the prompt waits for **go**.
"""

from pathlib import Path

import pytest

PROMPTS = sorted((Path(__file__).resolve().parents[1] / "prompts").rglob("*.md"))


def test_prompts_found():
    assert len(PROMPTS) >= 27  # 8 prediction prompts retired with their scanners (ER-53)


@pytest.mark.parametrize("path", PROMPTS, ids=lambda p: p.stem)
def test_execute_only_after_go_and_only_chosen_rows(path: Path):
    text = path.read_text(encoding="utf-8")
    runs = [ln for ln in text.splitlines() if "scripts/scan.py" in ln and "--execute" in ln]
    for ln in runs:
        assert "--pick" in ln or "--ticker" in ln, f"{path.name}: unpicked --execute: {ln.strip()}"
    if runs or "--execute --pick" in text or "--execute --ticker" in text:
        assert "reply **go**" in text, f"{path.name}: places orders without waiting for go"
