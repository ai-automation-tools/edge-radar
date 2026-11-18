"""ER-28: logs/ stays bounded."""

from datetime import date

from prune_logs import prune


def test_prune_drops_old_dated_logs_and_trims_fixed_ones(tmp_path):
    for name in ("edge_detector_2026-01-01.log", "edge_detector_2026-08-20.log", "notes.txt"):
        (tmp_path / name).write_text("x\n")
    big = tmp_path / "clv_capture.log"
    big.write_bytes(b"".join(b"line %07d\n" % i for i in range(120_000)))  # ~1.4 MB
    small = tmp_path / "scan_same_day.log"
    small.write_text("===== run\nok\n")

    assert prune(tmp_path, keep_days=90, max_mb=1, today=date(2026, 11, 18)) == (1, 1)

    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "clv_capture.log",
        "edge_detector_2026-08-20.log",
        "notes.txt",
        "scan_same_day.log",
    ]
    data = big.read_bytes()
    assert len(data) <= 1024 * 1024 // 5
    assert data.startswith(b"line ") and data.endswith(b"line 0119999\n")
    assert small.read_text() == "===== run\nok\n"
