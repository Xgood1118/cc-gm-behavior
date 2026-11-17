# -*- coding: utf-8 -*-
"""行为树中断与恢复"""



def Node:
    """class"""
    raise NotImplementedError("Node 尚未实现")


def Sequence:
    """class"""
    raise NotImplementedError("Sequence 尚未实现")


def Selector:
    """class"""
    raise NotImplementedError("Selector 尚未实现")


def tick(tree, ctx):
    """执行一次 tick"""
    raise NotImplementedError("tick 尚未实现")


def abort(tree, reason):
    """中断并清理"""
    raise NotImplementedError("abort 尚未实现")


def load_tree(path):
    """读入与落盘辅助"""
    raise NotImplementedError("load_tree 尚未实现")

