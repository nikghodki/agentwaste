"""PyPI renders README.md as the project page but can't resolve relative
paths, so every image and link must be absolute."""

import re
from pathlib import Path

import agentwaste

ROOT = Path(__file__).resolve().parent.parent


def test_readme_has_no_relative_links_or_images():
    readme = (ROOT / "README.md").read_text()
    targets = re.findall(r"\]\(([^)]+)\)", readme) + re.findall(r'src="([^"]+)"', readme)
    relative = [t for t in targets if not t.startswith(("http://", "https://", "#", "mailto:"))]
    assert not relative, f"relative links break on PyPI: {relative}"


def test_package_version_matches_pyproject():
    # Regex, not tomllib: tomllib is 3.11+ and agentwaste supports 3.10.
    version = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    assert version == agentwaste.__version__
