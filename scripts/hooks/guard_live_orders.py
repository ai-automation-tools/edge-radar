"""Claude Code PreToolUse hook (ER-01): an agent session never starts a live order.

Wired in `.claude/settings.json` for the Bash and PowerShell tools. It blocks (exit 2) any
command segment that carries an order trigger (`--execute`, `--go`, `--send-it`,
`--mode execute`, `--verify-eligibility`, `create_order`, `intra_exchange_transfer`).
Ask rules don't hold in bypass-permissions sessions; a hook's exit 2 does. The owner
places orders by typing `! <command>` in the prompt, which doesn't go through tool
hooks, or through the scheduled tasks, which don't run Claude at all.

Segments that start with a read-only tool (git, grep, cat, ...) are skipped, so
searching for or committing text about these flags still works.

ponytail: a text match, not a sandbox. A determined bypass (an alias, an encoded
string) gets past it; `KalshiClient`'s cap and `data/KILL` are the backstop.
Stdlib only, so it runs under any `python` on PATH.
"""

from __future__ import annotations

import json
import re
import sys

TRIGGER = re.compile(
    r"--(?:execute|go|send-it|verify-eligibility)(?![\w-])"
    r"|--mode[=\s]+execute\b"
    r"|\b(?:create_order|intra_exchange_transfer)\b"
)
READERS = {
    "git",
    "gh",
    "grep",
    "rg",
    "cat",
    "head",
    "tail",
    "sed",
    "awk",
    "less",
    "wc",
    "echo",
    "select-string",
    "get-content",
    "findstr",
}
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")


def blocked(command: str) -> bool:
    for segment in SEGMENT_SPLIT.split(command):
        words = segment.strip().split()
        if not words or words[0].lower() in READERS:
            continue
        if TRIGGER.search(segment):
            return True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if not blocked(command):
        return 0
    print(
        "Blocked by Edge-Radar's live-order guard (ER-01): this command can place real orders "
        "or move money. Show the owner the exact command and ask them to run it themselves "
        "by typing `! <command>` in the prompt.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
