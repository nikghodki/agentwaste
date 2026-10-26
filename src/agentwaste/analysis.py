"""Rolls streams up into one Report: totals, ranked findings, waste %, grade."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .cost import priced_input
from .detectors import ALL_DETECTORS, Finding
from .model import Stream
from .sources import claude_code

GRADES = [(10, "A"), (20, "B"), (30, "C"), (45, "D")]


def grade(waste_pct: float) -> str:
    for limit, letter in GRADES:
        if waste_pct < limit:
            return letter
    return "F"


@dataclass
class Report:
    sessions: int = 0
    streams: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    fresh_input: int = 0
    cache_write: int = 0
    cache_read: int = 0
    output: int = 0
    priced_input: float = 0.0
    first_ts: float | None = None
    last_ts: float | None = None
    findings: list[Finding] = field(default_factory=list)

    @property
    def waste(self) -> float:
        # Detectors can overlap (a huge result that is also a re-read), so cap
        # the total at what was actually spent.
        return min(sum(f.waste for f in self.findings), self.priced_input)

    @property
    def waste_pct(self) -> float:
        return 100.0 * self.waste / self.priced_input if self.priced_input else 0.0

    @property
    def grade(self) -> str:
        return grade(self.waste_pct)


def analyze(source: list[Stream] | Path | str, since: float | None = None) -> Report:
    streams = source if isinstance(source, list) else claude_code.load(source, since=since)
    r = Report(streams=len(streams), sessions=len({s.session_id for s in streams}))
    for s in streams:
        for c in s.calls:
            r.model_calls += 1
            r.tool_calls += len(c.tool_calls)
            r.fresh_input += c.input
            r.cache_write += c.cache_write
            r.cache_read += c.cache_read
            r.output += c.output
            r.priced_input += priced_input(c)
            r.first_ts = c.ts if r.first_ts is None else min(r.first_ts, c.ts)
            r.last_ts = c.ts if r.last_ts is None else max(r.last_ts, c.ts)
    r.findings = sorted((d(streams) for d in ALL_DETECTORS), key=lambda f: f.waste, reverse=True)
    return r
