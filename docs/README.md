# 📖 Edge-Radar Documentation

<p align="center">
  <img src="https://img.shields.io/badge/Documentation-Index-0078d4?style=for-the-badge&labelColor=09090b" alt="Documentation Index">
  <img src="https://img.shields.io/badge/Platform-Kalshi-e74c3c?style=for-the-badge&labelColor=09090b" alt="Platform">
  <img src="https://img.shields.io/badge/Stack-Python-2ea44f?style=for-the-badge&labelColor=09090b" alt="Stack">
  <img src="https://img.shields.io/badge/Status-Active%20Execution-8b5cf6?style=for-the-badge&labelColor=09090b" alt="Status">
</p>

Welcome to the central documentation index for **Edge-Radar**. This index organizes the setup manuals, strategy guides, system architecture definitions, and repository analyses.

---

## 🗺️ Documentation Directory

Only `README.md`, `CHANGELOG.md` and `RULES-RATIONALE.md` live at the root of `docs/`. Everything else is grouped into the subfolders below.

### 🚀 Setup & Architecture — [`setup/`](./setup/)
*   [SETUP_GUIDE.md](./setup/SETUP_GUIDE.md) — Step-by-step instructions to configure API keys, venv, and RSA private credentials.
*   [ARCHITECTURE.md](./setup/ARCHITECTURE.md) — In-depth overview of the pipeline, Kelly sizing equations, and risk gating conditions.
*   [AUTOMATION_GUIDE.md](./setup/AUTOMATION_GUIDE.md) — Setting up the automated scanners and schedulers.
*   [mcp-servers.md](./setup/mcp-servers.md) — why Edge-Radar needs no MCP server.
*   **[diagrams/](./diagrams/README.md) — the betting logic data-flow diagram the [homepage](https://edge-radar.ai-automation-tools.dev/#pipeline) shows** (interactive, every box linked to its code). Generated from one JSON; a pre-commit hook and `--check` flag it when cited code changes.
*   [pipeline-diagram.md](./setup/pipeline-diagram.md) — End-to-end pipeline & data-flow diagram (scan → edge models → risk gating → execution → calibration feedback).

### ⏰ Automation Schedule — [`task-schedules/`](./task-schedules/)
*   **[task-schedules/README.md](./task-schedules/README.md) — the full ~20-task automation pipeline the repo owner actually runs** (scan → execute → email → settle → reconcile → calibrate → review). Documented as a recommended starting point, with sanitized `.bat`/`.sh` templates and `schtasks` registration so you can build the equivalent on your own machine. Start with [AUTOMATION_GUIDE.md](./setup/AUTOMATION_GUIDE.md) for the minimal installer-driven core.

### 🎲 Longshot profile — [`longshot/`](./longshot/)
*   **[README.md](./longshot/README.md) — start here: how the two strategies stay separate** (selection / settings / money / data), what they deliberately share, and the surfaces still pooled. The longshot/futures strategy runs as a `--profile longshot` overlay on Kalshi subaccount 1 (P1); it replaced the separate `Edge-Radar-Longshot` fork on 2026-09-10.
*   [FORK-ROADMAP-ARCHIVE.md](./longshot/FORK-ROADMAP-ARCHIVE.md) — The retired fork's own ROADMAP, kept verbatim for its subaccount, `balance_breakdown` and price-band evidence.

### 🎯 Betting Guides & Coverage — [`kalshi/`](./kalshi/)
*   **[kalshi/README.md](./kalshi/README.md) — start here: the sports/markets coverage matrix (what's configured, what bet types) and links to every betting guide.**
*   [SPORTS_GUIDE.md](./kalshi/kalshi-sports-betting/SPORTS_GUIDE.md) — Sports edge model: weighted de-vig consensus, CDF spreads/totals, sportsbook weighting tiers.
*   [MLB_FILTERING_GUIDE.md](./kalshi/kalshi-sports-betting/MLB_FILTERING_GUIDE.md) — Pitcher/matchup and weather filtering for baseball wagers.
*   [KALSHI_API_REFERENCE.md](./kalshi/kalshi-sports-betting/KALSHI_API_REFERENCE.md) — Kalshi REST/auth reference (RSA signing, endpoints).
*   [FUTURES_GUIDE.md](./kalshi/kalshi-futures-betting/FUTURES_GUIDE.md) — Championship and division futures de-vigging models.
*   [PREDICTION_MARKETS_GUIDE.md](./kalshi/kalshi-prediction-betting/PREDICTION_MARKETS_GUIDE.md) — Scanners for Weather (NWS), Crypto (CoinGecko), and S&P 500.

### ⚙️ Scripts & CLI — [`scripts/`](./scripts/)
*   [SCRIPTS_REFERENCE.md](./scripts/SCRIPTS_REFERENCE.md) — Complete CLI reference for every script, flag, and batch command.
*   [per-script/](./scripts/per-script/) — Deep-dive docs for each script (edge_detector, futures_edge, prediction_scanner, kalshi_executor, kalshi_settler, risk_check, backtester).

### 🔬 Strategy Reviews — [`enhancements/`](./enhancements/)
*   [betting-strategy-review-2026-08-26.md](./enhancements/betting-strategy-review-2026-08-26.md) — Full review of the settled record (402 bets), the defects found (CLV never computed, no cumulative-exposure gate, taker-only fee drag), and a four-phase action plan: stop waste → install CLV measurement → remove trading cost → scale only on evidence.

### 📈 Roadmap & Changelog
*   [ROADMAP.md](./ROADMAP.md) — Open work only, in priority order. Shipped items and findings live in the changelog.
*   [CHANGELOG.md](./CHANGELOG.md) — Project history since 2026-10. Older months, and the pre-2026-09-29 roadmap, are in [changelog/](./changelog/README.md).
*   [RULES-RATIONALE.md](./RULES-RATIONALE.md) — The evidence behind each rule in `AGENTS.md`: incidents, settled-bet numbers, reasoning.

> Periodic performance audits live under `docs/my-documents/` (git-ignored, local-only). Their conclusions are folded into the ROADMAP findings log, which is the tracked, canonical record.

---

> [!NOTE]
> All automated scheduler files and execution paths in this repository are designed for Windows 11 using PowerShell (`pwsh`) and Command Prompt (`cmd`) scripts.

<p align="center">
  Built with <a href="https://modelcontextprotocol.io">MCP</a> · <a href="https://kalshi.com">Kalshi API</a>
</p>
