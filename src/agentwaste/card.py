"""Shareable "Wrapped"-style card: one self-contained HTML file with
aggregates only. It must never contain file paths, project names, commands
or any session content -- tests/test_report_and_cli.py enforces this."""

from __future__ import annotations

import html
from datetime import datetime

from .analysis import Report
from .report import human

_CSS = """
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#0f1115;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#f5f5f5}
.card{width:420px;padding:32px;border-radius:20px;background:linear-gradient(160deg,#1d2533,#2a1a2e)}
.k{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#a3a9b8}
.grade{font-size:96px;font-weight:800;line-height:1;margin:8px 0}
.big{font-size:28px;font-weight:700}
.row{display:flex;justify-content:space-between;margin:10px 0;font-size:15px}
.bar{height:8px;border-radius:4px;background:#ff7a59;margin-top:4px}
.foot{margin-top:24px;font-size:12px;color:#a3a9b8}
"""


def render_card(r: Report) -> str:
    rows = []
    for f in r.findings[:3]:
        if not f.count or not r.priced_input:
            continue
        pct = 100 * f.waste / r.priced_input
        rows.append(f'<div class="row"><span>{html.escape(f.title)}</span><span>{pct:.0f}%</span></div>'
                    f'<div class="bar" style="width:{max(2, min(100, pct)):.0f}%"></div>')
    span = ""
    if r.first_ts and r.last_ts:
        days = max(1, round((r.last_ts - r.first_ts) / 86400))
        span = f"{days} days"
    made = datetime.now().strftime("%Y-%m-%d")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>My agent waste</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>{_CSS}</style></head>
<body><div class="card">
<div class="k">My AI coding agent, {html.escape(span)}</div>
<div class="grade">{r.grade}</div>
<div class="big">{r.waste_pct:.0f}% of input tokens wasted</div>
<div class="k" style="margin-top:6px">{human(r.priced_input)} token-equivalents across {r.sessions} sessions</div>
<div style="margin-top:24px">{''.join(rows)}</div>
<div class="foot">Made {made} with agentwaste &middot; github.com/nikghodki/agentwaste</div>
</div></body></html>
"""
