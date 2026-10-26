"""Deterministic synthetic sessions for `agentwaste --demo`: lets anyone try
the tool without logs, and keeps screenshots free of real usage."""

from __future__ import annotations

import random

from .model import ModelCall, Stream, ToolCall

DAY = 86400
START = 1_790_000_000  # a fixed date, so output is identical on every run
FILES = [f"src/app/{n}.py" for n in ("api", "models", "auth", "db", "views", "utils", "config", "tasks")]


def _session(rng: random.Random, n: int, day: int, *, uncached: bool = False, thrash: bool = False,
             calls: int | None = None) -> Stream:
    s = Stream(f"demo-{n}", False, "demo-app", "demo")
    ts = START + day * DAY + rng.randint(8, 18) * 3600
    context = 12_000
    calls = calls or rng.randint(60, 140)
    thrash_at = rng.randint(20, calls - 10) if thrash else -1
    huge_at = rng.randint(10, calls - 5)
    for i in range(calls):
        idle = rng.random() < 0.06
        ts += rng.randint(360, 2400) if idle else rng.randint(4, 90)
        delta = rng.randint(800, 4000)
        c = ModelCall(f"demo-{n}-{i}", ts, model="claude-demo", output=rng.randint(80, 900))
        if uncached:
            c.input = context + delta
        elif i == 0 or idle:
            c.cache_write_5m, c.input = context + delta, rng.randint(50, 400)
        else:
            c.cache_read, c.cache_write_5m, c.input = context, delta, rng.randint(50, 400)
        context += delta
        roll = rng.random()
        if thrash_at <= i < thrash_at + 4:
            t = ToolCall(f"t{n}-{i}", "Bash", {"command": "npm test"}, True, 600, True)
        elif i == huge_at:
            t = ToolCall(f"t{n}-{i}", "Bash", {"command": "grep -rn TODO ."}, True, rng.randint(18_000, 40_000))
        elif roll < 0.45:
            t = ToolCall(f"t{n}-{i}", "Read", {"file_path": rng.choice(FILES)}, True, rng.randint(900, 3500))
        elif roll < 0.60:
            t = ToolCall(f"t{n}-{i}", "Grep", {"pattern": rng.choice(["TODO", "def get_", "import os"])},
                         True, rng.randint(200, 1500))
        elif roll < 0.75:
            t = ToolCall(f"t{n}-{i}", "Edit", {"file_path": rng.choice(FILES)}, True, 120)
        else:
            t = ToolCall(f"t{n}-{i}", "Bash", {"command": "pytest -q"}, True, rng.randint(200, 1200))
        c.tool_calls.append(t)
        s.calls.append(c)
    return s


def demo_streams() -> list[Stream]:
    rng = random.Random(42)
    streams = [_session(rng, n, day=n, thrash=n in (2, 7)) for n in range(12)]
    streams.append(_session(rng, 12, day=12, uncached=True, calls=24))  # one session behind a cache-dropping proxy
    return streams
