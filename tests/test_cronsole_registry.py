"""The Cronsole catalog in site/registry/ is generated, current, and matches the installer.

The templates and the .bat files the installer registers are two descriptions of the same
jobs, so these tests fail when one changes without the other — above all, when a template
could place an order without the person applying it choosing to.
"""

from __future__ import annotations

import importlib.util
import json
import shlex
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
AUTOMATION = ROOT / "scripts" / "schedulers" / "automation"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


reg = _load("_cronsole_registry", AUTOMATION / "build_cronsole_registry.py")
installer = _load("_install_windows_task", AUTOMATION / "install_windows_task.py")
TEMPLATES = {t[0]: reg.template(*t) for t in reg.TEMPLATES}


def _scan_flags(tokens: list[str]) -> list[str]:
    """Flags after `sports`, without the two that legitimately differ (where, and whether live)."""
    out, skip = [], False
    for tok in tokens[tokens.index("sports") + 1 :]:
        if skip:
            skip = False
        elif tok in ("--report-dir", "--mode"):
            skip = True
        elif tok != "--execute":
            out.append(tok)
    return out


def test_registry_is_current():
    stale = [p for p, b in reg.build().items() if not p.exists() or p.read_bytes() != b]
    assert not stale, "run: python scripts/schedulers/automation/build_cronsole_registry.py"


def test_every_installer_profile_has_a_template_or_a_reason():
    assert set(TEMPLATES) | set(reg.EXCLUDED) == set(installer.TASK_PROFILES)
    assert not set(TEMPLATES) & set(reg.EXCLUDED)


@pytest.mark.parametrize("profile", ["scan", "execute", "next-day"])
def test_scan_templates_pass_the_same_flags_as_their_bat(profile):
    # The .bat files are gitignored, so this runs only where they exist (the owner's machine).
    bat = installer.TASK_PROFILES[profile]["script"]
    if not bat.exists():
        pytest.skip(f"{bat.name} is not in this checkout")
    text = bat.read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if "scan.py" in ln).replace("%%", "%")
    cmd = TEMPLATES[profile]["commandTemplate"]
    assert _scan_flags(shlex.split(line, posix=False)) == _scan_flags(shlex.split(cmd, posix=False))
    assert ("--execute" in line) == (profile in reg.LIVE_PROFILES)


def test_nothing_places_an_order_unless_mode_says_so():
    for profile, t in TEMPLATES.items():
        cmd = t["commandTemplate"]
        assert "--execute" not in cmd, profile
        params = {p["key"]: p for p in t["parameters"]}
        if profile in reg.LIVE_PROFILES:
            assert "--mode {{mode}}" in cmd, profile
            assert params["mode"]["default"] == "preview", profile
            assert "REAL Kalshi orders" in t["description"], profile
        else:
            assert "mode" not in params, profile


def test_templates_are_valid_registry_v1():
    index = json.loads((reg.OUT / "index.json").read_bytes())
    ids = [e["id"] for e in index["templates"]]
    assert ids == [t["id"] for t in TEMPLATES.values()]
    assert all(i.startswith("edge-radar-") for i in ids)
    assert index["packs"][0]["templateIds"] == ids
    for t in TEMPLATES.values():
        assert len(t["trigger"]["cron"].split()) == 5
        used = {p.split("}}")[0] for p in t["commandTemplate"].split("{{")[1:]}
        assert used == {p["key"] for p in t["parameters"]}, t["id"]
    for path in reg.OUT.rglob("*.json"):
        assert b"\r\n" not in path.read_bytes(), path
