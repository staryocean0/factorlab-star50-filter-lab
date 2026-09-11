# D3 复现与证据边界

本目录的D3评价已完成，结论为D3_INCREMENTAL_UTILITY_NOT_SUPPORTED，不是待跑任务。
先读PROTOCOL.md、RESULTS.md、DECISIVE_RECEIPT.json和EXECUTION_RECEIPT.json。

完整原始结果包包含results/FROZEN_PROBES.json、三个期限逐行预测、12份块统计、全部切片/描述、执行日志、输入ZIP和SOURCE/OUTPUT清单。完整结果包是本会话文件，不是Actions统计产物。仓库保留可审计代码、事前协议/冻结回执、全部主比较/失败门槛和结果哈希。输入转运artifact10273059875仅用于旧数据格式转换。

在解压结果包的根目录，以Python3.13.5、numpy2.3.5、pandas2.2.3检查已封存结果（不拟合、不重新选参）：

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_utility_d3 -p 'test_*.py' -v
python research/causal_state_utility_d3/verify_d3.py --transport inputs/d3_input_transport_34623937960.zip --out results
```

需要代码级全量复现时，使用**新输出目录**，不要覆盖随包冻结模型。先执行fit（仅Development），其产物写盘冻结后才evaluate：

```bash
OPENBLAS_NUM_THREADS=1 python research/causal_state_utility_d3/run_d3.py --phase fit --transport inputs/d3_input_transport_34623937960.zip --ledger inputs/d2_causal_state_replay_34620317766.zip --out reproduced
OPENBLAS_NUM_THREADS=1 python research/causal_state_utility_d3/run_d3.py --phase evaluate --transport inputs/d3_input_transport_34623937960.zip --ledger inputs/d2_causal_state_replay_34620317766.zip --out reproduced
```

这是复现，不是新独立确认。其他依赖版本可能产生浮点/文件序列化差异，必须报告，不改门槛。完整原始SUMMARY的SHA256为8414d6920cf29166e3599dd90dd5f6c8e6cf9c23d2580e0db2500530793684d5，模型SHA256为f5a33a71969a18f2e7aa0aad45cd83903943d86962f2a92f5206e348667a2db0。

20个真实历史特征扰动检查范围见结果包results/MARKET_FEATURE_PREFIX_CHECKS.json；它不是新的3s引擎回放。完整仓库、线上接入、策略经济收益未验收。production_authority=false。
