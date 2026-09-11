# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 目标是让下游在当时正确读取行情属性变化，用于环境分桶和策略适用性研究；本仓不开发具体交易动作、方向、仓位或收益router。

## 当前：D5本仓样例消费者已验收

D5_BOUNDED_RESEARCH_CONSUMER_ACCEPTED_EXTERNAL_INTEGRATION_PENDING。
完整接入232704条D2双时钟事件、116352条D4 E15增强；源字段与数值零差异，930816次固定时点查询独立复核通过。40项测试、20个消费者历史前缀和零/2秒延迟样例通过。没有新模型或新行情查询。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [D5进度](research/state_degree_consumer_d5/PROGRAM_STATE.json) → [结果](research/state_degree_consumer_d5/RESULTS.md) / [执行回执](research/state_degree_consumer_d5/EXECUTION_RECEIPT.json) / [可运行示例](research/state_degree_consumer_d5/REPRODUCE.md) / [外部研究接入交接](research/state_degree_consumer_d5/LOCAL_HANDOFF.md)。

E15与CLOSE分开，晚到不回填，过期不沿用，缺失不补NORMAL。E15增强不能冒充CLOSE增强；训练分位键不交付为门控。日初缺参考、日末观察较旧和非实测延迟限制保留。

## 结论边界

[V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)是冻结识别基线；[D2](research/causal_state_delivery_d2/RESULTS.md)是工程回放；[D3](research/causal_state_utility_d3/RESULTS.md)未获实际增量晋升；[D4](research/continuous_risk_utility_d4/RESULTS.md)只支持指定风险目标的连续信息集。D5接入通过不提高预测证据等级，也不证明盈利或实盘就绪。

下一步是真实外部研究消费者验收，不为版本号开D6/V20。本会话未连接FactorLab/DataHub或生产系统。
[V2数据治理](docs/governance/DATA_USAGE_POLICY_V2.md)、[研究桶边界](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md)不变；Validation可复用但非fresh OOS。D5仅复用2021–2025封存记录，无2026/BlackBox/PnL；NORMAL非安全保证，UNSAFE非看空。

```bash
python -m unittest discover -s research/state_degree_consumer_d5 -p 'test_*.py' -v
python scripts/validate_data_usage_policy.py
```

production_authority=false。
