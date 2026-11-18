"""ER-27: the scheduled-task wrappers and the email sender are tracked and portable."""

import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import importlib.util

import pytest

from app.config import EmailConfig

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    path = ROOT / "scripts/schedulers/automation" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rre, sre = _load("render_report_email"), _load("send_report_email")


def _tracked(pattern: str) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", pattern], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [ROOT / p for p in out]


WRAPPERS = _tracked("scripts/schedulers/*.bat")


def test_the_scheduled_wrappers_are_tracked():
    names = {p.name for p in WRAPPERS}
    for live in (
        "same_day_execute.bat",
        "same_day_execute_late.bat",
        "next_day_execute.bat",
        "no_date_filter_execution_midday.bat",
        "weekly_futures_execute.bat",
        "clv_capture.bat",
        "reconcile.bat",
    ):
        assert live in names
    assert (ROOT / "scripts/schedulers/run-hidden.vbs") in _tracked("scripts/schedulers/*.vbs")


@pytest.mark.parametrize("path", WRAPPERS, ids=lambda p: p.name)
def test_wrapper_is_portable(path):
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    assert not re.search(r"\b[A-Za-z]:\\", text), "absolute drive path; use %~dp0"
    assert "%~dp0" in text, "should cd relative to its own folder"
    assert b"\n" not in raw.replace(b"\r\n", b""), "cmd.exe wants CRLF (.gitattributes)"
    assert "Unit size:" not in text, "the scan.py flags are the only copy of the sizing"


def _cfg(**kw):
    base = dict(notify_email="ops@example.com", resend_from="Bot <bot@example.com>")
    return EmailConfig(**{**base, "resend_api_key": "re_test", **kw})  # pragma: allowlist secret


def test_payload_needs_a_recipient_and_a_sender():
    with pytest.raises(RuntimeError, match="NOTIFY_EMAIL"):
        sre.build_payload(_cfg(), to=[], subject="s", html="h", text="", tags=[])
    with pytest.raises(RuntimeError, match="RESEND_FROM"):
        sre.build_payload(
            _cfg(resend_from=""), to=["a@b.c"], subject="s", html="h", text="", tags=[]
        )


def test_payload_shape():
    p = sre.build_payload(
        _cfg(),
        to=["ops@example.com"],
        subject="S",
        html="<p>h</p>",
        text="t",
        tags=["daily summary"],
    )
    assert p["from"] == "Bot <bot@example.com>"
    assert p["reply_to"] == "ops@example.com"
    assert p["tags"] == [{"name": "tag1", "value": "daily_summary"}]


def test_send_posts_and_stamps(tmp_path, monkeypatch):
    sent = {}

    def fake_post(url, headers, data, timeout):
        sent.update(url=url, headers=headers, payload=json.loads(data))
        return SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"id": "abc"})

    monkeypatch.setattr(sre.requests, "post", fake_post)
    monkeypatch.setattr(sre, "get_config", lambda: SimpleNamespace(email=_cfg()))
    monkeypatch.setattr(sre, "LOG_DIR", tmp_path)
    body = tmp_path / "r.html"
    body.write_bytes(b"caf\xe9 \x97")  # cp1252 bytes (e-acute, em dash): must still send

    assert sre.main(["--subject", "Hi", "--html-file", str(body), "--tag", "t"]) == 0
    assert sent["url"] == sre.ENDPOINT
    assert sent["headers"]["Authorization"] == "Bearer re_test"
    assert sent["payload"]["to"] == ["ops@example.com"]
    assert json.loads((tmp_path / "last_email_sent.json").read_text())["id"] == "abc"


def test_send_fails_without_settings(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sre, "get_config", lambda: SimpleNamespace(email=EmailConfig()))
    monkeypatch.setattr(sre, "LOG_DIR", tmp_path)
    body = tmp_path / "r.txt"
    body.write_text("x")
    assert sre.main(["--subject", "Hi", "--text-file", str(body)]) == 1
    assert "NOTIFY_EMAIL" in capsys.readouterr().err
    assert not (tmp_path / "last_email_sent.json").exists()


def test_render_sends_through_the_tracked_sender():
    assert rre.SENDER == Path(sre.__file__).resolve()
    assert "custom" not in rre.SENDER.parts
