# Execute Prediction Market Bets

Scan a prediction category and execute the best picks through the pipeline.

> **⚠️ Prediction execution is gated off by default (Gate 4.7 / R25).** Crypto, weather, SPX, mentions, companies, and politics bets are **rejected at the risk gate** unless `ALLOW_PREDICTION_BETS=true` is set in `.env`. Scans (preview) always work; only `--execute` is blocked. If you set this in `.env`, restart any long-running host process (gates snapshot at import). For a one-off CLI run you can prepend it:
> ```
> ALLOW_PREDICTION_BETS=true python scripts/scan.py prediction --filter <category> --min-edge 0.05 --max-bets 5 --unit-size 1 --exclude-open
> ```

```
python scripts/kalshi/kalshi_executor.py status
python scripts/scan.py prediction --filter <category> --min-edge 0.05 --max-bets 5 --unit-size 1 --exclude-open
```

Replace `<category>` with: `crypto`, `btc`, `eth`, `xrp`, `doge`, `sol`, `weather`, `spx`, `mentions`, `companies`, `politics`.

Output columns: Title | Date | Cat. | Side | Mkt | Fair | Edge | Conf | Score

In the preview, explain each row in plain English. Afterwards, tell me when each bet settles so I know when to run `python scripts/kalshi/kalshi_settler.py settle`

## Placing orders

1. Run the sizing command above. It has no `--execute`, so it previews and sizes the rows and places nothing.
2. Show me the preview table and stop. Place nothing until I reply **go** with the markets I want.
3. Place exactly those markets, with the same flags (and the `ALLOW_PREDICTION_BETS=true` prefix if you used it) plus:
   ```
   --execute --ticker <TICKER> [<TICKER> ...]
   ```
   This scanner doesn't cache its preview and a fresh scan can renumber rows, so pick by ticker, not row number.
4. Show me the run summary (placed / failed / blocked), total cost and updated balance.
