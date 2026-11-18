"""ER-18: every script entry point imports in a fresh clone.

A fresh clone has no `.venv/Lib/site-packages/edge_radar.pth`, so running
`python scripts/<dir>/<name>.py` puts only that script's own folder on sys.path.
Each entry point is loaded in a child interpreter started with `-S`, with
site-packages passed through PYTHONPATH: packages resolve, `.pth` files don't
run. Module-level code runs; `main()` doesn't.
"""

import os
import re
import subprocess
import sys
import sysconfig
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_GUARD = re.compile(r"""^if __name__ == ["']__main__["']""", re.M)

# Not yet black/flake8 clean, so any edit reformats the whole file. They get
# the sys.path block with the lint cleanup (ER-21); remove them here then.
KNOWN_BROKEN = {
    "scripts/kalshi/model_calibration.py",
    "scripts/kalshi/risk_check.py",
    "scripts/prediction/prediction_scanner.py",
}

# A missing third-party package (Pillow, for make_favicon.py) is a requirements
# question, not a sys.path one: only a project module that can't be found fails.
PROJECT_MODULES = {p.stem for p in (ROOT / "scripts").rglob("*.py")} | {"app"}
_MISSING = re.compile(r"No module named '(\w+)")

_LOAD = (
    "import importlib.util as u, os, sys; p = sys.argv[1]; "
    "sys.path.insert(0, os.path.dirname(p)); "
    "s = u.spec_from_file_location('_entry', p); m = u.module_from_spec(s); "
    "sys.modules['_entry'] = m; s.loader.exec_module(m)"
)


def _entry_points() -> list[Path]:
    return sorted(
        p
        for p in (ROOT / "scripts").rglob("*.py")
        if MAIN_GUARD.search(p.read_text(encoding="utf-8"))
    )


def _path_failure(r: subprocess.CompletedProcess) -> bool:
    if r.returncode == 0:
        return False
    missing = _MISSING.search(r.stderr)
    return not missing or missing[1] in PROJECT_MODULES


def test_entry_points_import_without_venv_pth(tmp_path):
    site = os.pathsep.join(dict.fromkeys(sysconfig.get_paths()[k] for k in ("purelib", "platlib")))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    env.update(PYTHONPATH=site, DRY_RUN="true", PYTHONIOENCODING="utf-8")

    def load(path: Path):
        r = subprocess.run(
            [sys.executable, "-S", "-c", _LOAD, str(path)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return path.relative_to(ROOT).as_posix(), r

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(pool.map(load, _entry_points()))

    assert "scripts/kalshi/kalshi_settler.py" in results, "entry-point discovery found nothing"
    broken = {rel for rel, r in results.items() if _path_failure(r)}
    detail = {rel: results[rel].stderr.strip().splitlines()[-1:] for rel in broken - KNOWN_BROKEN}
    assert not detail, f"entry points that fail without the venv .pth: {detail}"
    fixed = KNOWN_BROKEN - broken
    assert not fixed, f"now import cleanly, drop them from KNOWN_BROKEN: {sorted(fixed)}"
