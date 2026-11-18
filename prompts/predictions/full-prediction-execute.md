# Full Prediction Market Execute Session

Scan all prediction categories and execute the best opportunities.

## Steps

1. Check portfolio:
```bash
python scripts/kalshi/kalshi_executor.py status
```

2. Settle any outstanding prediction bets:
```bash
python scripts/kalshi/kalshi_settler.py settle
```

3. Scan all prediction markets:
```bash
python scripts/scan.py prediction --min-edge 0.03 --top 20 --exclude-open
```

4. Or scan by category for focused analysis:
```bash
python scripts/scan.py prediction --filter crypto --min-edge 0.03 --top 10 --exclude-open
python scripts/scan.py prediction --filter weather --min-edge 0.05 --top 10 --exclude-open
python scripts/scan.py prediction --filter spx --min-edge 0.03 --top 10 --exclude-open
```

5. Size the top picks (preview only):
```bash
python scripts/scan.py prediction --min-edge 0.05 --max-bets 5 --unit-size 1 --exclude-open
```

> **⚠️ Execution requires `ALLOW_PREDICTION_BETS=true` (Gate 4.7 / R25).** Without it, every prediction bet is rejected at the risk gate — scans still preview fine. Set it in `.env` (restart any long-running host) or prepend `ALLOW_PREDICTION_BETS=true ` to the CLI command for a one-off run.

## Output

The scan table shows: Title, Date, Cat. (crypto/weather/spx/mentions), Side, Mkt, Fair, Edge, Conf, Score.

## Category notes

- **Crypto**: Model uses CoinGecko price + trend. Best when market is clearly mispriced vs current price.
- **Weather**: Model uses NWS forecast. Most accurate 1-2 days out. Temperature strikes far from forecast have the most edge.
- **SPX**: Model uses Yahoo Finance + VIX. VIX spikes create the most mispricing.
- **Mentions**: Historical settlement patterns. High base-rate YES markets often mispriced.
- **Companies / Politics**: Lower-frequency categories. Treat displayed edge skeptically — thin liquidity and slow-moving lines mean stale prices look like edge. Confirm the strike/resolution wording before betting.

## Placing orders

1. Run the sizing command above. It has no `--execute`, so it previews and sizes the rows and places nothing.
2. Show me the preview table and stop. Place nothing until I reply **go** with the markets I want.
3. Place exactly those markets, with the same flags (and the `ALLOW_PREDICTION_BETS=true` prefix if you used it) plus:
   ```
   --execute --ticker <TICKER> [<TICKER> ...]
   ```
   This scanner doesn't cache its preview and a fresh scan can renumber rows, so pick by ticker, not row number.
4. Show me the run summary (placed / failed / blocked), total cost and updated balance.
