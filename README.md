<div align="center">

# agentwaste

**Your AI coding agent is wasting tokens. Find out where, and how to stop it.**

[![CI](https://github.com/nikghodki/agentwaste/actions/workflows/ci.yml/badge.svg)](https://github.com/nikghodki/agentwaste/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-nikghodki.github.io%2Fagentwaste-ff7a59)](https://nikghodki.github.io/agentwaste/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/nikghodki/agentwaste/tree/main/LICENSE)

[**Documentation**](https://nikghodki.github.io/agentwaste/) ·
[Quickstart](https://nikghodki.github.io/agentwaste/quickstart/) ·
[How it works](https://nikghodki.github.io/agentwaste/how-it-works/) ·
[Contributing](https://github.com/nikghodki/agentwaste/blob/main/CONTRIBUTING.md)

<img src="https://raw.githubusercontent.com/nikghodki/agentwaste/main/assets/report.png" alt="agentwaste report: 41% waste, grade D, with re-caching after idle breaks as the top finding and a fix for each pattern" width="820">

</div>

## Try it in 10 seconds

```bash
uvx --from git+https://github.com/nikghodki/agentwaste agentwaste
```

That's it: no install, no account, no config. It reads the Claude Code logs
already on your machine and prints a report. No history yet? Add `--demo`.

Want the `agentwaste` command permanently? Install it once:

```bash
uv tool install git+https://github.com/nikghodki/agentwaste      # or: pipx install git+https://github.com/nikghodki/agentwaste
```

The examples below use the installed command. Without installing, put
`uvx --from git+https://github.com/nikghodki/agentwaste` in front of them.

## Why

Usage trackers tell you **how much** you used. agentwaste tells you **why**,
and how much of it was avoidable.

On one developer's month of Claude Code use, **about a third of all input cost
was re-caching the conversation after stepping away for more than five
minutes.** Nobody noticed, because nothing showed it.

Whether you pay per token or hit subscription limits, that's waste you can fix
in minutes once you can see it.

## What it finds

| | Pattern | What's happening | The fix |
|---|---|---|---|
| ⏸️ | **Idle cache rebuild** | You step away, the 5-minute prompt cache expires, and the next message re-writes the whole context at 1.25x | `/compact` before a break, or the 1-hour cache |
| 🔁 | **Uncached context** | Every turn re-sends the conversation without caching, often because a proxy drops cache markers | Fix the proxy so caching survives |
| 📄 | **Re-read** | The agent re-reads a file it already read, with no change in between | Put the facts in `CLAUDE.md` |
| 🔍 | **Duplicate call** | The same search or fetch runs again with nothing changed | Reuse results, search more precisely |
| 📦 | **Huge result** | One 10k+ token output, carried in every later message | `head`, filters, ranged reads |
| 💥 | **Error thrash** | The same tool fails 3+ times in a row | Give the agent the missing context |

Every finding comes with its cost, the worst offenders and a specific fix.
[Exact definitions →](https://nikghodki.github.io/agentwaste/detectors/overview/)

## Share your grade

<img src="https://raw.githubusercontent.com/nikghodki/agentwaste/main/assets/card.png" alt="Shareable agentwaste card: grade D, 41% of input tokens wasted, top categories re-caching after idle breaks, huge tool outputs and uncached context" width="300" align="right">

```bash
agentwaste --card my-card.html
```

A one-file card with your grade and top waste categories, ready to screenshot
and post. It contains **aggregates only**: no paths, project names, commands
or code. A test enforces that on every change.

<br clear="right">

## More options

```bash
agentwaste --days 7               # last week only (default 30; 0 = everything)
agentwaste --usd-per-mtok 3       # dollar estimates at $3 per million input tokens
agentwaste --json > waste.json    # machine-readable, for scripts and dashboards
agentwaste --demo                 # try it on synthetic sessions
```

Full reference: [CLI](https://nikghodki.github.io/agentwaste/reference/cli/) ·
[JSON output](https://nikghodki.github.io/agentwaste/reference/json-output/)

## Private by design

- **Local and read-only.** No network requests, nothing uploaded, your logs are never changed.
- **No dependencies.** Plain Python 3.10+, so there's nothing hidden to audit.
- **Honest numbers.** Costs are in [token-equivalents](https://nikghodki.github.io/agentwaste/how-it-works/#token-equivalents)
  that weight cache writes, cache reads and fresh input the way they're actually
  billed. Self-hosted models are reported separately, since their cost is GPU
  time, not tokens.

## Roadmap

- [x] Claude Code support, six detectors, report, JSON, shareable card
- [ ] Codex support
- [ ] `pip install agentwaste` / `uvx agentwaste` from PyPI
- [ ] Live warnings while you work ("your cache expires in 1 minute")
- [ ] Before/after comparison: did the fix actually help?

Ideas and votes welcome in [issues](https://github.com/nikghodki/agentwaste/issues).

## Contributing

Contributions are very welcome, especially **new log sources** (Codex, Gemini
CLI, OpenCode) and **new detectors**. Start with [CONTRIBUTING.md](https://github.com/nikghodki/agentwaste/blob/main/CONTRIBUTING.md):

```bash
git clone https://github.com/nikghodki/agentwaste && cd agentwaste
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest
```

The original AgentSight SDK lives on in [`legacy/agentsight`](https://github.com/nikghodki/agentwaste/tree/main/legacy/agentsight).

## License

[MIT](https://github.com/nikghodki/agentwaste/tree/main/LICENSE)
