#!/usr/bin/env python
"""Render an Edge-Radar markdown report to HTML and email it -- no model involved.

    python scripts/schedulers/automation/render_report_email.py same-day
    python scripts/schedulers/automation/render_report_email.py daily-summary --dry-run out.html

Replaces the `claude -p` sessions in scripts/custom/Shell-Scripts/Run-Reports/*.sh
(2026-09-23 consolidation audit #6). Each of those spawned a headless Claude
session only to restyle a file a script had already written, and had to *ask*
the model not to drop columns from a real-money Orders table. Rendering is
deterministic here, so the tables are byte-exact by construction.

Picks the NEWEST report in the preset's folder modified within --max-age-hours,
never "the file named with today's date": report filenames carry the UTC date,
so a PT evening run (NextDay 20:30, Weekly-Analysis 23:45) writes tomorrow's
name, and a date match against the local clock misses it.

An execute preset (SCAN_LOGS) whose report is missing, or whose .bat recorded a
non-zero scan exit, sends a [FAILED] email with the log tail and exits 1 (ER-07).

Otherwise a missing report exits 2 without sending, except for presets with a scan log,
where no report is the normal zero-opportunity case and the email is
proof-of-life led by the log's execution outcome. (No preset uses one since the
Polymarket preset was removed 2026-09-29.)

Sends through send_report_email.py in this folder, the one send path (Resend
settings from app.config.EmailConfig, plus the delivery stamp).
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from markdown_it import MarkdownIt

REPO = Path(__file__).resolve().parents[3]
SENDER = Path(__file__).with_name("send_report_email.py")
SPORTS = "reports/Sports/schedulers"

# name -> (report folder, glob, subject, tag, email log, scan log or None)
PRESETS = {
    "daily-summary": (
        "reports/Performance",
        "daily_summary_*.md",
        "Edge-Radar | Daily Summary",
        "daily-summary",
        "email_daily_summary.log",
        None,
    ),
    "same-day": (
        f"{SPORTS}/same-day-executions",
        "*.md",
        "Edge-Radar | Same Day Execution Report",
        "same-day",
        "email_sameday.log",
        None,
    ),
    "same-day-late": (
        f"{SPORTS}/same-day-late-executions",
        "*.md",
        "Edge-Radar | Same-Day Late Execution Report",
        "same-day-late",
        "email_sameday_late.log",
        None,
    ),
    "nodatefilter-midday": (
        f"{SPORTS}/no-date-filter-midday-executions",
        "*.md",
        "Edge-Radar | NoDateFilter Midday Execution Report",
        "no-date-filter-midday",
        "email_nodatefilter_midday.log",
        None,
    ),
    "next-day": (
        f"{SPORTS}/next-day-executions",
        "*.md",
        "Edge-Radar | Next Day Edge Report",
        "next-day",
        "email_nextday.log",
        None,
    ),
    "weekly-futures": (
        "reports/Futures/schedulers",
        "*_futures_*.md",
        "Edge-Radar | Weekly Futures Execution Report",
        "weekly-futures",
        "email_futures.log",
        None,
    ),
    "weekly-analysis": (
        "reports/Performance",
        "betting_analysis_*_7d.md",
        "Edge-Radar | Weekly Performance Analysis",
        "weekly-analysis",
        "email_weekly_analysis.log",
        None,
    ),
    "drift-check": (
        "reports/Maintenance/drift",
        "drift_*.md",
        "Edge-Radar | Integration Drift Check",
        "drift-check",
        "email_drift_check.log",
        None,
    ),
}

# ER-07: each execute .bat appends its scan output and `exit code N` here. Every
# execute run writes a report, even with zero bets, so a missing report or a
# non-zero exit is a failed live run: send [FAILED] and exit 1. Task Scheduler's
# Last Result is the last action's code, so the old silent exit 2 hid it.
SCAN_LOGS = {
    "same-day": "logs/scan_same_day.log",
    "same-day-late": "logs/scan_same_day_late.log",
    "nodatefilter-midday": "logs/scan_nodatefilter_midday.log",
    "next-day": "logs/scan_next_day.log",
    "weekly-futures": "logs/scan_weekly_futures.log",
}

# Another report whose headline sections open a preset's email, so one Sunday
# email carries both (2026-10-27). The full lead report stays on disk.
LEADS = {
    "weekly-analysis": (
        "reports/Maintenance/betting-audit",
        "betting_audit_*.md",
        ("## Flags", "## Analysis", "## Recommended actions"),
    ),
}

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "Consolas,'SF Mono',Menlo,monospace"
CELL = "padding:6px 10px;border:1px solid #e5e7eb;font-size:13px;white-space:nowrap"
STYLES = {  # inline only -- Gmail/Outlook strip <style> blocks and CSS vars
    "h1": "margin:0 0 6px;font-size:22px;color:#111827",
    "h2": (
        "margin:26px 0 10px;font-size:17px;color:#0e7490;"
        "border-bottom:1px solid #e5e7eb;padding-bottom:4px"
    ),
    "h3": "margin:18px 0 8px;font-size:15px;color:#1f2937",
    "p": "margin:8px 0;font-size:14px;line-height:1.55",
    "ul": "margin:8px 0 8px 20px;padding:0;font-size:14px;line-height:1.55",
    "table": "border-collapse:collapse;margin:10px 0;width:auto",
    "th": CELL + ";background:#f3f4f6;font-weight:600;color:#111827",
    "td": CELL,
    "hr": "border:none;border-top:1px solid #e5e7eb;margin:20px 0",
    "code": (
        f"font-family:{MONO};font-size:12px;background:#f3f4f6;" "padding:1px 4px;border-radius:3px"
    ),
    "blockquote": "margin:10px 0;padding:6px 12px;border-left:3px solid #0891b2;color:#374151",
}

# html=False (ER-22): the commonmark preset passes raw HTML through, and report text
# includes Kalshi market titles and model output. Escaped, a stray <tag> shows as text.
_md = MarkdownIt("commonmark", {"html": False}).enable("table")


def md_to_html(text: str) -> str:
    """Markdown -> HTML with inline styles merged onto every styled tag."""
    tokens = _md.parse(text)

    def style(tok):
        extra = STYLES.get(tok.tag)
        if extra and (tok.nesting == 1 or tok.type in ("hr", "code_inline")):
            own = tok.attrGet("style")  # th/td carry text-align from the md table
            tok.attrSet("style", f"{extra};{own}" if own else extra)
        for child in tok.children or ():
            style(child)

    for tok in tokens:
        style(tok)
    return _md.renderer.render(tokens, _md.options, {})


def find_report(folder: Path, pattern: str, max_age_hours: float) -> Path | None:
    cutoff = time.time() - max_age_hours * 3600
    fresh = [p for p in folder.glob(pattern) if p.stat().st_mtime >= cutoff]
    return max(fresh, key=lambda p: p.stat().st_mtime, default=None)


def log_excerpt(path: Path, lines: int = 40) -> str:
    """The last run in a scan log, minus INFO chatter: portfolio state, gate
    verdicts, and the exit code the .bat appends."""
    raw = path.read_bytes().decode("utf-8", errors="replace").splitlines()
    banners = [i for i, ln in enumerate(raw) if ln.startswith("=====")]
    run = raw[banners[-1] + 1 :] if banners else raw
    kept = [ln for ln in run if " | INFO | " not in ln and ln.strip()]
    return "\n".join(kept[-lines:])


def last_exit(path: Path, max_age_hours: float) -> int | None:
    """The exit code the .bat recorded for its last run, or None if the log is
    missing, stale, or the last run recorded none."""
    if not path.exists() or path.stat().st_mtime < time.time() - max_age_hours * 3600:
        return None
    for ln in reversed(path.read_bytes().decode("utf-8", errors="replace").splitlines()):
        if ln.startswith("====="):
            return None
        if ln.startswith("exit code "):
            try:
                return int(ln.split()[2])
            except (IndexError, ValueError):
                return None
    return None


def failure(preset: str, max_age_hours: float) -> str | None:
    """Why an execute preset's run failed, or None if it didn't (or isn't one)."""
    if preset not in SCAN_LOGS:
        return None
    rc = last_exit(REPO / SCAN_LOGS[preset], max_age_hours)
    if rc:
        return f"scan exited {rc}"
    folder, pattern = PRESETS[preset][:2]
    if find_report(REPO / folder, pattern, max_age_hours) is None:
        return f"no report newer than {max_age_hours:g}h"
    return None


def build_failure(preset: str, reason: str) -> tuple[str, str]:
    subject, log = PRESETS[preset][2], REPO / SCAN_LOGS[preset]
    excerpt = log_excerpt(log) if log.exists() else f"(no scan log at {SCAN_LOGS[preset]})"
    md_text = f"# FAILED: {subject}\n\n**{reason}**\n\n## Scan log, last run\n\n{excerpt}\n"
    parts = [
        f"<h1 style=\"{STYLES['h1']};color:#b91c1c\">FAILED: {html.escape(subject)}</h1>",
        f"<p style=\"{STYLES['p']}\"><strong>{html.escape(reason)}</strong></p>",
        f"<h2 style=\"{STYLES['h2']}\">Scan log, last run</h2>",
        f'<pre style="font-family:{MONO};font-size:12px;background:#f9fafb;'
        f'border:1px solid #e5e7eb;padding:10px;white-space:pre-wrap">'
        f"{html.escape(excerpt)}</pre>",
    ]
    return wrap(parts, SCAN_LOGS[preset]), md_text


def wrap(parts: list[str], source: str) -> str:
    footer = (
        f"<strong>Edge-Radar</strong> &middot; automation fleet &middot; "
        f"{html.escape(source)} &middot; {datetime.now():%Y-%m-%d %H:%M}"
    )
    return (
        f'<!DOCTYPE html><html><body style="font-family:{FONT};max-width:960px;margin:0 auto;'
        f'padding:20px;background:#fafaf9;color:#1f2937">'
        f'<div style="background:#fff;padding:24px;border-radius:10px;border:1px solid #e5e7eb;'
        f'overflow-x:auto">{"".join(parts)}'
        f'<div style="margin-top:28px;padding-top:12px;border-top:1px solid #e5e7eb;'
        f'color:#888;font-size:12px">{footer}</div></div></body></html>'
    )


def lead_sections(text: str, headings: tuple[str, ...]) -> str:
    """Title, status line, and the named `## ` sections of a markdown report."""
    lines = text.splitlines()
    out, keep = lines[:1], False
    for ln in lines[1:]:
        if ln.startswith("## "):
            keep = ln.strip() in headings
        if keep or ln.startswith("**Status:"):
            out.append(ln)
    return "\n".join(out).strip()


_MODE_LINE = re.compile(r"^\*\*((?:LIVE|DRY RUN|DEMO|PREVIEW)[^*\n]*)\*\*(.*)$", re.M)


def with_mode(subject: str, text: str) -> str:
    """ER-12: put the execution report's mode line in the subject.

    "Edge-Radar | Same Day Execution Report | LIVE · REAL MONEY · PROD · 0 placed · 3 blocked"
    """
    m = _MODE_LINE.search(text)
    return f"{subject} | {m[1]}{m[2]}".strip() if m else subject


def build(preset: str, max_age_hours: float) -> tuple[str, str] | None:
    folder, pattern, subject, _tag, _log, scan_log = PRESETS[preset]
    report = find_report(REPO / folder, pattern, max_age_hours)
    if report is None and scan_log is None:
        return None

    md_text, parts = "", []
    if report is not None and preset in LEADS:
        lead_folder, lead_pattern, headings = LEADS[preset]
        lead = find_report(REPO / lead_folder, lead_pattern, max_age_hours)
        if lead is not None:
            body = lead_sections(lead.read_bytes().decode("utf-8", errors="replace"), headings)
            body += f"\n\n_Full audit: `{lead.relative_to(REPO).as_posix()}`_\n\n---\n\n"
            parts.append(md_to_html(body))
            md_text += body
    if scan_log:
        excerpt = log_excerpt(REPO / scan_log)
        heading = "Execution outcome" if report else "No opportunities surfaced -- scan log"
        parts.append(
            f"<h2 style=\"{STYLES['h2']}\">{heading}</h2>"
            f'<pre style="font-family:{MONO};font-size:12px;background:#f9fafb;'
            f'border:1px solid #e5e7eb;padding:10px;white-space:pre-wrap">'
            f"{html.escape(excerpt)}</pre>"
        )
        md_text = f"## {heading}\n\n{excerpt}\n\n"
    if report:
        body = report.read_bytes().decode("utf-8", errors="replace")
        parts.append(md_to_html(body))
        md_text += body

    return wrap(parts, report.name if report else scan_log), md_text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("preset", choices=sorted(PRESETS))
    ap.add_argument(
        "--max-age-hours",
        type=float,
        default=3.0,
        help="Ignore reports older than this (default 3).",
    )
    ap.add_argument(
        "--dry-run", metavar="HTML_OUT", help="Write the HTML here and exit without sending."
    )
    args = ap.parse_args()

    _folder, _pattern, subject, tag, email_log, _scan = PRESETS[args.preset]
    log = REPO / "logs" / email_log
    log.parent.mkdir(exist_ok=True)

    def note(msg: str) -> None:
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {args.preset} | {msg}"
        print(line)
        if not args.dry_run:
            with log.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    reason = failure(args.preset, args.max_age_hours)
    if reason:
        page, text = build_failure(args.preset, reason)
        subject = f"[FAILED] {subject}"
        note(f"FAILED run: {reason}")
    else:
        built = build(args.preset, args.max_age_hours)
        if built is None:
            note(f"no report newer than {args.max_age_hours}h -- not sending")
            return 2
        page, text = built
        subject = with_mode(subject, text)

    if args.dry_run:
        Path(args.dry_run).write_text(page, encoding="utf-8")
        note(f"dry run -> {args.dry_run}")
        return 0

    tmp = REPO / ".claude" / "temp"
    tmp.mkdir(parents=True, exist_ok=True)
    html_file, text_file = tmp / f"{tag}.html", tmp / f"{tag}.txt"
    html_file.write_text(page, encoding="utf-8")
    text_file.write_text(text, encoding="utf-8")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SENDER),
                "--subject",
                subject,
                "--html-file",
                str(html_file),
                "--text-file",
                str(text_file),
                "--tag",
                tag,
            ],
            capture_output=True,
            text=True,
        )
    finally:
        html_file.unlink(missing_ok=True)
        text_file.unlink(missing_ok=True)
    note(f"send exit {proc.returncode}: {(proc.stdout + proc.stderr).strip()}")
    return proc.returncode or (1 if reason else 0)


if __name__ == "__main__":
    raise SystemExit(main())
