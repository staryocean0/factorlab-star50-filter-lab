# 执行审计工作流

读取 `preregistration.json`、`clock_amendment.json`、`repair_amendment.json`。本轮沿用仓库strategy-slice-rebuild的年度审阅和证据封存；按本主题显式边界使用2021—2025五年，不引入通用Skill示例的2009—2020、两浪、隔夜开盘或多因子工程。

```bash
python -m pip install -e .
python -m pip install 'matplotlib>=3.9,<4'
python scripts/validate_drawdown_study.py
python -m pytest -q
```

准备输入：使用仓库的 `scripts/export_drawdown_material.py` 导出的已封存2020—2025载体，或指定含这些精确载体的目录。runner只接受既有原始文件或已封存导出文件的SHA256，Parquet读取使用截至本年度的过滤器。

每次只执行一个年度：

```bash
python scripts/run_execution_audit.py --data-dir artifacts/drawdown_material prepare --year 2021
```

主代理阅读该年 `annual.svg`、`annual_metrics.csv`、`top10_events.csv`、`opportunity_attribution.csv`、`source_audit.json` 后，手写 `analysis.json`，再执行：

```bash
python scripts/run_execution_audit.py seal --year 2021
```

之后才允许用同一方式打开2022，以此进行五个独立的人工审阅会话。不得批量生成年度归因或改写已经封存的年份。重放用于代码验证时应在隔离输出副本或新的审计版本中进行，不在封存目录覆盖。

五年全部封存后，执行快照推导：

```bash
python scripts/finalize_execution_audit.py
python scripts/finalize_execution_audit.py --validate-only
```

结项manifest绑定全部最终源、协议、文档、年度证据与报告；新增报告不重新运行策略或账户调度。`--validate-only`恢复200个快照并验证原始数组摘要、会计恒等式、源界限、连续年度持仓、冻结参数和逐年摘要链。GitHub Actions `execution-audit`在最终提交上验证这一流程，并同时验证旧70文件封存包和全部测试。

报告状态只能在已满足的范围内陈述。源盘中版本和可交易产品映射未闭合时保留测量结果，禁止升级生产权限或声称新样本验证。2026永远不作为本轮补充验证集。
