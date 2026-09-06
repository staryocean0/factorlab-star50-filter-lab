# 可执行工作流

研究协议先于本轮新属性—结果关联冻结在GitHub提交dda728840fb142061572e80334089ed3ed70b3f2。此前历史已消费，不宣称盲态。

```bash
python -m pip install -e . matplotlib
python scripts/export_drawdown_material.py
python scripts/run_cross_scale_root_cause.py prepare --data-dir artifacts/drawdown_material
```

`prepare`计算固定原策略、14视图属性与五偏移面板；不生成年度解释或变更策略。随后每次只打开一个年份：

```bash
python scripts/run_cross_scale_root_cause.py year --year 2021
```

主研究者检查该年度表、图与反例，编写包含year/observations/counterexamples/mechanism_status/next_year_fixed_protocol的JSON，再执行：

```bash
python scripts/run_cross_scale_root_cause.py seal --year 2021 --review /absolute/path/review-2021.json
```

2022—2025分别重复人工审查与封存，前一年度未封存不能打开下一年度。已封存年度禁止覆盖。**本仓库已完成的封存不要重跑year/seal覆盖；复核直接使用校验器。**需要重新生成整套证据时应在另一个隔离输出工作副本中复现，不改旧回执。

五个年度完成后，固定全局参照与结构实验：

```bash
OPENBLAS_NUM_THREADS=1 python scripts/run_cross_scale_root_cause.py analyze --data-dir artifacts/drawdown_material
python scripts/complete_cross_scale_root_cause.py
python -m pytest -q
python scripts/validate_cross_scale_root_cause.py --data-dir artifacts/drawdown_material
```

`analyze`不是年度策略搜索。它执行两族各40关联、两种错位参照、配对bootstrap、固定联合格、84合成波形、7频段组合和全十事件图。`complete`补齐已注册的条件持续时间、互斥事件贡献、14视图事件表与具体K线例图，不追加统计假说。

交付时对全部新代码、文档、图表、表格与依赖生成不可变manifest；`CURRENT_RESEARCH.md`是可变入口，不纳入封存内容。CI只读核验、重放原始账户，不重新发明年度审查或选择策略。

如果库中没有development-only载体，导出脚本按已批准边界过滤<=2025；切勿直接把2026当作双向滤波padding。所有GitHub旧轮次清单保留，不改生产或live registry。
