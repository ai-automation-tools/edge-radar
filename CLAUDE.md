@AGENTS.md

# CLAUDE.md — Edge-Radar (Claude Code-only notes)

The rules, gates and limits all live in `AGENTS.md` (imported above). This file holds only what is
specific to Claude Code.

- **Skills:** `/edge-radar`, `/edge-radar-analysis`, `betting-logic-review` and the two `edge-radar-strategy-*` skills are tracked in `skills/` at the repo root (the strategy pair moved here from `agent-skills` on 2026-11-27); `.claude/skills/` holds Windows junctions to them (git-ignored — real symlinks can't be committed with `core.symlinks=false`). **Edit `skills/`, never the junctions.** After a fresh clone: `pwsh -File scripts/setup/link_skills.ps1`.
- Project slash commands live in `.claude/commands/`. There are no project agents; use the skills.
- Memory is Claude Code's auto-memory for this project only (`/memory` shows where).
