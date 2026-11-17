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
