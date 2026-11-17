# 行为树中断与恢复

一个能在运行中被打断、之后从正确位置恢复的行为树执行器

## 保留签名

- `Node`
- `Sequence`
- `Selector`
- `tick(tree, ctx)`
- `abort(tree, reason)`

## 自测

```
python -m pytest tests -q
python -m behavior.cli data/tree.json --events data/events.json --out trace.json
```

## 运行结果

`python -m behavior.cli data/tree.json --events data/events.json --out trace.json`
（事件序列：`["preempt", "resume", "preempt"]`）：

| 指标 | 值 |
| --- | --- |
| 最终状态 | `success` |
| 清理次数 | 3（selector / sequence / patrol 各一次，重复 abort 不重复清理） |
| tick 总次数 | 3 |
| 轨迹长度 | 14 条状态转移 |

轨迹要点：tick 1 启动 `patrol`（running）→ `preempt` 中断并清理运行链 →
tick 2 从 `patrol` 原进度恢复并成功、转而运行 `attack` → tick 3 `attack`
成功，整树 `success`。同一事件序列重复执行，轨迹逐条一致。
