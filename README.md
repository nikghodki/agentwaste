# agentwaste

**Find where your AI coding agent wastes tokens, and how to stop it.**

agentwaste reads the session logs Claude Code already keeps on your computer,
finds the patterns that burn tokens for nothing, and tells you what to change.
Usage trackers tell you *how much* you used; agentwaste tells you *why*, and how
much of it was avoidable.

```bash
uvx agentwaste
```

```text
agentwaste: 111 sessions, 78,496 model calls, 90,274 tool calls  (2026-09-01 to 2026-10-26)

Priced input: 3.3B token-equivalents   (cache writes 1.2B, cache reads 18.4B, fresh 10.6M; output 22.3M)
Estimated waste: 1.1B (34%)   Grade: D

 32.3%  Re-caching after idle breaks  (2,588x, 1.1B eq)
        Fix: The prompt cache expires after 5 minutes idle, so the next message re-writes
        the whole context at 1.25x. Run /compact (or /clear) before a break, ...
```

## What it finds

| Pattern | What happens |
| --- | --- |
| Idle cache rebuild | You step away, the 5-minute prompt cache expires, and the next message re-writes the whole context |
| Uncached context | Every turn re-sends the conversation without prompt caching (often a proxy dropping cache markers) |
| Re-read | The agent reads a file it already read, with no change in between |
| Duplicate call | The same search or fetch runs again with nothing changed |
| Huge result | One tool output over 10k tokens, carried in every later message |
| Error thrash | The same tool fails 3+ times in a row |

Each finding comes with its cost, the worst examples and a specific fix.
Self-hosted models are reported separately: their cost is GPU time, not tokens,
so they don't affect the grade.

## Options

```bash
uvx agentwaste --days 7               # last week only (default 30; 0 = everything)
uvx agentwaste --card card.html       # shareable card, aggregates only
uvx agentwaste --usd-per-mtok 3       # add dollar estimates
uvx agentwaste --json                 # machine-readable output
```

## Privacy

Local only and read-only: no network requests, and your logs are never changed.
The shareable card contains aggregates only, with no paths, project names,
commands or content; a test enforces this. The terminal report and JSON are for
you and can name files and projects.

## Docs

Full documentation is in [`docs/`](docs/) (MDX, Mintlify): how the cost model
works, exact detector definitions, CLI and JSON reference.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

No runtime dependencies; Python 3.10+. Tests use synthetic transcripts only.
The original AgentSight SDK lives in [`legacy/agentsight`](legacy/agentsight).

## License

MIT
