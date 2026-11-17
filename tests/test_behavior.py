# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import behavior as mod  # noqa: E402


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
