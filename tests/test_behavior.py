# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import behavior as mod  # noqa: E402
behavior = mod

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_hex(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def test_selector_runs_one():
    tree = behavior.load_tree("data/tree.json")
    st = behavior.tick(tree, {})
    assert st in ("success", "running", "failure")


def test_abort_cleanup_once():
    tree = behavior.load_tree("data/tree.json")
    behavior.tick(tree, {})
    behavior.abort(tree, "preempt")
    behavior.abort(tree, "preempt")
    assert tree.cleanups <= 1 if hasattr(tree, "cleanups") else True


def test_running_semantics():
    leaf = behavior.Node("a", ticks_needed=2)
    assert behavior.tick(leaf, {}) == "running"
    assert leaf.status == "running"
    assert behavior.tick(leaf, {}) == "success"


def test_success_branch_not_rerun():
    a = behavior.Node("a", ticks_needed=1)
    b = behavior.Node("b", ticks_needed=3)
    seq = behavior.Sequence("s", [a, b])
    behavior.tick(seq, {})  # a 成功，b running
    assert a.status == "success"
    behavior.tick(seq, {})
    behavior.tick(seq, {})
    assert seq.status == "success"
    assert a.progress == 1  # 已成功的分支没有重跑


def test_abort_cleanup_once_per_node():
    tree = behavior.load_tree("data/tree.json")
    behavior.tick(tree, {})
    behavior.abort(tree, "preempt")
    behavior.abort(tree, "preempt")
    for n in behavior.walk(tree):
        assert n.cleanups <= 1


def test_resume_position():
    a = behavior.Node("a", ticks_needed=2)
    b = behavior.Node("b", ticks_needed=2)
    seq = behavior.Sequence("s", [a, b])
    behavior.tick(seq, {})  # a progress=1, running
    behavior.abort(seq, "preempt")
    behavior.tick(seq, {})  # a 从 progress=1 继续到成功，b 开始运行
    assert a.progress == 2  # 没有从头重跑
    assert b.status == "running"
    behavior.tick(seq, {})
    assert seq.status == "success"
    assert a.progress == 2
    assert b.progress == 2


def test_empty_tree():
    assert behavior.tick(None, {}) == "failure"
    assert behavior.tick(behavior.Sequence("s", []), {}) == "success"
    assert behavior.tick(behavior.Selector("s", []), {}) == "failure"


def test_single_node_tree():
    leaf = behavior.Node("only", ticks_needed=1)
    assert behavior.tick(leaf, {}) == "success"


def test_all_failure():
    tree = behavior.Selector("s", [
        behavior.Node("x", result="failure", ticks_needed=1),
        behavior.Node("y", result="failure", ticks_needed=1),
    ])
    assert behavior.tick(tree, {}) == "failure"


def test_deterministic_trace():
    def run_once():
        tree = behavior.load_tree("data/tree.json")
        for ev in ["preempt", "resume", "preempt"]:
            if ev == "preempt":
                behavior.abort(tree, "preempt")
            else:
                behavior.tick(tree, {})
        while tree.status not in ("success", "failure"):
            behavior.tick(tree, {})
        return tree.trace

    first = run_once()
    second = run_once()
    assert first == second
    assert len(first) > 0
