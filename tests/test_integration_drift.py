"""integration_drift.probe_series: flags the M1 failure class, passes clean data."""

from integration_drift import FAIL, OK, WARN, probe_series, rules_template


def _event(away, home, commence="2026-10-04T17:00:00Z"):
    return {"away_team": away, "home_team": home, "commence_time": commence, "bookmakers": []}


def _game(ticker, team, rules):
    return {
        "ticker": ticker,
        "yes_sub_title": team,
        "rules_primary": rules,
        "yes_ask_dollars": "0.50",
        "no_ask_dollars": "0.51",
        "yes_bid_dollars": "0.49",
    }


EVENTS = [
    _event("Denver Broncos", "San Francisco 49ers"),
    _event("Detroit Lions", "Carolina Panthers"),
]


def _slate(rules_fmt):
    out = []
    for i in range(3):
        out.append(
            _game(
                f"KXNFLGAME-26OCT04DENSF-SF{i}",
                "San Francisco",
                rules_fmt.format(a="Denver", b="San Francisco"),
            )
        )
        out.append(
            _game(
                f"KXNFLGAME-26OCT04DETCAR-DET{i}",
                "Detroit",
                rules_fmt.format(a="Detroit", b="Carolina"),
            )
        )
    return out


def test_clean_slate_is_ok():
    r = probe_series(
        "KXNFLGAME", _slate("If X wins the {a} vs {b} professional football game"), EVENTS
    )
    assert r["level"] == OK
    assert r["parse_rate"] == 1.0 and r["match_rate"] == 1.0


def test_unknown_wording_fails_parse():
    # The M1 shape: a league word the extractor does not know -> no teams at all.
    r = probe_series(
        "KXNFLGAME", _slate("If X wins the {a} vs {b} Gridiron Football contest"), EVENTS
    )
    assert r["level"] == FAIL
    assert r["parse_rate"] == 0.0
    assert r["examples"]["unparsed"]


def test_missing_field_fails():
    slate = _slate("If X wins the {a} vs {b} professional football game")
    del slate[0]["yes_ask_dollars"]
    assert probe_series("KXNFLGAME", slate, EVENTS)["level"] == FAIL


def test_unposted_games_are_not_misses():
    r = probe_series("KXNFLGAME", _slate("If X wins the {a} vs {b} professional football game"), [])
    assert r["measurable"] == 0 and r["match_rate"] is None and r["level"] == OK


def test_unmatched_team_warns_or_fails():
    # Event pairs, but the YES team resolves to neither side (the spread-suffix shape).
    slate = [
        _game(
            f"KXNFLGAME-26OCT04DENSF-X{i}",
            "DEN wins by",
            "If X wins the Denver vs San Francisco professional game",
        )
        for i in range(6)
    ]
    assert probe_series("KXNFLGAME", slate, EVENTS)["level"] in (WARN, FAIL)


def test_rules_template_abstracts_names_and_numbers():
    m = {
        "rules_primary": "If DET Lions wins by more than 7.5 points in the DET Lions vs "
        "CAR Panthers Pro Football game originally scheduled for Oct 4, 2026, "
        "then the market resolves to Yes."
    }
    t = rules_template(m, ("DET Lions", "CAR Panthers"), "DET Lions")
    assert "DET" not in t and "7.5" not in t and "<DATE>" in t
    assert t.endswith("originally scheduled for <DATE>")


def test_autofix_changed_keeps_first_path_intact(monkeypatch):
    import drift_autofix as da

    # Porcelain lines start with a space; a strip() once ate "s" of "scripts".
    monkeypatch.setattr(
        da, "_git", lambda *a, **k: " M scripts/kalshi/edge_detector.py\n?? tests/test_new.py"
    )
    assert da._changed(None) == [
        ("M", "scripts/kalshi/edge_detector.py"),
        ("??", "tests/test_new.py"),
    ]


def test_autofix_allowlist():
    from drift_autofix import ALLOWED

    for ok in ("scripts/kalshi/edge_detector.py", "tests/test_edge_detection.py"):
        assert ALLOWED.match(ok)
    for bad in (
        "scripts/kalshi/kalshi_executor.py",
        "scripts/kalshi/kalshi_client.py",  # ER-04: it places orders
        "scripts/kalshi/integration_drift.py",
        "app/config.py",
        ".env",
        "scripts/schedulers/maintenance/drift_check.bat",
    ):
        assert not ALLOWED.match(bad)


# ── ER-04: the auto-fix's containment ───────────────────────────────────────


def test_tree_env_carries_no_credentials(monkeypatch):
    import drift_autofix as da

    for k in (
        "KALSHI_API_KEY",
        "KALSHI_PRIVATE_KEY_PATH",
        "RESEND_API_KEY",
        "GH_TOKEN",
        "AGENT_CLI",
    ):
        monkeypatch.setenv(k, "planted")
    env = da._tree_env()
    assert not {"KALSHI_API_KEY", "KALSHI_PRIVATE_KEY_PATH", "RESEND_API_KEY", "GH_TOKEN"} & set(
        env
    )
    assert (
        "AGENT_CLI" not in env and env["DRY_RUN"] == "true" and "PATH" in {k.upper() for k in env}
    )


def test_planted_test_in_tree_sees_no_key(tmp_path, monkeypatch):
    """The audit's acceptance check: code run by _in_tree finds no Kalshi key."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    import drift_autofix as da

    monkeypatch.setenv("KALSHI_API_KEY", "planted")
    (tmp_path / "planted.py").write_text(
        "import os, sys\n"
        "ok = os.environ.get('KALSHI_API_KEY') is None and os.environ.get('DRY_RUN') == 'true'\n"
        "sys.exit(0 if ok else 3)\n"
    )
    root = Path(da.__file__).resolve().parents[2]
    env = da._tree_env()
    env["PYTHONPATH"] = os.pathsep.join(str(root / d) for d in ("scripts/shared", "scripts/kalshi"))
    res = subprocess.run(
        [sys.executable, da.__file__, "--in-tree", str(tmp_path), "planted.py"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr[-800:]


def test_fix_session_reads_only_inside_the_worktree():
    import drift_autofix as da

    reads = [t for t in da.FIX_TOOLS if t.split("(")[0] in ("Read", "Grep", "Glob")]
    assert sorted(reads) == ["Glob(./**)", "Grep(./**)", "Read(./**)"]
    assert "{analysis}" not in da.FIX_PROMPT  # the web-capable analysis never reaches it


def test_probe_reads_markets_unsigned(monkeypatch):
    import integration_drift as idr

    seen = {}

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"markets": [], "cursor": ""}

    def fake_get(url, params=None, timeout=None, **kw):
        seen.update(url=url, params=params, kw=kw)
        return _Resp()

    monkeypatch.setattr(idr.requests, "get", fake_get)
    idr.fetch_series(idr.PublicMarkets("https://example.invalid/v2/"), "KXNBAGAME")
    assert seen["url"] == "https://example.invalid/v2/markets"
    assert "cursor" not in seen["params"] and seen["params"]["series_ticker"] == "KXNBAGAME"
    assert "headers" not in seen["kw"]


def test_college_in_a_real_team_name_is_not_filler():
    from integration_drift import SUSPECT_WORDS

    assert not SUSPECT_WORDS.search("Boston College")
    assert SUSPECT_WORDS.search("Boston College Football")
