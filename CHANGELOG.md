# Changelog

## 0.1.0 (2026-10-26)

On PyPI: `uvx agentwaste`.

First release of agentwaste, pivoted from the AgentSight SDK (now in
`legacy/agentsight`).

- Claude Code transcript reader.
- Six detectors: idle cache rebuild, uncached context (Claude, and
  informational for self-hosted models), re-read, duplicate call, huge result,
  error thrash.
- Terminal report with fixes, `--json`, shareable `--card`, optional
  `--usd-per-mtok`, and `--demo` synthetic sessions.
- Documentation site (Astro Starlight) at https://nikghodki.github.io/agentwaste/.
