"""The report ends with a card command the user can paste. It must match how
agentwaste was started: under `uvx` nothing is installed, so a bare
`agentwaste` would be "command not found" (users hit exactly that)."""

from agentwaste.cli import invocation


def test_uvx_runs_from_the_uv_cache():
    assert invocation("/Users/a/.cache/uv/archive-v0/Zx91/bin/agentwaste") == "uvx agentwaste"
    assert invocation("/home/a/.cache/uv/builds-v0/.tmp1/bin/agentwaste") == "uvx agentwaste"


def test_installed_tools_use_the_plain_command():
    assert invocation("/Users/a/.local/bin/agentwaste") == "agentwaste"
    assert invocation("/Users/a/.local/share/uv/tools/agentwaste/bin/agentwaste") == "agentwaste"
    assert invocation("/opt/venv/bin/agentwaste") == "agentwaste"


def test_pipx_run_and_python_m():
    assert invocation("/Users/a/.local/pipx/.cache/abc/bin/agentwaste") == "pipx run agentwaste"
    assert invocation("/repo/src/agentwaste/__main__.py") == "python -m agentwaste"


def test_report_footer_suggests_the_card_command(transcript, capsys, monkeypatch):
    from agentwaste.cli import main
    monkeypatch.setattr("sys.argv", ["/Users/a/.cache/uv/archive-v0/Zx91/bin/agentwaste"])
    assert main(["--demo"]) == 0
    # --demo is kept, so the card matches the report the user just saw.
    assert "uvx agentwaste --demo --card agentwaste-card.html" in capsys.readouterr().out


def test_no_footer_in_json_or_when_a_card_was_written(tmp_path, capsys):
    from agentwaste.cli import main
    main(["--demo", "--json"])
    assert "--card" not in capsys.readouterr().out
    main(["--demo", "--card", str(tmp_path / "c.html")])
    out = capsys.readouterr().out
    assert "Shareable card written to" in out and "Share your grade:" not in out
