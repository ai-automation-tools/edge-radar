# Filter reference

*Reference for the [`/edge-radar` skill](../SKILL.md).* Every `--filter` name each scanner accepts, plus raw ticker prefixes. Read it when routing a sport, futures or prediction request.

---

## Filter Quick Reference

### Sports (Game Betting) — `edge_detector.py`

| Filter | Sport | Edge Detection |
|--------|-------|----------------|
| `nba` | NBA Basketball | Yes |
| `nhl` | NHL Hockey | Yes |
| `mlb` | MLB Baseball | Yes |
| `nfl` | NFL Football | Yes (seasonal) |
| `ncaamb` | NCAA Men's Basketball | Yes |
| `ncaabb` | NCAA Basketball (additional) | Yes |
| `ncaawb` | NCAA Women's Basketball | Browse only |
| `ncaafb` | NCAA Football | Browse only |
| `mls` | MLS Soccer | Browse only |
| `soccer` | All soccer combined | Browse only |
| `ucl`, `epl`, `laliga`, `seriea`, `bundesliga`, `ligue1` | European leagues | Browse only |
| `ufc`, `boxing` | Combat sports | Browse only |
| `f1`, `nascar` | Motorsports | Browse only |
| `pga` | PGA Golf (majors) | Yes — routes to futures (4 majors only) |
| `ipl` | IPL Cricket | Browse only |
| `cs2`, `lol`, `esports` | Esports | Browse only |
| `tennis`, `wimbledon` | ATP + WTA match-winner | Yes — needs date-tolerant matching (`_is_tennis_market()`), since tennis tickers don't carry a reliable start time |
| `wc`, `worldcup` | World Cup (`KXWCSPREAD` etc.) | Yes |

37 filter shortcuts are registered in `FILTER_SHORTCUTS` (`scripts/kalshi/edge_detector.py`) — the table above covers the common ones. When unsure, read that dict rather than guessing.

**Market types per sport.** Most sports scan all three of moneyline / spread / total. **MLB was moneyline-only until 2026-07-20**, when `KXMLBSPREAD` + `KXMLBTOTAL` were wired in (they'd launched on Kalshi after MLB was first integrated in March and were silently absent from the maps). First scan after the fix went 106 → 407 MLB markets. Deep-bracket MLB Unders are a young, uncalibrated sub-population — treat high claimed edges there with suspicion until more settle.

### Futures (Championships) — `futures_edge.py`

| Filter | What It Scans | Edge Detection |
|--------|---------------|----------------|
| `futures` | All futures | Yes (where available) |
| `nfl-futures` / `superbowl` | Super Bowl champion | Yes |
| `nba-futures` | NBA Finals + conferences | Yes |
| `nhl-futures` | Stanley Cup + conferences | Yes |
| `mlb-futures` | World Series + playoffs | Yes |
| `ncaab-futures` | NCAAB MOP | Yes |
| `golf-futures` | Golf major winners (4 majors only) | Yes |

### Prediction Markets — `prediction_scanner.py`

| Filter | Category | Edge Detection | Data Source |
|--------|----------|----------------|-------------|
| `crypto`, `btc`, `eth`, `xrp`, `doge`, `sol` | Crypto prices | Yes | CoinGecko |
| `weather` | Temperature forecasts | Yes | NWS API |
| `spx`, `sp500` | S&P 500 levels | Yes | Yahoo Finance + VIX |
| `mentions`, `lastword`, `nbamention`, `foxnews`, `politicsmention` | TV mentions | Yes | Historical rates |
| `companies`, `bankruptcy`, `ipo` | Corporate events | Partial | Historical baseline |
| `politics`, `impeach` | Political events | Yes | Time-decay model |
| `techscience`, `quantum`, `fusion` | Tech milestones | Yes | Time-decay model |

### Raw Ticker Prefixes

Any Kalshi ticker prefix works as a filter (e.g., `KXNHLGOAL`, `KXNBA3PT`, `KXUFCFIGHT`).
