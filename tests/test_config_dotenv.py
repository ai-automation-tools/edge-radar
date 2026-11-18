"""ER-45: get_config() loads the repo-root .env itself, so import order doesn't matter."""

import os
import subprocess
import sys
from pathlib import Path


def test_config_loads_dotenv_when_imported_first(tmp_path):
    (tmp_path / ".env").write_text("KALSHI_FEE_RATE=0.05\n", encoding="utf-8")
    # conftest disables python-dotenv for the test process; this child needs it on.
    drop = ("KALSHI_FEE_RATE", "EDGE_RADAR_PROFILE", "PYTHON_DOTENV_DISABLED")
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env["PROJECT_ROOT"] = str(tmp_path)
    code = "from app.config import get_config; print(get_config().gates.kalshi_fee_rate)"
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parent.parent,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "0.05"
