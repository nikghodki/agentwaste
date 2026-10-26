import json

import pytest


class TranscriptBuilder:
    """Writes synthetic Claude Code JSONL transcripts for tests. Never use real
    logs as fixtures: they contain code, paths and secrets."""

    def __init__(self, path, session="s1", sidechain=False):
        self.path = path
        self.session = session
        self.sidechain = sidechain
        self.records = []
        self._n = 0

    def _base(self, kind, ts):
        self._n += 1
        return {"type": kind, "sessionId": self.session, "isSidechain": self.sidechain,
                "timestamp": ts, "uuid": f"u{self._n}", "cwd": "/home/dev/project"}

    def assistant(self, ts, msg_id, *, input=0, cache_write=0, cache_read=0, output=0,
                  cache_1h=None, tools=(), model="claude-test", split=False):
        usage = {"input_tokens": input, "cache_creation_input_tokens": cache_write,
                 "cache_read_input_tokens": cache_read, "output_tokens": output}
        if cache_1h is not None:
            usage["cache_creation"] = {"ephemeral_5m_input_tokens": cache_write - cache_1h,
                                       "ephemeral_1h_input_tokens": cache_1h}
        blocks = [{"type": "tool_use", "id": tid, "name": name, "input": inp} for tid, name, inp in tools]
        chunks = [[b] for b in blocks] if split and blocks else [blocks or [{"type": "text", "text": "ok"}]]
        for chunk in chunks:
            rec = self._base("assistant", ts)
            rec["message"] = {"id": msg_id, "role": "assistant", "model": model, "usage": usage, "content": chunk}
            self.records.append(rec)
        return self

    def result(self, ts, tool_id, text="", is_error=False):
        rec = self._base("user", ts)
        rec["message"] = {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_id, "content": text, "is_error": is_error}]}
        self.records.append(rec)
        return self

    def raw(self, line):
        self.records.append(line)
        return self

    def write(self):
        with open(self.path, "w") as fh:
            for r in self.records:
                fh.write((r if isinstance(r, str) else json.dumps(r)) + "\n")
        return self.path


@pytest.fixture
def transcript(tmp_path):
    def make(name="session.jsonl", **kw):
        project = tmp_path / "projects" / "-home-dev-project"
        project.mkdir(parents=True, exist_ok=True)
        return TranscriptBuilder(project / name, **kw)
    return make
