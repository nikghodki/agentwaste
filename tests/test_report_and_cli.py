import json

from agentwaste.analysis import analyze, grade
from agentwaste.card import render_card
from agentwaste.cli import main
from agentwaste.report import render_text, to_json


def T(sec):
    return f"2026-10-01T{10 + sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}.000Z"


def wasteful_session(transcript):
    t = transcript()
    t.assistant(T(0), "m1", input=100, cache_write=60000, output=50,
                tools=[("r1", "Read", {"file_path": "/home/dev/project/secret_config.yaml"})])
    t.result(T(1), "r1", text="k" * 4000)
    t.assistant(T(10), "m2", cache_read=60000, output=20,
                tools=[("r2", "Read", {"file_path": "/home/dev/project/secret_config.yaml"})])
    t.result(T(11), "r2", text="k" * 4000)
    t.assistant(T(700), "m3", cache_write=62000, output=30,  # back after a >5 min break
                tools=[("b1", "Bash", {"command": "cat /etc/hosts_private"})])
    t.result(T(701), "b1", text="z" * 60000)
    t.assistant(T(710), "m4", cache_read=80000, output=10)
    t.write()
    return t.path.parent.parent


def test_analysis_totals_rank_findings_and_grade(transcript):
    r = analyze(load_root := wasteful_session(transcript))
    assert r.sessions == 1 and r.model_calls == 4 and r.tool_calls == 3
    assert r.findings[0].key == "idle_cache_rebuild"  # biggest waste first
    assert {f.key for f in r.findings if f.count} >= {"idle_cache_rebuild", "reread", "huge_result"}
    assert 0 < r.waste_pct <= 100
    assert r.grade == grade(r.waste_pct)


def test_grade_bands():
    assert [grade(p) for p in (5, 15, 25, 40, 60)] == ["A", "B", "C", "D", "F"]


def test_text_report_has_headline_numbers_and_fixes(transcript):
    text = render_text(analyze(wasteful_session(transcript)))
    assert "Re-caching after idle breaks" in text
    assert "Fix:" in text and "/compact" in text
    assert "secret_config.yaml" in text  # local report may show the worst file


def test_json_is_machine_readable(transcript):
    data = json.loads(to_json(analyze(wasteful_session(transcript))))
    assert {"priced_input", "waste", "waste_pct", "grade", "findings"} <= data.keys()
    assert data["findings"][0]["key"] == "idle_cache_rebuild"


def test_card_contains_aggregates_only(transcript):
    html = render_card(analyze(wasteful_session(transcript)))
    assert html.lstrip().startswith("<!doctype html>")
    for private in ("secret_config", "/home/dev", "hosts_private", "project"):
        assert private not in html, f"card leaks {private!r}"
    assert "Re-caching after idle breaks" in html


def test_cli_prints_report(transcript, capsys):
    root = wasteful_session(transcript)
    assert main(["--path", str(root), "--days", "0"]) == 0
    assert "Re-caching after idle breaks" in capsys.readouterr().out


def test_cli_json_and_card(transcript, tmp_path, capsys):
    root = wasteful_session(transcript)
    card = tmp_path / "card.html"
    assert main(["--path", str(root), "--days", "0", "--json", "--card", str(card)]) == 0
    assert json.loads(capsys.readouterr().out)["grade"]
    assert card.read_text().startswith("<!doctype html>")


def test_cli_with_no_logs_explains_and_fails(tmp_path, capsys):
    assert main(["--path", str(tmp_path / "nothing")]) == 1
    assert "No Claude Code sessions found" in capsys.readouterr().err


def test_usd_estimate_is_optional(transcript, capsys):
    root = wasteful_session(transcript)
    main(["--path", str(root), "--days", "0"])
    assert "$" not in capsys.readouterr().out
    main(["--path", str(root), "--days", "0", "--usd-per-mtok", "15"])
    assert "$" in capsys.readouterr().out
