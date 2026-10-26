# Contributing to agentwaste

Thanks for helping. agentwaste is small on purpose: a zero-dependency Python
CLI, a handful of detectors, and docs that must match the code.

## Setup

```bash
git clone https://github.com/nikghodki/agentwaste
cd agentwaste
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/agentwaste --demo
```

Docs (Astro Starlight, Node 18+):

```bash
cd docs && npm ci && npm run dev   # http://localhost:4321/agentwaste/
```

## How the code is organised

| Path | What it does |
| --- | --- |
| `src/agentwaste/sources/` | Readers that turn an agent's logs into `Stream` objects |
| `src/agentwaste/model.py` | The source-agnostic session model |
| `src/agentwaste/detectors.py` | One function per waste pattern, each returning a `Finding` |
| `src/agentwaste/cost.py` | Token-equivalent weights |
| `src/agentwaste/analysis.py` | Totals, waste %, grade |
| `src/agentwaste/report.py`, `card.py`, `cli.py` | Output |
| `src/agentwaste/demo.py` | Synthetic sessions for `--demo` |
| `docs/src/content/docs/` | The MDX docs site |
| `legacy/agentsight/` | The earlier AgentSight SDK, not built or tested here |

## Good first contributions

- **A new log source** (Codex, Gemini CLI, OpenCode, ...). Add a reader in
  `src/agentwaste/sources/` that returns `Stream` objects; detectors then work
  unchanged. Open a "New log source" issue first so we can agree on the format.
- **A new detector.** Add it to `detectors.py` and `ALL_DETECTORS`, give it a
  docs page under `docs/src/content/docs/detectors/`, and add it to the overview
  table and `docs/sidebar.json`. The docs tests fail until it's documented.
- **Better fix advice.** If you know a better way to avoid a pattern, improve
  its `fix` text.

## Rules

1. **Tests first, synthetic data only.** Never commit real transcripts: they
   contain code, paths and secrets. `tests/conftest.py` has a builder for
   synthetic Claude Code logs.
2. **The card stays private.** It must never contain paths, project names,
   commands or session content. A test enforces this.
3. **Docs match code.** Thresholds, weights, grade bands, CLI flags and detector
   keys quoted in the docs are checked by `tests/test_docs.py`.
4. **No runtime dependencies.** The CLI must run with a plain Python 3.10+.
5. **Small, focused pull requests** with a clear description of the behaviour
   change. CI must be green.

## Reporting bugs

Use the issue templates. For a wrong number, the `--json` output (with names
removed) is the most useful thing you can attach. Don't paste raw transcripts.

By contributing you agree that your contributions are licensed under the MIT
License and that you'll follow the [Code of Conduct](CODE_OF_CONDUCT.md).
