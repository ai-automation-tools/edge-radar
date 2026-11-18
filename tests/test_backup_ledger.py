"""ER-08: the ledger backup zips every history file, round-trips, and prunes."""

import json
import os
import time
import zipfile

import backup_ledger as bl
import trade_log


def _seed(tmp_path, monkeypatch, trades='[{"trade_id": "a"}]'):
    monkeypatch.setattr(bl.paths, "DATA_DIR", tmp_path / "data")
    (tmp_path / "data" / "history").mkdir(parents=True)
    (tmp_path / "data" / "history" / "shadow_book.json").write_text("[]")
    trade_log.TRADE_LOG_PATH.write_text(trades)
    trade_log.SETTLEMENT_LOG_PATH.write_text("[]")


def test_zip_holds_every_file_and_restores_byte_exact(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    out, bad = bl.backup(tmp_path / "dest", 30)
    assert bad == []
    restored = tmp_path / "restore"
    zipfile.ZipFile(out).extractall(restored)
    assert sorted(p.name for p in restored.iterdir()) == [
        "kalshi_settlements.json",
        "kalshi_trades.json",
        "shadow_book.json",
    ]
    assert (restored / "kalshi_trades.json").read_bytes() == trade_log.TRADE_LOG_PATH.read_bytes()
    assert json.loads((restored / "kalshi_trades.json").read_text()) == [{"trade_id": "a"}]


def test_old_zips_are_pruned_and_others_left_alone(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    dest = tmp_path / "dest"
    dest.mkdir()
    old, recent, foreign = (
        dest / f"{bl.PREFIX}old.zip",
        dest / f"{bl.PREFIX}new.zip",
        dest / "keep.zip",
    )
    for p in (old, recent, foreign):
        p.write_bytes(b"x")
    month_ago = time.time() - 31 * 86400
    os.utime(old, (month_ago, month_ago))
    os.utime(foreign, (month_ago, month_ago))
    out, _ = bl.backup(dest, 30)
    assert not old.exists() and recent.exists() and foreign.exists() and out.exists()


def test_corrupt_source_is_still_kept_but_flagged(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, trades='[{"trade_id": ')
    out, bad = bl.backup(tmp_path / "dest", 30)
    assert out.exists() and bad == ["kalshi_trades.json"]


def test_monthly_shadow_files_are_zipped_under_their_folder(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    hist = tmp_path / "data" / "history"
    (hist / "shadow_book.json").unlink()
    (hist / "shadow_book").mkdir()
    (hist / "shadow_book" / "2026-11.jsonl").write_text('{"ticker": "A"}\n')
    (hist / "shadow_book" / "2026-10.jsonl").write_text("{broken\n")
    out, bad = bl.backup(tmp_path / "dest", 30)
    names = zipfile.ZipFile(out).namelist()
    assert "shadow_book/2026-11.jsonl" in names and "shadow_book/2026-10.jsonl" in names
    assert bad == ["shadow_book/2026-10.jsonl"]
