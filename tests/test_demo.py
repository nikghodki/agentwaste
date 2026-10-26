from agentwaste.analysis import analyze
from agentwaste.cli import main
from agentwaste.demo import demo_streams


def test_demo_data_triggers_every_counted_detector():
    r = analyze(demo_streams())
    hit = {f.key for f in r.findings if f.count and f.counted}
    assert hit == {"idle_cache_rebuild", "uncached_context", "reread", "duplicate_call",
                   "huge_result", "error_thrash"}
    assert r.grade in {"C", "D"}  # a realistic, not cartoonish, result


def test_demo_data_is_deterministic():
    a, b = analyze(demo_streams()), analyze(demo_streams())
    assert (a.priced_input, a.waste) == (b.priced_input, b.waste)


def test_cli_demo_needs_no_logs(tmp_path, capsys):
    assert main(["--demo", "--path", str(tmp_path / "missing")]) == 0
    out = capsys.readouterr().out
    assert "demo data" in out.lower() and "Re-caching after idle breaks" in out
