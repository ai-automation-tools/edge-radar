"""ER-51: bare `make` is harmless and the money path has a code owner."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_bare_make_prints_help():
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^\.DEFAULT_GOAL\s*:=\s*help\s*$", text, re.M)
    assert re.search(r"^help:", text, re.M)


def test_codeowners_cover_the_money_path():
    owned = {
        line.split()[0]
        for line in (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    for path in ("/scripts/kalshi/", "/scripts/shared/", "/scripts/schedulers/", "/app/"):
        assert path in owned, path
