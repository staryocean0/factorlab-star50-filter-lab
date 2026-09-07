# 分辨率与迁移复现工作流

入口：[结果](result.md) → [结果前合同](protocol.md) → [数据使用声明](data_usage.json)。

主执行器 `scripts/research_resolution_transfer_v1.py`，数学测量 `src/star50_filter/resolution_measurement.py`，报告 `scripts/report_resolution_transfer_v1.py`，独立样本核对 `scripts/audit_resolution_formula_v1.py`。

使用本机FactorLab `.venv/bin/python` 执行统计和策略。DataHub的精确grant检查通过其自身 `.venv/bin/python` 和 `star50_history_bbo_onboarding.py coverage`，不向DataHub环境安装scipy/torch，也不修改DataHub代码、数据版本或授权。

过程命令（现有工件不可覆盖）：

```bash
python scripts/research_resolution_transfer_v1.py freeze
python scripts/research_resolution_transfer_v1.py seconds --year 2024
python scripts/research_resolution_transfer_v1.py seconds --year 2025
python scripts/research_resolution_transfer_v1.py migration --year 2021
```

迁移每年必须由主控阅读summary/trades，写review.json绑定当年receipt的SHA后才运行下一年，直到2025；不生成参数候选、不根据表现切换V1/V2。秒级年度测量是两个独立描述性任务，可以并行，其结果不影响迁移。

```bash
python -m pytest -q
python scripts/report_resolution_transfer_v1.py
python scripts/audit_resolution_formula_v1.py
```

已运行完成，不应为查看图表重跑。完整重放需要独立空目录/checkout和同一来源，保留原始freeze及历史字节。报告主要只读现有工件；独立现金对账按固定年度重新读取受限1m原始开盘，秒级直接求和核对仅读取两个已列明的真实日，不宣称全量独立复验。

[HTML总报告](../../../artifacts/resolution_transfer_v1/final/report.html)、[分辨率图](../../../artifacts/resolution_transfer_v1/final/resolution_comparison.png)、[迁移图](../../../artifacts/resolution_transfer_v1/final/migration_comparison.png)、[精确数据表](../../../artifacts/resolution_transfer_v1/final/resolution_summary.csv)、[验证](../../../artifacts/resolution_transfer_v1/final/validation.json)、[710例直接公式审计](../../../artifacts/resolution_transfer_v1/formula_audit.json)。

秒级source/coverage与完整测量放在 `artifacts/resolution_transfer_v1/seconds_2024` 和 `seconds_2025`；迁移五年各有`migration_YEAR`。`measurements.parquet`是所有有效测量，`common_support.parquet`是五网格共同ER支持；最终var60还取五网格共同方差支持。缺失不能前填，零路程不能设ER=0。
