# STAR50 / CSI1000 当前权威索引

## 当前断点：PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING

[当前任务](../CURRENT_RESEARCH.md) → [recorder程序状态](../research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [冻结协议](../research/prospective_reception_recorder_v1/PROTOCOL.md) → [schema](../research/prospective_reception_recorder_v1/SCHEMA.json) → [执行回执](../research/prospective_reception_recorder_v1/EXECUTION_RECEIPT.json) → [本地接入交接](../research/prospective_reception_recorder_v1/LOCAL_INTEGRATION_HANDOFF.md)。

历史D5R判定仍有效：[D5R结果](../research/reception_clock_adjudication_d5r/RESULTS.md)。两个指数历史存储没有逐条真实本机received_at，历史实测feed/network/processing latency不可恢复。

参考recorder已经实现：feed callback入口先记录UTC wall-clock、monotonic_ns、本地sequence和raw payload identity，再解析event time/symbol/price。18项合成测试、编译和独立validator样例通过；尚未安装DataHub、未读取新行情、未产生真实reception rows。

## 保持原样的历史阶段证据

- [D5样例消费者](../research/state_degree_consumer_d5/RESULTS.md)：本仓consumer工程验收；
- [D4连续属性](../research/continuous_risk_utility_d4/RESULTS.md)：15/30/60m波动与30m尾部有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：增量效用未过原实际门槛；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟历史工程回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md) / [残差审计](../research/v19_residual_failure_audit/RESULTS.md)；
- [V18](../research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md) / [V17](../research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md) / [V16](../research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json)。

## 下一可执行条件

本地先用synthetic/允许replay把参考语义接进DataHub真实callback，并测插桩开销、重启和持久化。真实新行情如果开始采集，因为当前日期已过2026-08-21，必须留在受保护本地数据层，不能直接暴露逐行内容；后续研究使用需服从[V2](governance/DATA_USAGE_POLICY_V2.md)与[BlackBox ledger](governance/blackbox_query_ledger.json)。

`true_reception_timestamp_available=false`; `measured_feed_latency_supported=false`; `live_recorder_installed=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
