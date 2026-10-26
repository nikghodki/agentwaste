# agentwaste v1 design

## What it is
A zero-dependency CLI that reads the session logs AI coding agents already
write locally, finds where tokens were wasted, and suggests fixes. Local-only:
nothing leaves the machine unless the user shares the generated card.

## Cost model: priced input-token equivalents ("eq")
Anthropic prompt caching bills input three ways. One eq = one fresh input token.

| Kind | Weight |
|---|---|
| fresh input (`input_tokens`) | 1.0 |
| cache write, 5-minute TTL | 1.25 |
| cache write, 1-hour TTL | 2.0 |
| cache read (`cache_read_input_tokens`) | 0.1 |

Output tokens are reported separately. Dollar figures are optional
(`--usd-per-mtok`): prices and plans change, so eq is the primary unit.

## Streams
Calls are grouped per `(sessionId, isSidechain)`: subagents run in sidechains
with their own cache, so their timing and repeats are judged separately.

## Detectors (v1)
1. **idle_cache_rebuild**: a model call writes >= `min_rebuild` (20,000)
   cache tokens and the previous call in the stream was more than the cache TTL
   ago (300 s; 3,600 s if the call used the 1-hour cache). Waste = tokens x
   (write weight - read weight): the extra over what a warm cache would cost.
2. **reread**: `Read` of a file already read in the stream, with no edit of
   that file (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`) and no `Bash` call
   in between (Bash may have changed it). Waste = result tokens x 1.25.
3. **duplicate_call**: an identical call (same tool, same input) of a
   read-only tool (`Grep`, `Glob`, `LS`, `WebFetch`, `WebSearch`) already made
   in the stream, with no mutating call (`Edit`, `Write`, `MultiEdit`,
   `NotebookEdit`, `Bash`) in between. Waste = result tokens x 1.25.
4. **huge_result**: a tool result over `huge_tokens` (10,000). It is written to
   the cache once and re-read by every later call in the stream. Waste =
   (tokens - 2,000) x (1.25 + 0.1 x later calls in the stream).
5. **error_thrash**: 3 or more consecutive failed results of the same tool in a
   stream. Waste = the priced input of the model calls that issued the 3rd and
   later failing attempts.

Result tokens are estimated as characters / 4.

## Output
- Terminal report: totals, waste by detector (count, eq, % of priced input),
  top examples, one fix per detector.
- `--json`: the same data, machine-readable.
- `--card FILE`: self-contained HTML card with aggregates only: no paths,
  commands or file contents.

## Sources
v1: Claude Code (`~/.claude/projects/**/*.jsonl`). Next: Codex
(`~/.codex/sessions`). The `sources/` interface returns plain `Session`
objects, so detectors stay source-agnostic.
