# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓用于研究行情环境与策略适用条件，不开发交易动作、方向、仓位或收益 router。

## 当前：D5样例消费者通过，历史真实接收时钟不可用

当前断点：**D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

D5 已完成本仓样例消费者验收；但随后本地只读检索确认，两个指数没有逐条真实本机 `received_at` 历史记录。因此无法把历史 `owner_realtime_assumption` 升级成实测 feed/network/processing latency，也无法从现有历史数据完成真实接收时钟验收。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [D5R进度](research/reception_clock_adjudication_d5r/PROGRAM_STATE.json) → [D5R结果](research/reception_clock_adjudication_d5r/RESULTS.md) → [本地负结果包](docs/ops/receipts/star50_true_reception_raw_20260912/README.md)。

## 保留的结论

- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结风险状态识别基线；
- [D2](research/causal_state_delivery_d2/RESULTS.md)：因果双时钟历史工程回放；
- [D3](research/causal_state_utility_d3/RESULTS.md)：三状态增量用途未获实际门槛晋升；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：连续 I/V 对指定风险目标有限支持；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：本仓样例消费者字节/as-of/过期/缺失语义通过。

这些都不等于真实本机 reception log 已存在，也不证明策略盈利或生产就绪。

## 接收时钟边界

本地 DataHub recording 相关表为空，`lake/recording` / `ticks.parquet` 未物化。`available_at`、batch `ingested_at`、文件 mtime、下载时间、市场 observation time、row_index 都不能冒充真实 `received_at`。

若未来要验证真实延迟，只能前瞻持久化市场事件时钟与本机接收 wall-clock/monotonic clock/sequence 等字段；在此之前继续标记 `unmeasured_reception`。

[V2数据治理](docs/governance/DATA_USAGE_POLICY_V2.md)与[研究桶边界](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md)不变。无新2026/BlackBox/PnL/生产权限，不启动 D6/V20。

`production_authority=false`。
