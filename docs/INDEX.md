# STAR50 / CSI1000 — 当前权威索引

## 当前断点：D4_COMPLETED_CONTINUOUS_ATTRIBUTES_PARTIALLY_SUPPORTED

[方向](research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) → [D4进度](../research/continuous_risk_utility_d4/PROGRAM_STATE.json) → [结果](../research/continuous_risk_utility_d4/RESULTS.md) → [判定](../research/continuous_risk_utility_d4/DECISIVE_RECEIPT.json) → [执行回执](../research/continuous_risk_utility_d4/EXECUTION_RECEIPT.json) → [协议](../research/continuous_risk_utility_d4/PROTOCOL.md) → [评分前冻结](../research/continuous_risk_utility_d4/FIT_FREEZE_RECEIPT.json) → [独立核验](../research/continuous_risk_utility_d4/INDEPENDENT_VERIFICATION.json)。

连续属性I/V：15/30/60m波动、30m尾部在H/L双基准下支持；15/60m尾部未晋升。D3已知线索后的可复用Validation，不是fresh OOS。下游接续：[消费者契约](../research/continuous_risk_utility_d4/CONSUMER_CONTRACT.md) / [复核命令](../research/continuous_risk_utility_d4/REPRODUCE.md)。真实接入尚未执行，D5未启动。

## 历史阶段证据保持不变

- [D3未获实际增量晋升](../research/causal_state_utility_d3/RESULTS.md) / [原判定](../research/causal_state_utility_d3/DECISIVE_RECEIPT.json)。D4不改判D3。
- [D2双时钟回放](../research/causal_state_delivery_d2/RESULTS.md) / [原回执](../research/causal_state_delivery_d2/EXECUTION_RECEIPT.json)。
- [D1原契约](../research/causal_state_delivery_v1/CONTRACT.md)。
- [V19 Validation](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md) / [残差审计](../research/v19_residual_failure_audit/RESULTS.md)。
- [V18 switch-on](../research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md) / [V17 recovery](../research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md) / [V16 surface](../research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json)。

[当前任务](../CURRENT_RESEARCH.md)、[接续](../CONTINUE_HERE.md)、[V2](governance/DATA_USAGE_POLICY_V2.md)、[数据角色](governance/data_usage_declaration.json)、[桶边界](governance/BUCKET_SCOPE_REPAIR_20260909.md)、[时钟澄清](governance/available_at_owner_clarification_20260906.json)、[BlackBox ledger](governance/blackbox_query_ledger.json)。旧20260907交接与历史本地记录不是当前指令；历史入口在commit4844ca27006bc187ee4d4ecb6262b903f4d798f0。

`d4_executed=true`; `d5_started=false`; `v20_started=false`; `production_authority=false`。
