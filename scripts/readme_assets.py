"""Regenerate the README images from --demo data (never real logs):
assets/card.png and assets/report.png. Needs Google Chrome or Chromium.

    python scripts/readme_assets.py
"""

import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentwaste.analysis import analyze  # noqa: E402
from agentwaste.card import render_card  # noqa: E402
from agentwaste.demo import demo_streams  # noqa: E402
from agentwaste.report import render_text  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "chromium", "chromium-browser"]

TERMINAL = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#0f1115}
.win{margin:24px;border-radius:12px;background:#161a22;box-shadow:0 10px 40px #0008;overflow:hidden}
.bar{height:34px;background:#1f2430;display:flex;align-items:center;gap:8px;padding:0 14px}
.dot{width:12px;height:12px;border-radius:50%}
pre{margin:0;padding:18px 22px 22px;color:#d7dae0;font:14px/1.5 "SF Mono",Menlo,Consolas,monospace;white-space:pre}
.cmd{color:#8fd18f}.pct{color:#ff9e85;font-weight:700}.fix{color:#9aa4b2}.hl{color:#fff;font-weight:700}
</style></head><body><div class="win"><div class="bar">
<span class="dot" style="background:#ff5f57"></span><span class="dot" style="background:#febc2e"></span><span class="dot" style="background:#28c840"></span>
</div><pre>{body}</pre></div></body></html>"""


def chrome() -> str:
    for c in CHROMES:
        if os.path.exists(c) or shutil.which(c):
            return c
    sys.exit("Google Chrome or Chromium is needed to render the images")


def shot(page: str, out: Path, width: int, height: int) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(page)
    subprocess.run([chrome(), "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--window-size={width},{height}", f"--screenshot={out}", f"file://{fh.name}"],
                   check=True, capture_output=True)
    os.unlink(fh.name)


def terminal_html(text: str, max_findings: int = 4) -> str:
    lines, shown = [], 0
    for line in text.splitlines():
        if line.lstrip().startswith(("Token-equivalents", "of fresh input")):
            continue
        if line[:6].strip().endswith("%"):
            shown += 1
            if shown > max_findings:
                break
        esc = html.escape(line)
        if line[:6].strip().endswith("%"):
            esc = f'<span class="pct">{esc[:6]}</span><span class="hl">{esc[6:]}</span>'
        elif "Fix:" in line or (line.startswith("        ") and not line.strip().startswith("-")):
            esc = f'<span class="fix">{esc}</span>'
        elif line.startswith("Estimated waste"):
            esc = f'<span class="hl">{esc}</span>'
        lines.append(esc)
    body = '<span class="cmd">$ agentwaste</span>\n\n' + "\n".join(lines).rstrip()
    return TERMINAL.replace("{body}", body)


def main() -> None:
    report = analyze(demo_streams())
    ASSETS.mkdir(exist_ok=True)
    shot(render_card(report), ASSETS / "card.png", 520, 600)
    text = render_text(report).replace("Showing demo data", "")
    rows = terminal_html(text).count("\n") + 4
    shot(terminal_html(text), ASSETS / "report.png", 1000, 30 + rows * 21)
    print("wrote", ASSETS / "card.png", "and", ASSETS / "report.png")


if __name__ == "__main__":
    main()
