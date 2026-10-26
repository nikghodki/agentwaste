"""Terminal and JSON rendering. The terminal report is local-only and may show
file names; the shareable card (card.py) never does."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime

from .analysis import Report


def human(n: float) -> str:
    for unit, size in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(n) >= size:
            return f"{n / size:.1f}{unit}"
    return f"{n:.0f}"


def _date(ts: float | None) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"


def _usd(eq: float, usd_per_mtok: float | None) -> str:
    return f" (~${eq / 1e6 * usd_per_mtok:,.0f})" if usd_per_mtok else ""


def render_text(r: Report, usd_per_mtok: float | None = None, top: int = 3) -> str:
    lines = [
        f"agentwaste: {r.sessions} sessions, {r.model_calls:,} model calls, {r.tool_calls:,} tool calls"
        f"  ({_date(r.first_ts)} to {_date(r.last_ts)})",
        "",
        f"Priced input: {human(r.priced_input)} token-equivalents{_usd(r.priced_input, usd_per_mtok)}"
        f"   (cache writes {human(r.cache_write)}, cache reads {human(r.cache_read)},"
        f" fresh {human(r.fresh_input)}; output {human(r.output)})",
        f"Estimated waste: {human(r.waste)} ({r.waste_pct:.0f}%){_usd(r.waste, usd_per_mtok)}   Grade: {r.grade}",
        "",
    ]
    info_header = False
    for f in r.findings:
        if not f.count:
            continue
        if not f.counted:
            if not info_header:
                lines += ["Not counted in the grade (self-hosted models: the cost is GPU time, not tokens):", ""]
                info_header = True
            lines.append(f"  info  {f.title}  ({f.count:,}x, {human(f.waste)} tokens re-processed)")
        else:
            pct = 100 * f.waste / r.priced_input if r.priced_input else 0
            lines.append(f"{pct:5.1f}%  {f.title}  ({f.count:,}x, {human(f.waste)} eq{_usd(f.waste, usd_per_mtok)})")
        for label, n in f.examples[:top]:
            lines.append(f"        - {label}: {n:,}x")
        lines += ["        " + l for l in textwrap.wrap("Fix: " + f.fix, 88)]
        lines.append("")
    if not any(f.count for f in r.findings):
        lines.append("No waste patterns found. Nice.")
    lines.append("Token-equivalents weight cache writes 1.25x (1-hour cache 2x) and cache reads 0.1x")
    lines.append("of fresh input. Estimates; see https://github.com/nikghodki/agentwaste for definitions.")
    return "\n".join(lines)


def to_json(r: Report, usd_per_mtok: float | None = None) -> str:
    data = {
        "sessions": r.sessions, "streams": r.streams, "model_calls": r.model_calls,
        "tool_calls": r.tool_calls, "fresh_input": r.fresh_input, "cache_write": r.cache_write,
        "cache_read": r.cache_read, "output": r.output, "priced_input": round(r.priced_input),
        "waste": round(r.waste), "waste_pct": round(r.waste_pct, 2), "grade": r.grade,
        "first_ts": r.first_ts, "last_ts": r.last_ts, "usd_per_mtok": usd_per_mtok,
        "findings": [
            {"key": f.key, "title": f.title, "count": f.count, "waste": round(f.waste), "counted": f.counted,
             "examples": [{"label": l, "count": n} for l, n in f.examples], "fix": f.fix}
            for f in r.findings
        ],
    }
    return json.dumps(data, indent=2)
