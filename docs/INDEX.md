# STAR50 / CSI1000 — 当前权威索引

## 当前阶段：因果 K 线风险属性交付

[下一阶段权威叙事](research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) → [机器进度](../research/causal_state_delivery_v1/PROGRAM_STATE.json) → [接口契约](../research/causal_state_delivery_v1/CONTRACT.md) → [执行回执](../research/causal_state_delivery_v1/EXECUTION_RECEIPT.json)。

用途：以当时可得的 K 线风险属性/转移帮助下游跟踪行情、状态识别和策略适用条件分桶；本仓不开发策略动作。

当前状态 `CAUSAL_KLINE_STATE_DELIVERY_V1_CONTRACT_TESTED_REPLAY_PENDING`：E-15 状态适配切片与20项合成测试已完成，真实事件回放、概率接入及非 PnL 风险分桶效用待验收。这是交付版本，不是 V20。

## 冻结科学基线与原始证据

- [V19 reusable Validation](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md) → [receipt](../research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json) → [contract](../research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json)。Development 证据在 `research/highvol_risk_episode_state_machine_v19/`。
- [V19 residual audit](../research/v19_residual_failure_audit/RESULTS.md) → [receipt](../research/v19_residual_failure_audit/DECISIVE_RECEIPT.json)。结论 `NO_V20_FROM_V19_RESIDUALS` 保留；不是不可改进性定理或 Validation 永不可复用的政策。
- [V18 switch-on](../research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md) → [receipt](../research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json)。
- [V17 realtime recovery](../research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md) → [冻结 transfer](../research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json)。
- [V16 final-5m surface](../research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json) → [Validation](../research/highvol_horizon_adaptive_v16_validation/VALIDATION_RESULTS.md)。

V17/V18/V19 实时验证覆盖仅 2024–2025；V16 final-5m 到 2026-08-21。不得据此声称 2026 realtime、所有市场风险识别、经济效用或实盘已通过。

## 治理与接续

[当前任务](../CURRENT_RESEARCH.md)；[接续入口](../CONTINUE_HERE.md)；[研究桶边界](governance/BUCKET_SCOPE_REPAIR_20260909.md)；[V2数据政策](governance/DATA_USAGE_POLICY_V2.md)；[数据角色](governance/data_usage_declaration.json)；[可得性字段澄清](governance/available_at_owner_clarification_20260906.json)；[BlackBox ledger](governance/blackbox_query_ledger.json)。

Validation 可复用但非 fresh OOS。旧 payoff/router 不恢复；不修改其他研究桶、生产 registry 或数据权限。

## 历史资料入口（非当前任务）

[2026-09-07云端交接](handoff/cloud_risk_gate_20260907/HANDOFF.md)；[云端—本地历史记录](ops/cloud_local_communication.md)；[因果波动V1](research/causal_volatility_tool_v1/result.md)；[尾部分布](research/tail_distribution_v1/result.md)；[分辨率历史测量](research/resolution_transfer_v1/result.md)。历史资料中的“当前/下一步”不覆盖以上新权威链，原报告保持不变。

`v20_started=false`; `production_authority=false`。
