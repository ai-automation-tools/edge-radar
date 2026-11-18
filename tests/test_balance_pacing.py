"""K1: balance reads are spaced >= 1 s apart (Kalshi's 1 req/s balance bucket)."""

import kalshi_client as kc


class _Clock:
    def __init__(self):
        self.t = 1000.0

    def monotonic(self):
        return self.t

    def sleep(self, s):
        self.t += s


def _client(monkeypatch, clock, calls, fail_at=None):
    c = kc.KalshiClient.__new__(kc.KalshiClient)  # no keys, no network
    c.subaccount = 0

    def fake_get(path, params=None):
        calls.append((clock.t, path, dict(params or {})))
        clock.t += 0.05  # the request itself
        if fail_at is not None and len(calls) == fail_at:
            raise kc.KalshiAPIError(429, "slow down")
        return {"balance_dollars": "12.50", "balance": 1250, "portfolio_value": 0}

    monkeypatch.setattr(c, "_get", fake_get)
    monkeypatch.setattr(kc, "time", clock)
    monkeypatch.setattr(kc, "_balance_last", [float("-inf")])
    return c


def test_a_burst_of_balance_reads_never_exceeds_one_per_second(monkeypatch):
    clock, calls = _Clock(), []
    c = _client(monkeypatch, clock, calls)
    c.get_balance()
    c.get_shard_balance(3)
    c.get_shard_balance(0)
    c.get_balance_dollars()
    starts = [t for t, _, _ in calls]
    assert len(starts) == 4
    assert all(b - a >= kc.BALANCE_MIN_INTERVAL - 1e-9 for a, b in zip(starts, starts[1:]))
    assert calls[1][2] == {"subaccount": 0, "exchange_index": 3}


def test_the_first_read_does_not_wait_and_a_failed_read_still_counts(monkeypatch):
    clock, calls = _Clock(), []
    c = _client(monkeypatch, clock, calls, fail_at=1)
    try:
        c.get_balance()
    except kc.KalshiAPIError:
        pass
    assert calls[0][0] == 1000.0  # no wait on a cold start
    c.get_balance()
    assert calls[1][0] - calls[0][0] >= kc.BALANCE_MIN_INTERVAL
