# Execute Futures Bets

Scan championship/futures markets and execute the best picks. Futures edges are small (0.5–2% is normal) and capital locks up until the season resolves, so be disciplined and size small.

> Futures execution mirrors the automated **Weekly-Futures-Execution** task (Saturdays): `scan.py futures --execute` with a small budget, capped at a few bets. Most weeks it places **zero** bets by design — that's expected, not a failure.

```
python scripts/kalshi/kalshi_executor.py status

# Preview first
python scripts/scan.py futures --filter <sport> --min-edge 0.01 --top 20 --exclude-open --save

# Size with a tight budget cap (preview only)
python scripts/scan.py futures --filter <sport> --min-edge 0.01 --max-bets 3 --unit-size 1 --budget 5% --exclude-open
```

Replace `<sport>` with: `nfl-futures`, `nba-futures`, `nhl-futures`, `mlb-futures`, `ncaab-futures`, `golf-futures`. Omit `--filter` to scan all futures at once.

Output columns: Bet Type, Candidate, Date, Side, Mkt, Fair, Edge, Conf.

## Discipline

1. Show the preview first — Candidate, Side (YES/NO), Mkt price, Fair value, Edge, Conf
2. Wait for confirmation before executing
3. Prefer YES bets where edge supports it (lower cost, cleaner ROI)
4. Flag any pick where the displayed Kalshi price looks **stale or unfillable** — futures liquidity is thin
5. After execution: orders placed, fill status, total cost, updated balance, and the settlement horizon (these positions lock up for weeks/months)

If the best edge is under ~0.5%, say so honestly and recommend skipping — daily game betting usually offers better value.

## Placing orders

1. Run the sizing command above. It has no `--execute`, so it previews and sizes the rows and places nothing.
2. Show me the preview table and stop. Place nothing until I reply **go** with the markets I want.
3. Place exactly those markets, with the same flags plus:
   ```
   --execute --ticker <TICKER> [<TICKER> ...]
   ```
   This scanner doesn't cache its preview and a fresh scan can renumber rows, so pick by ticker, not row number.
4. Show me the run summary (placed / failed / blocked), total cost and updated balance.
