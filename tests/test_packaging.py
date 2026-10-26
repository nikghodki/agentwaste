"""PyPI renders README.md as the project page but can't resolve relative
paths, so every image and link must be absolute."""

import re
import tomllib
from pathlib import Path

import agentwaste

ROOT = Path(__file__).resolve().parent.parent


def test_readme_has_no_relative_links_or_images():
    readme = (ROOT / "README.md").read_text()
    targets = re.findall(r"\]\(([^)]+)\)", readme) + re.findall(r'src="([^"]+)"', readme)
    relative = [t for t in targets if not t.startswith(("http://", "https://", "#", "mailto:"))]
    assert not relative, f"relative links break on PyPI: {relative}"


def test_package_version_matches_pyproject():
    meta = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert meta["project"]["version"] == agentwaste.__version__
