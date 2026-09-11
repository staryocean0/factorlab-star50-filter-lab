# 接续入口：D4完成，状态+连续程度的研究消费者接入是下一步

当前状态D4_COMPLETED_CONTINUOUS_ATTRIBUTES_PARTIALLY_SUPPORTED。D4不是待执行；D3未通过的结论保持不变，不重新设计V19。

先读AGENTS.md、CURRENT_RESEARCH.md和docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md。随后读research/continuous_risk_utility_d4/下的PROGRAM_STATE.json、RESULTS.md、DECISIVE_RECEIPT.json、EXECUTION_RECEIPT.json、PROTOCOL.md、FIT_FREEZE_RECEIPT.json、CONSUMER_CONTRACT.md与REPRODUCE.md。旧D3/D2/D1及V16—V19证据仍保留。

D4：当前连续I/V对15/30/60m log未来RMS以及30m尾部在H/L双基准上支持；15/60m尾部不晋升。状态上下文与程度字段并列，不能把delta或3×3分位键叫已验收交易门控。D3线索已知，Validation2024–2025复用，不是新盲验。

## 可执行无新行情复核

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/continuous_risk_utility_d4 -p 'test_*.py' -v
python research/continuous_risk_utility_d4/verify_d4.py --transport /path/to/d3_input_transport_34623937960.zip --out /path/to/results_d4
```

23项D4合成测试、20项市场历史前缀检查及113928属性/96030未来记录复核已完成。完整原始日志、冻结模型、预测/块表和输入包见本轮证据包。不要为阅读结果重跑fit或新统计Validation；完整复现严格按REPRODUCE.md使用新输出目录。

## 下一项实际任务

按CONSUMER_CONTRACT.md，在本仓建立只输出风险属性的样例消费者：D2 E15/CLOSE双时钟与D4裸值按发布时间as-of join，验证不回填、过期失效、缺失明确、时区/版本正确、无未来标签或交易动作。无需新数据、无需调阈值、不改V19、不恢复router。该接入未执行，d5_started=false；数学步骤不需要逐项审批。

Development分位编码不能被声称在2021年已部署；日初不可用、日末旧观察、理想实时假设和CSV Asia/Shanghai时区随交付传递。若真实外部接入需要本地，由本地实际回执确认，不冒称已运行。

继续遵守V2、研究桶与执行位置协议；本轮及接续无2026 3s/保护期/BlackBox/PnL/生产权限。旧当前入口见commit4844ca27006bc187ee4d4ecb6262b903f4d798f0，原封存证据不改。production_authority=false。
