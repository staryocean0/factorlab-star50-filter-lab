# 同期同频尾部研究工作流

先读[结果](result.md)、[结果前协议](protocol.md)和[数据声明](data_usage.json)。本次是市场测量，不运行策略优化，不替代V2账户审计。

代码：`src/star50_filter/tail_distribution.py`；执行器：`scripts/research_tail_distribution_v1.py`；报告：`scripts/report_tail_distribution_v1.py`；测试：`tests/test_tail_distribution.py`。

首次过程：

```bash
python -m pytest -q tests/test_tail_distribution.py
python scripts/research_tail_distribution_v1.py freeze
python scripts/research_tail_distribution_v1.py prepare
python scripts/research_tail_distribution_v1.py analyze --minutes 1
python scripts/research_tail_distribution_v1.py analyze --minutes 5
python scripts/report_tail_distribution_v1.py
```

现有输出不可覆盖；已完成后查看HTML/CSV即可，不为看图重算。完整重放需独立空目录/checkout及相同DataHub固定输入。1m/5m分析可独立并行，最终24项Holm必须合并处理。运行环境沿用FactorLab `.venv/bin/python`，资源runner记录在本次artifact根目录的resource_1m/resource_5m。

`panel_1m.parquet` / `panel_5m.parquet`保留两指数共同时间上的收益、过去σ、边界分解和事前时间；`cutoffs_*`是共同标定阈值。`1m/`和`5m/`各自保存年度分布、经济幅度阈值计数、事件、尾簇、条件、概率和999次置换数组。

最终[HTML](../../../artifacts/tail_distribution_v1/final/report.html)链接尾分布、波动条件、幅度×异常交叉表、预测评分、时段边界以及整体校正检验。`largest_events.csv`是事后案例表，不是首次预测输入。

数值定义：σ_t截止t−1；当前r_t仅为待预测事件标签。会话首棒不进入普通r，边界单列；最近尾部标记不跨会话。训练段标签按最终标定阈值定义，仅用于拟合；不能称为当年在线已知阈值。只有后两年固定风险概率比较具本轮先后顺序，仍不具fresh OOS权威。
