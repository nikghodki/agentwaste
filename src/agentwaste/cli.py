"""agentwaste command line."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .analysis import analyze
from .card import render_card
from .report import render_text, to_json
from .sources import claude_code


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentwaste",
                                description="Find where your AI coding agent wastes tokens, and how to stop it.")
    p.add_argument("--path", default=str(claude_code.DEFAULT_ROOT),
                   help="Claude Code projects directory (default: %(default)s)")
    p.add_argument("--days", type=float, default=30, help="look back this many days; 0 = all (default: 30)")
    p.add_argument("--json", action="store_true", help="print machine-readable JSON instead of the report")
    p.add_argument("--card", metavar="FILE", help="also write a shareable HTML card (aggregates only)")
    p.add_argument("--usd-per-mtok", type=float, metavar="USD",
                   help="show dollar estimates at this price per million input tokens")
    p.add_argument("--top", type=int, default=3, help="examples to show per finding (default: 3)")
    p.add_argument("--version", action="version", version=f"agentwaste {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).expanduser()
    since = time.time() - args.days * 86400 if args.days else None
    report = analyze(root, since=since)
    if not report.model_calls:
        print(f"No Claude Code sessions found in {root}"
              + (f" in the last {args.days:g} days" if args.days else "")
              + ". Try --days 0 or --path.", file=sys.stderr)
        return 1
    print(to_json(report, args.usd_per_mtok) if args.json else render_text(report, args.usd_per_mtok, args.top))
    if args.card:
        Path(args.card).write_text(render_card(report))
        if not args.json:
            print(f"\nShareable card written to {args.card}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
