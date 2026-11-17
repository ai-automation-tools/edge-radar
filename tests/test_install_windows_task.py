"""`install_windows_task.py status` lists every task in the folder, not just profiles (R24c)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_PATH = ROOT / "scripts" / "schedulers" / "automation" / "install_windows_task.py"
_spec = importlib.util.spec_from_file_location("_install_windows_task_status", _PATH)
installer = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = installer
_spec.loader.exec_module(installer)


def test_status_lists_hand_built_tasks_in_folder(monkeypatch, capsys):
    monkeypatch.setattr(installer, "TASK_FOLDER", "Org\\Live")
    registered = {
        "\\Org\\Live\\Hourly-Settle",  # a profile leaf (settle)
        "\\Org\\Live\\All-Sports-SameDay-Execution",  # hand-built, not a profile
        "\\Other\\Unrelated",
    }

    def fake(args, check=True):
        if args[:2] == ["/Query", "/FO"]:  # the list-everything query
            out = "".join(f'"{p}","N/A","Ready"\n' for p in sorted(registered))
            return subprocess.CompletedProcess(args, 0, out, "")
        tn = args[2]
        known = ("\\" + tn.lstrip("\\")) in registered
        return subprocess.CompletedProcess(
            args, 0 if known else 1, "Status: Ready\n" if known else "", ""
        )

    monkeypatch.setattr(installer, "_run_schtasks", fake)
    installer.status()
    out = capsys.readouterr().out

    assert "Other tasks in \\Org\\Live\\ (not managed by this script): 1" in out
    assert "All-Sports-SameDay-Execution" in out
    assert "Unrelated" not in out
    assert "No Edge-Radar tasks installed" not in out
