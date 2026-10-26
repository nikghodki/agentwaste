"""Reads Claude Code transcripts: ~/.claude/projects/<project>/<session>.jsonl.

Format notes (observed):
- One assistant reply is split across several records sharing message.id;
  usage repeats on each, so it is counted once, while tool_use blocks are
  collected from all of them.
- Tool results arrive in later "user" records and link back by tool_use_id.
- usage.cache_creation may split cache writes into 5-minute and 1-hour TTLs.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from ..model import ModelCall, Stream, ToolCall

DEFAULT_ROOT = Path("~/.claude/projects").expanduser()


def _ts(value) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _result_tokens(content) -> int:
    if content is None:
        return 0
    text = content if isinstance(content, str) else json.dumps(content)
    return len(text) // 4


def _project(cwd: str | None, file: Path) -> str:
    if cwd:
        return os.path.basename(cwd.rstrip("/")) or cwd
    return file.parent.name


def discover(root: Path | str = DEFAULT_ROOT) -> list[Path]:
    return sorted(Path(root).expanduser().rglob("*.jsonl"))


def parse_file(path: Path) -> list[Stream]:
    streams: dict[tuple[str, bool], Stream] = {}
    calls: dict[tuple[str, bool, str], ModelCall] = {}
    tools: dict[str, ToolCall] = {}

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            sid = rec.get("sessionId") if isinstance(rec, dict) else None
            if not isinstance(msg, dict) or not sid:
                continue
            side = bool(rec.get("isSidechain"))
            key = (sid, side)
            stream = streams.get(key)
            if stream is None:
                stream = streams[key] = Stream(sid, side, _project(rec.get("cwd"), path), "claude-code")
            content = msg.get("content") if isinstance(msg.get("content"), list) else []

            if rec.get("type") == "assistant":
                mid = msg.get("id") or rec.get("uuid")
                ts = _ts(rec.get("timestamp"))
                # Claude Code writes "<synthetic>" placeholders (errors, interrupts)
                # with zero usage; they are not model calls.
                if not mid or ts is None or msg.get("model") == "<synthetic>":
                    continue
                call = calls.get((sid, side, mid))
                if call is None:
                    usage = msg.get("usage") or {}
                    written = usage.get("cache_creation_input_tokens") or 0
                    split = usage.get("cache_creation") or {}
                    w1h = split.get("ephemeral_1h_input_tokens") or 0
                    w5m = split.get("ephemeral_5m_input_tokens")
                    call = ModelCall(
                        id=mid, ts=ts, model=msg.get("model") or "",
                        input=usage.get("input_tokens") or 0,
                        cache_write_5m=(written - w1h) if w5m is None else w5m,
                        cache_write_1h=w1h,
                        cache_read=usage.get("cache_read_input_tokens") or 0,
                        output=usage.get("output_tokens") or 0,
                    )
                    calls[(sid, side, mid)] = call
                    stream.calls.append(call)
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id"):
                        tc = ToolCall(block["id"], block.get("name") or "", block.get("input") or {})
                        call.tool_calls.append(tc)
                        tools[tc.id] = tc

            elif rec.get("type") == "user":
                for block in content:
                    if not (isinstance(block, dict) and block.get("type") == "tool_result"):
                        continue
                    tc = tools.get(block.get("tool_use_id"))
                    if tc is not None:
                        tc.has_result = True
                        tc.result_tokens = _result_tokens(block.get("content"))
                        tc.is_error = bool(block.get("is_error"))

    for stream in streams.values():
        stream.calls.sort(key=lambda c: c.ts)
    return [s for s in streams.values() if s.calls]


def load(root: Path | str = DEFAULT_ROOT, since: float | None = None) -> list[Stream]:
    out = []
    for path in discover(root):
        for stream in parse_file(path):
            if since is not None:
                stream.calls = [c for c in stream.calls if c.ts >= since]
            if stream.calls:
                out.append(stream)
    return out
