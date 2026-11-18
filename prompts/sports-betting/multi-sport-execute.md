# Multi-Sport Execute Session

Full scan-and-execute workflow across all active sports. Scans each sport, previews the combined best picks, and executes with discipline.

## Steps

1. Check portfolio and risk limits:
```bash
python scripts/kalshi/kalshi_executor.py status
python scripts/kalshi/risk_check.py --report limits
```

2. Settle any outstanding bets first:
```bash
python scripts/kalshi/kalshi_settler.py settle
```

3. Scan each active sport (adjust filters to what's in season):
```bash
python scripts/scan.py sports --filter mlb --min-edge 0.03 --top 10 --date today --exclude-open
python scripts/scan.py sports --filter nba --min-edge 0.03 --top 10 --date today --exclude-open
python scripts/scan.py sports --filter nhl --min-edge 0.03 --top 10 --date today --exclude-open
```

4. Size the best picks across all sports (preview only; adjust max-bets and unit-size to your risk appetite):
```bash
python scripts/scan.py sports --min-edge 0.05 --max-bets 10 --unit-size 1 --date today --exclude-open
```

5. After placing orders (below), save a report of what was executed:
```bash
python scripts/kalshi/kalshi_executor.py status --save
```

## Output

The preview table shows: Bet, Type (ML/Spread/Total/Prop), Pick (e.g., "Heat win", "Over 220.5", "Spurs -4.5"), When, Qty, Price, Cost, Edge.

## Discipline checklist

- [ ] Daily loss limit not breached
- [ ] Not doubling up on same game (check for multiple bets on one matchup)
- [ ] Unit size consistent with bankroll (1-2% of balance)
- [ ] Minimum edge 5%+ for execution (preview at 3%, execute at 5%)

## Placing orders

1. Run the sizing command above. It has no `--execute`, so it previews and sizes the rows and places nothing.
2. Show me the preview table and stop. Place nothing until I reply **go** with the rows I want.
3. Place exactly those rows, with the same flags plus:
   ```
   --execute --pick '<rows>'
   ```
   `--pick` replays the cached preview, so the row numbers are the ones I saw.
4. Show me the run summary (placed / failed / blocked), total cost and updated balance.
