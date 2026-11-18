# Execute Top Picks

Scan for the best opportunities on `<sport>` and execute the top picks. Be disciplined -- only bet where edge is real.

```
python scripts/kalshi/kalshi_executor.py status
python scripts/scan.py sports --filter <sport> --min-edge 0.05 --max-bets 5 --unit-size 1 --date today --exclude-open
```

Replace `<sport>` with any active filter: `nba`, `nhl`, `mlb`, `nfl`, `ncaamb`, `ncaafb`, `soccer`, `mls`, `epl`, `worldcup`, `ufc`, `boxing`, `f1`, `nascar`, `ipl`, `esports`, etc. (full roster in `sport-specific-scan.md`).

To target a specific market type, add `--category game`, `--category spread`, `--category total`, or `--category player_prop`.

In the preview, show the Bet (matchup), Type, Pick, Edge, Conf and Score for each row. Afterwards, remind me when to run `python scripts/kalshi/kalshi_settler.py settle`.

## Placing orders

1. Run the sizing command above. It has no `--execute`, so it previews and sizes the rows and places nothing.
2. Show me the preview table and stop. Place nothing until I reply **go** with the rows I want.
3. Place exactly those rows, with the same flags plus:
   ```
   --execute --pick '<rows>'
   ```
   `--pick` replays the cached preview, so the row numbers are the ones I saw.
4. Show me the run summary (placed / failed / blocked), total cost and updated balance.
