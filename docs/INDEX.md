# STAR50 / CSI1000 — 当前权威索引

## 当前断点：D2_CAUSAL_REPLAY_SUPPORTED_D3_NOT_EXECUTED

[下一阶段方向](research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) → [当前机器进度](../research/causal_state_delivery_d2/PROGRAM_STATE.json) → [D2结果与限制](../research/causal_state_delivery_d2/RESULTS.md) → [执行回执](../research/causal_state_delivery_d2/EXECUTION_RECEIPT.json) → [冻结协议](../research/causal_state_delivery_d2/PROTOCOL.md) → [独立账本复核](../research/causal_state_delivery_d2/LOCAL_VERIFICATION_SUMMARY.json)。

D2：113,928原可用E-15行零漂移；232,704双时钟事件；20市场前缀检查通过。原D1契约/20测试与D2新增38测试通过。完整网格97.9167%可用；日初缺参考和15:00 E-15观察新鲜度限制如实保留。下一步D3预注册非PnL分桶效用，不把标签一致性当效用证明。

[D1原始契约](../research/causal_state_delivery_v1/CONTRACT.md)与[原始执行回执](../research/causal_state_delivery_v1/EXECUTION_RECEIPT.json)不改，旧D1 PROGRAM_STATE不再是当前状态。

## 冻结科学基线

- [V19 reusable Validation](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md) → [receipt](../research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json) → [contract](../research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json)；Development在research/highvol_risk_episode_state_machine_v19/。
- [V19残差审计](../research/v19_residual_failure_audit/RESULTS.md) → [receipt](../research/v19_residual_failure_audit/DECISIVE_RECEIPT.json)。NO_V20_FROM_V19_RESIDUALS保留，不是不可改进性定理或Validation复用禁令。
- [V18 switch-on](../research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md) → [receipt](../research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json)。
- [V17 realtime recovery](../research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md) → [冻结transfer](../research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json)。
- [V16 surface](../research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json) → [Validation](../research/highvol_horizon_adaptive_v16_validation/VALIDATION_RESULTS.md)。

V17/V18/V19实时验证2024–2025；V16 final-5m到2026-08-21；没有2026 realtime、策略收益或实盘验收。

## 治理与接续

[当前任务](../CURRENT_RESEARCH.md)；[接续入口](../CONTINUE_HERE.md)；[研究桶边界](governance/BUCKET_SCOPE_REPAIR_20260909.md)；[V2数据政策](governance/DATA_USAGE_POLICY_V2.md)；[数据角色](governance/data_usage_declaration.json)；[available_at澄清](governance/available_at_owner_clarification_20260906.json)；[BlackBox ledger](governance/blackbox_query_ledger.json)。

Validation可复用，非fresh OOS。不恢复payoff/router，不修改其他桶、生产registry或数据权限。

## 历史资料，非当前任务

[2026-09-07交接](handoff/cloud_risk_gate_20260907/HANDOFF.md)；[云端—本地记录](ops/cloud_local_communication.md)；[因果波动V1](research/causal_volatility_tool_v1/result.md)；[尾部分布](research/tail_distribution_v1/result.md)；[分辨率测量](research/resolution_transfer_v1/result.md)。历史“当前/下一步”不覆盖新的权威链。

`d2_supported=true`; `d3_executed=false`; `v20_started=false`; `production_authority=false`。
