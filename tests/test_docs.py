"""Keeps the MDX docs in step with the code: navigation, quoted numbers, CLI
flags and component tags."""

import json
import re
from pathlib import Path

import pytest

from agentwaste import cost, detectors
from agentwaste.analysis import GRADES
from agentwaste.cli import build_parser

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PAGES = DOCS / "src" / "content" / "docs"
BASE = "/agentwaste/"


def nav_pages():
    groups = json.loads((DOCS / "sidebar.json").read_text())
    return ["index"] + [p for g in groups for p in g["items"]]


def mdx(page):
    return (PAGES / f"{page}.mdx").read_text()


@pytest.mark.parametrize("page", nav_pages())
def test_every_navigation_page_exists_with_a_title(page):
    text = mdx(page)
    assert re.match(r"---\ntitle: \".+\"", text), f"{page}: missing frontmatter title"


@pytest.mark.parametrize("page", nav_pages())
def test_mdx_component_tags_are_balanced(page):
    text = re.sub(r"```.*?```", "", mdx(page), flags=re.S)
    for tag in set(re.findall(r"<([A-Z][A-Za-z]+)[\s>]", text)):
        opens = len(re.findall(rf"<{tag}[\s>]", text)) - len(re.findall(rf"<{tag}[^>]*/>", text))
        assert opens == text.count(f"</{tag}>"), f"{page}: unbalanced <{tag}>"


@pytest.mark.parametrize("page", nav_pages())
def test_internal_links_point_at_real_pages(page):
    for link in re.findall(r'(?:\]\(|href="|link: )(/[^)"#\s]*)', mdx(page)):
        assert link.startswith(BASE), f"{page}: link {link} is missing the {BASE} base path"
        target = link[len(BASE):].strip("/") or "index"
        assert (PAGES / f"{target}.mdx").exists(), f"{page}: broken link {link}"


def test_every_page_is_in_the_sidebar():
    on_disk = {str(p.relative_to(PAGES).with_suffix("")) for p in PAGES.rglob("*.mdx")}
    assert on_disk == set(nav_pages())


def test_quickstart_shows_the_real_demo_output():
    from agentwaste.demo import demo_streams
    from agentwaste.analysis import analyze
    from agentwaste.report import render_text
    real = render_text(analyze(demo_streams())).splitlines()
    block = re.search(r"```text\n(.*?)```", mdx("quickstart"), re.S).group(1)
    shown = [l.strip() for l in block.splitlines() if l.strip() and not l.strip().endswith("...")]
    for line in shown:
        assert line in [r.strip() for r in real], f"quickstart shows {line!r}, not in the real --demo output"


def number(n):
    return f"{n:,}"


def test_detector_thresholds_quoted_in_docs_match_the_code():
    assert number(detectors.MIN_REBUILD) in mdx("detectors/idle-cache-rebuild")
    assert str(cost.TTL_5M) in mdx("detectors/idle-cache-rebuild")
    assert number(cost.TTL_1H) in mdx("detectors/idle-cache-rebuild")
    assert number(detectors.UNCACHED_MIN) in mdx("detectors/uncached-context")
    assert number(detectors.HUGE_TOKENS) in mdx("detectors/huge-result")
    assert number(detectors.HUGE_KEEP) in mdx("detectors/huge-result")
    assert f"**{detectors.THRASH_RUN}**" in mdx("detectors/error-thrash")
    for name in sorted(detectors.READ_ONLY_TOOLS):
        assert f"`{name}`" in mdx("detectors/duplicate-call")


def test_cost_weights_in_docs_match_the_code():
    page = mdx("how-it-works")
    for w in (cost.W_INPUT, cost.W_CACHE_WRITE_5M, cost.W_CACHE_WRITE_1H, cost.W_CACHE_READ):
        assert f"| {w:g} |" in page or f"| {w} |" in page, f"weight {w} missing from how-it-works"


def test_grade_bands_in_docs_match_the_code():
    page = mdx("how-it-works")
    for limit, letter in GRADES:
        assert f"{limit}%" in page and f"| {letter} |" in page


def test_every_cli_flag_is_documented():
    page = mdx("reference/cli")
    flags = {o for a in build_parser()._actions for o in a.option_strings if o.startswith("--")}
    for flag in flags - {"--help"}:
        assert re.search(rf"\| `{flag}[ `]", page), f"{flag} not documented in reference/cli.mdx"


def test_every_detector_key_is_documented():
    keys = {d([]).key for d in detectors.ALL_DETECTORS}
    page = mdx("detectors/overview")
    for key in keys:
        assert f"`{key}`" in page, f"{key} missing from detectors/overview.mdx"
