"""Email an Edge-Radar report through Resend (one REST POST, no SDK).

    python send_report_email.py --subject S --html-file a.html --text-file a.txt --tag t
    python send_report_email.py --check   # key + domain probe, sends nothing

The one send path for render_report_email.py (ER-27: it used to live in the
untracked scripts/custom/). Settings come from app.config.EmailConfig:
NOTIFY_EMAIL (recipient), RESEND_FROM (sender), RESEND_REPLY_TO (optional) and
RESEND_API_KEY (OS environment or .env). None of them has a default.

Every send is stamped to logs/last_email_sent.json and logs/email_sends.jsonl:
alert on a stale stamp, because "can I authenticate" is not "did mail go out".
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from app.config import get_config  # noqa: E402

LOG_DIR = REPO / "logs"
ENDPOINT = "https://api.resend.com/emails"
DOMAINS = "https://api.resend.com/domains"


def sanitize_tag(value: str) -> str:
    """Resend answers a tag value outside [A-Za-z0-9_-] with a 422 that fails the
    whole send, not just the tag."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(value))[:200] or "untagged"


def read_report(path: str) -> str:
    """Read a report that may not be UTF-8.

    Scan logs written through PowerShell 5.1 or Windows Python can be cp1252; a
    strict UTF-8 read once failed a send on one em dash. cp1252 decodes almost
    every byte, so it is the fallback before replacement characters.
    """
    raw = Path(path).read_bytes()
    for encoding in ("utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def build_payload(cfg, *, to, subject, html, text, tags) -> dict:
    if not to:
        raise RuntimeError("NOTIFY_EMAIL is not set (or pass --to).")
    if not cfg.resend_from:
        raise RuntimeError("RESEND_FROM is not set.")
    payload = {"from": cfg.resend_from, "to": to, "subject": subject}
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    reply_to = cfg.resend_reply_to or cfg.notify_email
    if reply_to:
        payload["reply_to"] = reply_to
    if tags:
        payload["tags"] = [
            {"name": f"tag{i}", "value": sanitize_tag(t)} for i, t in enumerate(tags, start=1)
        ]
    return payload


def _auth(cfg) -> dict:
    if not cfg.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not set.")
    return {"Authorization": f"Bearer {cfg.resend_api_key}"}


def _stamp(record: dict) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = json.dumps(record, indent=2)
        (LOG_DIR / "last_email_sent.json").write_text(stamp, encoding="utf-8")
        with (LOG_DIR / "email_sends.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except OSError as exc:  # never fail a delivered email over a logging problem
        print(f"WARN: could not write the delivery stamp: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Email an Edge-Radar report through Resend.")
    ap.add_argument("--to", action="append", help="Recipient (repeatable). Default: NOTIFY_EMAIL.")
    ap.add_argument("--subject", help="Subject line. Required unless --check.")
    ap.add_argument("--html-file", default="", help="HTML body file.")
    ap.add_argument("--text-file", default="", help="Plain-text body file.")
    ap.add_argument("--tag", action="append", default=[], help="Tag value, e.g. daily-summary.")
    ap.add_argument("--check", action="store_true", help="Probe the key and domains; send nothing.")
    args = ap.parse_args(argv)

    load_dotenv(REPO / ".env")
    cfg = get_config().email
    try:
        if args.check:
            resp = requests.get(DOMAINS, headers=_auth(cfg), timeout=30)
            if resp.status_code >= 300:
                raise RuntimeError(f"Resend HTTP {resp.status_code}: {resp.text[:300]}")
            domains = (resp.json() or {}).get("data", [])
            for d in domains:
                print(f"{d.get('status', '?'):>10}  {d.get('name')}")
            return 0 if any(d.get("status") == "verified" for d in domains) else 1

        if not args.subject:
            ap.error("--subject is required (unless --check)")
        html = read_report(args.html_file) if args.html_file else ""
        text = read_report(args.text_file) if args.text_file else ""
        if not (html or text):
            ap.error("supply --html-file, --text-file, or both")

        to = args.to or ([cfg.notify_email] if cfg.notify_email else [])
        tags = args.tag or ["edge-radar"]
        payload = build_payload(cfg, to=to, subject=args.subject, html=html, text=text, tags=tags)
        resp = requests.post(
            ENDPOINT,
            headers={**_auth(cfg), "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60,
        )
        if resp.status_code >= 300:
            raise RuntimeError(f"Resend HTTP {resp.status_code}: {resp.text[:500]}")

        record = {
            "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "subject": args.subject,
            "to": to,
            "tags": tags,
            "provider": "resend",
            "id": (resp.json() if resp.content else {}).get("id"),
        }
        _stamp(record)
        print(json.dumps({"status": "sent", **record}, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 -- the message is the whole point here
        failure = {"status": "failed", "provider": "resend", "error": str(exc)}
        print(json.dumps(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
