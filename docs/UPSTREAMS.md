# Upstreams

Every external service and library Edge-Radar depends on, what the code assumes about each,
and where to check whether that assumption still holds. The biweekly **Edge-Radar Upstream
Check** routine (`upstream/auto-*` PRs) works from this file. Keep it current by hand too:
a new API client is a new row.

**Money path** rows touch order placement, fills, settlement, or cash. The routine never
changes code on them. It opens a ROADMAP item and flags it in its PR body.

**Last checked** is filled in by the routine, and only with a date it actually read the
source. `—` means never checked.

## Execution venues (money path)

| Upstream | What the code assumes | Code | Check at | Last checked |
|:---|:---|:---|:---|:---|
| **Kalshi Trade API v2** | Base `api.elections.kalshi.com/trade-api/v2`; RSA-PSS request signing (create keys as RSA: the web dialog defaults to Ed25519, which the client cannot sign; ROADMAP M3); `GET /portfolio/balance` allows 1 request per second, so every balance read in a process is spaced 1 s apart (K1); fills and positions arrive as fixed-point strings (`fill_count_fp`, `position_fp`) and can be fractional (ROADMAP S28); the exchange is sharded (shard 2 Crypto & Commodities, shard 3 Tennis, Baseball & Basketball; names read live from `/exchange/status`, the shard of each market from its `exchange_index`) and cash does not follow the markets; the money path reads `*_dollars` price fields and sends whole-cent limits, which lie on every published `price_ranges` grid; the series tickers in the sport filters exist (`KXNCAAFGAME`, not `KXNCAAFBGAME`); the fee schedule | `scripts/kalshi/kalshi_client.py`, `kalshi_executor.py`, `kalshi_settler.py`, `app/config.py` · reference: `docs/kalshi/kalshi-sports-betting/KALSHI_API_REFERENCE.md` | docs.kalshi.com (API reference and changelog); kalshi.com/docs/kalshi-fee-schedule.pdf | 2026-11-16 |

## Market data

| Upstream | What the code assumes | Code | Check at | Last checked |
|:---|:---|:---|:---|:---|
| **The Odds API v4** | `api.the-odds-api.com/v4`; the per-event endpoint puts `last_update` on markets, not bookmakers (S19), and the docs now call the sport-level bookmaker `last_update` deprecated (read 2026-11-16), so `_bookmaker_last_update()` must keep its market-timestamp fallback; monthly per-key quota, keys rotated by `check_odds_keys.py` | `scripts/kalshi/edge_detector.py`, `futures_edge.py`, `scripts/shared/check_odds_keys.py` | the-odds-api.com/liveapi/guides/v4/ | 2026-11-16 |
| **ESPN site API** *(unofficial, undocumented)* | `site.api.espn.com/apis/site/v2/sports/…` and `/apis/v2/sports/…` return the shapes the parsers read | `scripts/shared/line_movement.py`, `rest_days.py`, `team_stats.py` | No official docs. Check with one live unauthenticated GET per endpoint and compare the keys the parser reads | 2026-11-16 |
| **MLB Stats API** *(public, undocumented)* | `statsapi.mlb.com/api/v1` standings and pitcher endpoints | `scripts/shared/pitcher_stats.py`, `team_stats.py` | One live GET; github.com/toddrob99/MLB-StatsAPI tracks changes | 2026-11-16 |
| **NHL web API** *(public, undocumented)* | `api-web.nhle.com/v1/standings/now` | `scripts/shared/team_stats.py` | One live GET | 2026-11-16 |
| **NWS API** | `api.weather.gov/gridpoints/…`; requires a `User-Agent` header | `scripts/shared/sports_weather.py` | weather.gov/documentation/services-web-api | 2026-11-16 |

## Notifications

| Upstream | What the code assumes | Code | Check at | Last checked |
|:---|:---|:---|:---|:---|
| **Resend** | REST `POST /emails` over `requests`, no SDK | `scripts/schedulers/automation/send_report_email.py` | resend.com/docs and resend.com/changelog | 2026-11-16 |

## Runtime and libraries

| Upstream | What the code assumes | Where | Check at | Last checked |
|:---|:---|:---|:---|:---|
| **Python** | 3.11+ | `pyproject.toml`, `AGENTS.md` | devguide.python.org/versions (EOL dates) | 2026-11-16 |
| **`requests`, `cryptography`, `numpy`, `scipy`, `rich`, `filelock`, `markdown-it-py`** | Exact, hashed pins in `requirements.txt` (built from `requirements.in` with `make lock`); `cryptography` does the RSA-PSS signing | `requirements.in`, `requirements.txt` | PyPI release pages. Flag breaking majors and security advisories only | 2026-11-16 |

*Planned, not built* (no row until code exists): Alpaca, Coinbase, Manifold.
