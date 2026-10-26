import pytest

from agentwaste.cost import W_CACHE_READ, W_CACHE_WRITE_1H, W_CACHE_WRITE_5M, priced_input
from agentwaste.detectors import (
    detect_duplicate_calls, detect_error_thrash, detect_huge_results, detect_idle_rebuilds,
    detect_rereads,
)
from agentwaste.model import ModelCall, Stream, ToolCall


def call(ts, *, cw=0, cw1h=0, cr=0, inp=0, tools=()):
    return ModelCall(id=f"m{ts}", ts=ts, input=inp, cache_write_5m=cw, cache_write_1h=cw1h,
                     cache_read=cr, tool_calls=list(tools))


def tool(name, inp, tokens=0, err=False, tid=None):
    return ToolCall(tid or f"{name}{id(inp)}", name, inp, has_result=True, result_tokens=tokens, is_error=err)


def stream(*calls):
    return Stream("s", False, "proj", "test", list(calls))


def test_priced_input_weights():
    c = call(0, inp=100, cw=1000, cw1h=1000, cr=10000)
    assert priced_input(c) == pytest.approx(100 + 1000 * W_CACHE_WRITE_5M + 1000 * W_CACHE_WRITE_1H + 10000 * W_CACHE_READ)


# --- idle cache rebuild ---------------------------------------------------

def test_idle_rebuild_after_cache_ttl_counts_extra_over_a_warm_read():
    f = detect_idle_rebuilds([stream(call(0, cw=50000), call(301, cw=40000))])
    assert f.count == 1
    assert f.waste == pytest.approx(40000 * (W_CACHE_WRITE_5M - W_CACHE_READ))


def test_no_idle_rebuild_within_ttl_or_when_small():
    s = stream(call(0, cw=50000), call(299, cw=40000), call(700, cw=5000))
    assert detect_idle_rebuilds([s]).count == 0


def test_one_hour_cache_uses_one_hour_ttl():
    s = stream(call(0, cw1h=50000), call(1800, cw1h=40000), call(1800 + 3601, cw1h=40000))
    f = detect_idle_rebuilds([s])
    assert f.count == 1
    assert f.waste == pytest.approx(40000 * (W_CACHE_WRITE_1H - W_CACHE_READ))


# --- re-reads ------------------------------------------------------------

def test_reread_of_unchanged_file_is_waste():
    a = tool("Read", {"file_path": "/a.py"}, tokens=800)
    b = tool("Read", {"file_path": "/a.py", "offset": 10}, tokens=500)
    f = detect_rereads([stream(call(0, tools=[a]), call(10, tools=[b]))])
    assert f.count == 1 and f.waste == pytest.approx(500 * W_CACHE_WRITE_5M)
    assert f.examples[0][0] == "/a.py"


def test_reread_after_editing_that_file_or_running_bash_is_not_waste():
    r1 = tool("Read", {"file_path": "/a.py"}, 100)
    ed = tool("Edit", {"file_path": "/a.py"})
    r2 = tool("Read", {"file_path": "/a.py"}, 100)
    sh = tool("Bash", {"command": "make"})
    r3 = tool("Read", {"file_path": "/a.py"}, 100)
    assert detect_rereads([stream(call(0, tools=[r1, ed, r2]), call(5, tools=[sh, r3]))]).count == 0


def test_editing_another_file_does_not_excuse_a_reread():
    s = stream(call(0, tools=[tool("Read", {"file_path": "/a.py"}, 100),
                              tool("Edit", {"file_path": "/b.py"}),
                              tool("Read", {"file_path": "/a.py"}, 100)]))
    assert detect_rereads([s]).count == 1


# --- duplicate read-only calls ---------------------------------------------

def test_identical_read_only_call_is_a_duplicate():
    s = stream(call(0, tools=[tool("Grep", {"pattern": "x"}, 300)]),
               call(9, tools=[tool("Grep", {"pattern": "x"}, 300)]))
    f = detect_duplicate_calls([s])
    assert f.count == 1 and f.waste == pytest.approx(300 * W_CACHE_WRITE_5M)


def test_duplicate_reset_by_mutation_and_bash_repeats_are_never_duplicates():
    s = stream(call(0, tools=[tool("Grep", {"pattern": "x"}, 300), tool("Write", {"file_path": "/a"}),
                              tool("Grep", {"pattern": "x"}, 300),
                              tool("Bash", {"command": "pytest"}), tool("Bash", {"command": "pytest"})]))
    assert detect_duplicate_calls([s]).count == 0


# --- huge results ----------------------------------------------------------

def test_huge_result_cost_includes_carrying_it_in_later_calls():
    big = tool("Bash", {"command": "grep -r foo ."}, tokens=12000)
    s = stream(call(0, tools=[big]), call(1), call(2), call(3))
    f = detect_huge_results([s])
    assert f.count == 1
    assert f.waste == pytest.approx((12000 - 2000) * (W_CACHE_WRITE_5M + W_CACHE_READ * 3))


def test_results_under_threshold_are_fine():
    s = stream(call(0, tools=[tool("Read", {"file_path": "/a"}, tokens=9999)]))
    assert detect_huge_results([s]).count == 0


# --- error thrash ------------------------------------------------------------

def test_three_consecutive_failures_of_one_tool_is_thrash():
    calls = [call(i, inp=1000, tools=[tool("Bash", {"command": "npm test"}, err=True, tid=f"b{i}")]) for i in range(4)]
    f = detect_error_thrash([stream(*calls)])
    assert f.count == 1                       # one episode
    assert f.waste == pytest.approx(2 * 1000)  # the 3rd and 4th attempts


def test_a_success_breaks_the_run():
    seq = [True, True, False, True, True]
    calls = [call(i, inp=10, tools=[tool("Bash", {"command": "x"}, err=e, tid=f"b{i}")]) for i, e in enumerate(seq)]
    assert detect_error_thrash([stream(*calls)]).count == 0
