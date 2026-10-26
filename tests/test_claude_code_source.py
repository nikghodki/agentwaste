from agentwaste.sources.claude_code import load


def T(sec):
    return f"2026-10-01T10:{sec // 60:02d}:{sec % 60:02d}.000Z"


def test_split_assistant_records_count_usage_once_and_keep_every_tool_call(transcript):
    t = transcript()
    t.assistant(T(0), "m1", input=10, cache_write=100, cache_read=1000, output=5, split=True,
                tools=[("t1", "Read", {"file_path": "/a.py"}), ("t2", "Grep", {"pattern": "x"})])
    t.write()
    [stream] = load(t.path.parent.parent)
    [call] = stream.calls
    assert (call.input, call.cache_write_5m, call.cache_read, call.output) == (10, 100, 1000, 5)
    assert [tc.name for tc in call.tool_calls] == ["Read", "Grep"]


def test_tool_results_are_linked_with_estimated_tokens_and_errors(transcript):
    t = transcript()
    t.assistant(T(0), "m1", tools=[("t1", "Bash", {"command": "make"})])
    t.result(T(1), "t1", text="x" * 4000, is_error=True)
    t.write()
    [tc] = load(t.path.parent.parent)[0].calls[0].tool_calls
    assert tc.has_result and tc.is_error
    assert 990 <= tc.result_tokens <= 1010  # ~chars / 4


def test_sidechains_are_separate_streams(transcript):
    main = transcript("main.jsonl")
    main.assistant(T(0), "m1").write()
    sub = transcript("sub.jsonl", sidechain=True)
    sub.assistant(T(5), "m2").write()
    streams = load(main.path.parent.parent)
    assert sorted(s.sidechain for s in streams) == [False, True]


def test_one_hour_cache_writes_are_separated(transcript):
    t = transcript()
    t.assistant(T(0), "m1", cache_write=30000, cache_1h=20000).write()
    call = load(t.path.parent.parent)[0].calls[0]
    assert (call.cache_write_5m, call.cache_write_1h) == (10000, 20000)


def test_malformed_lines_and_non_message_records_are_skipped(transcript):
    t = transcript()
    t.raw("{not json").raw('{"type": "file-history-snapshot"}')
    t.assistant(T(0), "m1", input=7).write()
    [stream] = load(t.path.parent.parent)
    assert stream.calls[0].input == 7


def test_calls_are_time_ordered_and_since_filters_old_calls(transcript):
    t = transcript()
    t.assistant(T(120), "late").assistant(T(0), "early").write()
    stream = load(t.path.parent.parent)[0]
    assert [c.id for c in stream.calls] == ["early", "late"]
    cutoff = stream.calls[0].ts + 60
    [only] = load(t.path.parent.parent, since=cutoff)
    assert [c.id for c in only.calls] == ["late"]


def test_project_name_comes_from_the_working_directory(transcript):
    t = transcript()
    t.assistant(T(0), "m1").write()
    assert load(t.path.parent.parent)[0].project == "project"


def test_synthetic_placeholder_messages_are_ignored(transcript):
    t = transcript()
    t.assistant(T(0), "m1", input=5, model="<synthetic>").assistant(T(1), "m2", input=7)
    t.write()
    [stream] = load(t.path.parent.parent)
    assert [c.id for c in stream.calls] == ["m2"]
