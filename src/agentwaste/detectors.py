"""Waste detectors. Each takes streams and returns a Finding. Definitions
match design/2026-10-26-agentwaste-v1.md; change both together."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field

from .cost import TTL_1H, TTL_5M, W_CACHE_READ, W_CACHE_WRITE_1H, W_CACHE_WRITE_5M, priced_input
from .model import Stream

MIN_REBUILD = 20_000
HUGE_TOKENS = 10_000
HUGE_KEEP = 2_000  # a result this size is reasonable; only the excess counts
THRASH_RUN = 3

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MUTATING_TOOLS = EDIT_TOOLS | {"Bash"}
READ_ONLY_TOOLS = {"Grep", "Glob", "LS", "WebFetch", "WebSearch"}


@dataclass
class Finding:
    key: str
    title: str
    fix: str
    count: int = 0
    waste: float = 0.0  # eq
    examples: list[tuple[str, int]] = field(default_factory=list)  # (label, occurrences)


def _top(counter: Counter, n: int = 3) -> list[tuple[str, int]]:
    return counter.most_common(n)


def detect_idle_rebuilds(streams: list[Stream]) -> Finding:
    f = Finding("idle_cache_rebuild", "Re-caching after idle breaks",
                "The prompt cache expires after 5 minutes idle, so the next message re-writes the whole "
                "context at 1.25x. Run /compact (or /clear) before a break, finish a thought before "
                "stepping away, or use the 1-hour cache for long sessions.")
    projects = Counter()
    for s in streams:
        for prev, cur in zip(s.calls, s.calls[1:]):
            if cur.cache_write < MIN_REBUILD:
                continue
            ttl = TTL_1H if cur.cache_write_1h > cur.cache_write_5m else TTL_5M
            if cur.ts - prev.ts > ttl:
                f.count += 1
                f.waste += (cur.cache_write_5m * (W_CACHE_WRITE_5M - W_CACHE_READ)
                            + cur.cache_write_1h * (W_CACHE_WRITE_1H - W_CACHE_READ))
                projects[s.project] += 1
    f.examples = _top(projects)
    return f


def detect_rereads(streams: list[Stream]) -> Finding:
    f = Finding("reread", "Re-reading unchanged files",
                "The agent read a file it had already read and not changed. Put the facts it keeps "
                "looking up (config values, key paths, conventions) in CLAUDE.md, or ask it to keep "
                "notes instead of re-opening the file.")
    files = Counter()
    for s in streams:
        seen: set[str] = set()
        for c in s.calls:
            for t in c.tool_calls:
                path = t.input.get("file_path") if isinstance(t.input, dict) else None
                if t.name == "Bash":
                    seen.clear()
                elif t.name in EDIT_TOOLS and path:
                    seen.discard(path)
                elif t.name == "Read" and path:
                    if path in seen:
                        f.count += 1
                        f.waste += t.result_tokens * W_CACHE_WRITE_5M
                        files[path] += 1
                    seen.add(path)
    f.examples = _top(files)
    return f


def detect_duplicate_calls(streams: list[Stream]) -> Finding:
    f = Finding("duplicate_call", "Repeating identical lookups",
                "The same search or fetch ran again with nothing changed in between. Ask the agent to "
                "reuse earlier results, or narrow the first search so it doesn't need repeating.")
    labels = Counter()
    for s in streams:
        seen: set[str] = set()
        for c in s.calls:
            for t in c.tool_calls:
                if t.name in MUTATING_TOOLS:
                    seen.clear()
                    continue
                if t.name not in READ_ONLY_TOOLS:
                    continue
                key = t.name + json.dumps(t.input, sort_keys=True, default=str)
                if key in seen:
                    f.count += 1
                    f.waste += t.result_tokens * W_CACHE_WRITE_5M
                    labels[t.name] += 1
                seen.add(key)
    f.examples = _top(labels)
    return f


def detect_huge_results(streams: list[Stream]) -> Finding:
    f = Finding("huge_result", "Huge tool outputs kept in context",
                "A command or read returned over 10k tokens, and the agent carried it in every later "
                "message. Pipe through head/tail, add filters or limits, read files in ranges, or use "
                "a code-search tool instead of recursive grep.")
    tools = Counter()
    for s in streams:
        n = len(s.calls)
        for i, c in enumerate(s.calls):
            later = n - i - 1
            for t in c.tool_calls:
                if t.result_tokens > HUGE_TOKENS:
                    f.count += 1
                    f.waste += (t.result_tokens - HUGE_KEEP) * (W_CACHE_WRITE_5M + W_CACHE_READ * later)
                    tools[t.name] += 1
    f.examples = _top(tools)
    return f


def detect_error_thrash(streams: list[Stream]) -> Finding:
    f = Finding("error_thrash", "Retry loops on failing commands",
                "The same tool failed 3+ times in a row. Stop and give the agent the missing context, "
                "put the fix in CLAUDE.md, or add a hook that halts after repeated failures.")
    tools = Counter()
    for s in streams:
        runs: Counter = Counter()
        for c in s.calls:
            for t in c.tool_calls:
                if not t.has_result:
                    continue
                if not t.is_error:
                    runs[t.name] = 0
                    continue
                runs[t.name] += 1
                if runs[t.name] == THRASH_RUN:
                    f.count += 1
                    tools[t.name] += 1
                if runs[t.name] >= THRASH_RUN:
                    f.waste += priced_input(c)
    f.examples = _top(tools)
    return f


ALL_DETECTORS = [detect_idle_rebuilds, detect_rereads, detect_duplicate_calls,
                 detect_huge_results, detect_error_thrash]
