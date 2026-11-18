"""ER-28: the shadow book is one JSONL file per month, and the old single file migrates."""

import json

import pytest

import shadow_book as sb


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(sb, "SHADOW_DIR", tmp_path / "shadow_book")
    monkeypatch.setattr(sb, "LEGACY_LOG", tmp_path / "shadow_book.json")
    monkeypatch.setattr(sb, "_on_disk", {})
    return tmp_path


def _row(t, month="2026-10"):
    return {"ticker": t, "side": "yes", "observed_at": f"{month}-05T12:00:00+00:00", "won": None}


def test_rows_split_by_month_and_round_trip(store):
    rows = [_row("A", "2026-10"), _row("B", "2026-11"), _row("C", "2026-11"), {"ticker": "D"}]
    sb.save_shadow(rows)
    names = sorted(p.name for p in (store / "shadow_book").iterdir())
    assert names == ["2026-10.jsonl", "2026-11.jsonl", "undated.jsonl"]
    sb._on_disk.clear()
    assert sorted(r["ticker"] for r in sb.load_shadow()) == ["A", "B", "C", "D"]


def test_only_changed_months_are_rewritten(store):
    sb.save_shadow([_row("A", "2026-10"), _row("B", "2026-11")])
    sb._on_disk.clear()
    rows = sb.load_shadow()
    oct_file = store / "shadow_book" / "2026-10.jsonl"
    before = oct_file.stat().st_mtime_ns
    rows[1]["won"] = True  # settle touches November only
    sb.save_shadow(rows)
    assert oct_file.stat().st_mtime_ns == before
    nov = (store / "shadow_book" / "2026-11.jsonl").read_text(encoding="utf-8")
    assert json.loads(nov.splitlines()[0])["won"] is True


def test_legacy_file_is_read_then_migrated_on_first_save(store):
    legacy = store / "shadow_book.json"
    legacy.write_text(json.dumps([_row("A"), _row("B", "2026-11")]), encoding="utf-8")
    rows = sb.load_shadow()
    assert [r["ticker"] for r in rows] == ["A", "B"]
    sb.save_shadow(rows)
    assert not legacy.exists() and (store / "shadow_book.json.migrated").exists()
    sb._on_disk.clear()
    assert [r["ticker"] for r in sb.load_shadow()] == ["A", "B"]


def test_a_bad_line_is_skipped_not_fatal(store):
    d = store / "shadow_book"
    d.mkdir()
    (d / "2026-10.jsonl").write_text(json.dumps(_row("A")) + "\n{oops\n", encoding="utf-8")
    assert [r["ticker"] for r in sb.load_shadow()] == ["A"]
