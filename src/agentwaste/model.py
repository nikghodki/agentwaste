"""Source-agnostic session model. Sources (sources/*.py) produce these;
detectors only ever see these."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict
    has_result: bool = False
    result_tokens: int = 0  # estimated: characters / 4
    is_error: bool = False


@dataclass
class ModelCall:
    id: str
    ts: float  # unix seconds
    model: str = ""
    input: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    output: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def cache_write(self) -> int:
        return self.cache_write_5m + self.cache_write_1h


@dataclass
class Stream:
    """One cache context: a session's main thread, or one of its sidechains
    (subagents), which keep their own cache."""

    session_id: str
    sidechain: bool
    project: str = ""
    source: str = ""
    calls: list[ModelCall] = field(default_factory=list)
