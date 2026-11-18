# MCP servers

Edge-Radar needs no MCP server. Scans, orders, settlement and reports all run from the Python scripts in
`scripts/`, and an agent works by reading the repo and running those scripts. The repo ships no `.mcp.json`.

- **Live orders never go through MCP.** They go through `kalshi_executor.py`, its risk gates and the
  `guard_live_orders.py` hook (see [AGENTS.md](../../AGENTS.md)). Don't give an agent an MCP server that can
  place orders or move funds.
- **Optional, not built:** a read-only Kalshi server (markets, order book, positions; no order or transfer
  endpoints) would save an agent from shelling out for lookups. Until it exists, use
  `python scripts/kalshi/kalshi_executor.py status` and the scan scripts.

Earlier versions of this page described a Claude Desktop setup (filesystem, fetch, memory, search, SQLite,
Alpaca, Playwright) and an agent-coordination server. None of it was ever wired to this repo, and it is gone.

[← Docs index](../README.md)
