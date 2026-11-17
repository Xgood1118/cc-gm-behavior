# -*- coding: utf-8 -*-
"""命令行入口：按事件序列驱动行为树，输出轨迹。"""

import argparse
import json

import behavior as m

MAX_TICKS = 1000


def run(tree, events):
    """按事件驱动：preempt -> abort，其余事件 -> tick；事件耗尽后跑到终态。"""
    ctx = {}
    ticks = 0
    for ev in events:
        if ev == "preempt":
            m.abort(tree, "preempt")
        else:
            m.tick(tree, ctx)
            ticks += 1
    while (
        tree is not None
        and tree.status not in ("success", "failure")
        and ticks < MAX_TICKS
    ):
        m.tick(tree, ctx)
        ticks += 1
    return ticks


def main():
    ap = argparse.ArgumentParser(description="行为树中断与恢复")
    ap.add_argument("tree", help="行为树 JSON 文件路径")
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tree = m.load_tree(a.tree)
    with open(a.events, encoding="utf-8") as f:
        events = json.load(f)

    ticks = run(tree, events)
    trace = tree.trace if tree is not None else []
    summary = {
        "final_status": tree.status if tree is not None else "failure",
        "cleanups": sum(n.cleanups for n in m.walk(tree)) if tree is not None else 0,
        "ticks": ticks,
        "trace_len": len(trace),
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "trace": trace}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
