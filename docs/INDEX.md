# STAR50 / CSI1000 当前权威索引

## 当前断点：D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED

[当前任务](../CURRENT_RESEARCH.md) → [D5R程序状态](../research/reception_clock_adjudication_d5r/PROGRAM_STATE.json) → [D5R结果](../research/reception_clock_adjudication_d5r/RESULTS.md) → [判定回执](../research/reception_clock_adjudication_d5r/DECISIVE_RECEIPT.json) → [本地负结果包说明](ops/receipts/star50_true_reception_raw_20260912/README.md)。

本地检索确认两个指数没有逐条真实本机 reception timestamp；Release 包 quote rows=0。历史 measured-latency / actual received_at 验收因此无法完成。`available_at`、batch `ingested_at`、mtime、下载时间、market observation time 与 row_index 均不得替代 `received_at`。

## 保持原样的历史阶段证据

- [D5样例消费者](../research/state_degree_consumer_d5/RESULTS.md)：本仓 consumer/as-of/过期/缺失工程验收通过，但接收延迟样例是合成/理想时钟；
- [D4连续属性](../research/continuous_risk_utility_d4/RESULTS.md)：15/30/60m波动与30m尾部有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：增量效用未获原实际门槛晋升；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟历史工程回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md) / [残差审计](../research/v19_residual_failure_audit/RESULTS.md)；
- [V18](../research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md) / [V17](../research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md) / [V16](../research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json)。

## 下一可执行条件

只有未来前瞻 recorder 真正持久化 market/event timestamp 与 local receive wall-clock/monotonic clock/sequence 后，才重新打开真实 reception 验收。没有这类新数据时保持冻结维护，不开 D6/V20。

[V2](governance/DATA_USAGE_POLICY_V2.md)、[桶边界](governance/BUCKET_SCOPE_REPAIR_20260909.md)、[available_at澄清](governance/available_at_owner_clarification_20260906.json)、[BlackBox ledger](governance/blackbox_query_ledger.json)不变。

`true_reception_timestamp_available=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `production_authority=false`。
