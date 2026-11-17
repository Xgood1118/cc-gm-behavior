# -*- coding: utf-8 -*-
"""行为树中断与恢复。

语义约定：
- 状态机：idle -> running -> success/failure；abort 把 running 节点打回 idle。
- 叶节点需要 ticks_needed 次 tick 才给出最终结果（result）。
- success/failure 是锁存状态：已成功的分支重复 tick 不会重跑。
- Sequence/Selector 记住正在运行的子节点位置，中断恢复后从该位置继续。
- abort 只对 running 节点执行清理，且每个节点每次中断只清理一次。
- 所有状态转移追加到根节点的 trace，可还原整条轨迹。
"""

import json

__all__ = [
    "Node",
    "Sequence",
    "Selector",
    "tick",
    "abort",
    "load_tree",
    "walk",
]

IDLE = "idle"
RUNNING = "running"
SUCCESS = "success"
FAILURE = "failure"
TERMINAL = (SUCCESS, FAILURE)


class Node:
    """叶节点：累计 ticks_needed 次 tick 后进入 result 状态。"""

    def __init__(self, name=None, children=None, result=SUCCESS, ticks_needed=2):
        self.name = name or "node"
        self.children = list(children) if children else []
        for child in self.children:
            child.parent = self
        self.parent = None
        self.result = result
        self.ticks_needed = max(1, int(ticks_needed))
        self.status = IDLE
        self.progress = 0
        self.cleanups = 0
        self.tick_count = 0  # 仅根节点的计数有意义
        self.trace = []      # 仅根节点的日志有意义

    # ---- 内部辅助 ----

    def _root(self):
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def _set(self, status, reason):
        if self.status == status:
            return
        old = self.status
        self.status = status
        root = self._root()
        root.trace.append({
            "tick": root.tick_count,
            "node": self.name,
            "from": old,
            "to": status,
            "reason": reason,
        })

    # ---- 行为 ----

    def tick(self, ctx):
        """叶节点执行一步；running 直到进度满。"""
        if self.status in TERMINAL:
            return self.status
        self._set(RUNNING, "tick")
        self.progress += 1
        if self.progress >= self.ticks_needed:
            self._set(self.result, "complete")
        return self.status

    def abort(self, reason):
        """中断运行中的子树并清理；清理对每个节点只生效一次。"""
        if self.status == RUNNING:
            self.cleanups += 1
            self._set(IDLE, "abort:%s" % reason)
        for child in self.children:
            child.abort(reason)


class Sequence(Node):
    """顺序执行：任一子节点失败即失败，全部成功才成功。

    index 记住当前子节点，中断恢复后从第一个未成功的子节点继续。
    """

    def __init__(self, name=None, children=None, **kwargs):
        super().__init__(name or "sequence", children, **kwargs)
        self.index = 0

    def tick(self, ctx):
        if self.status in TERMINAL:
            return self.status
        if not self.children:
            self._set(SUCCESS, "empty")
            return self.status
        self._set(RUNNING, "tick")
        while self.index < len(self.children):
            child = self.children[self.index]
            if child.status == SUCCESS:
                self.index += 1
                continue
            status = child.tick(ctx)
            if status == SUCCESS:
                self.index += 1
                continue
            if status == FAILURE:
                self._set(FAILURE, "child-failed")
                return self.status
            return self.status  # running
        self._set(SUCCESS, "complete")
        return self.status


class Selector(Node):
    """优先级选择：靠前的子节点优先级更高。

    index 记住正在运行的分支；每次 tick 先重新评估更高优先级的分支，
    若可运行则抢占（abort）当前低优先级分支。
    """

    def __init__(self, name=None, children=None, **kwargs):
        super().__init__(name or "selector", children, **kwargs)
        self.index = 0

    def tick(self, ctx):
        if self.status in TERMINAL:
            return self.status
        if not self.children:
            self._set(FAILURE, "empty")
            return self.status
        self._set(RUNNING, "tick")
        # 高优先级分支重新评估，可运行则抢占当前分支
        for i in range(min(self.index, len(self.children))):
            child = self.children[i]
            if child.status in TERMINAL:
                continue
            status = child.tick(ctx)
            if status in (RUNNING, SUCCESS):
                current = self.children[self.index] if self.index < len(self.children) else None
                if current is not None and current.status == RUNNING:
                    current.abort("preempt")
                self.index = i
                if status == SUCCESS:
                    self._set(SUCCESS, "child-succeeded")
                return self.status
        # 从记住的位置继续
        for i in range(self.index, len(self.children)):
            child = self.children[i]
            if child.status == SUCCESS:
                self._set(SUCCESS, "child-succeeded")
                return self.status
            status = child.tick(ctx)
            if status == SUCCESS:
                self.index = i
                self._set(SUCCESS, "child-succeeded")
                return self.status
            if status == RUNNING:
                self.index = i
                return self.status
            # failure：尝试下一个
        self._set(FAILURE, "all-failed")
        return self.status


def tick(tree, ctx):
    """执行一次 tick；空树（None）确定返回 failure。"""
    if tree is None:
        return FAILURE
    tree.tick_count += 1
    return tree.tick(ctx if ctx is not None else {})


def abort(tree, reason):
    """中断并清理；空树为 no-op。"""
    if tree is None:
        return
    tree.abort(reason)


def walk(tree):
    """先序遍历所有节点。"""
    yield tree
    for child in tree.children:
        for node in walk(child):
            yield node


def load_tree(path):
    """从 JSON 文件构建行为树；空文件/空对象返回 None。"""
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    if not spec:
        return None
    return _build(spec)


def _build(spec):
    kind = spec.get("type")
    children = [_build(c) for c in spec.get("children", [])]
    if kind == "sequence":
        return Sequence(spec.get("name"), children)
    if kind == "selector":
        return Selector(spec.get("name"), children)
    if kind == "leaf":
        return Node(
            spec.get("name"),
            result=spec.get("result", SUCCESS),
            ticks_needed=spec.get("ticks", 2),
        )
    raise ValueError("unknown node type: %r" % (kind,))
