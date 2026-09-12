# STAR50 / CSI1000 当前权威索引

## 最新科学状态：CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [M3程序状态](../research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json) → [正式结果](../research/activity_degree_incremental_utility_v1/RESULTS.md) → [执行回执](../research/activity_degree_incremental_utility_v1/EXECUTION_RECEIPT.json) → [原始Validation结果](../research/activity_degree_incremental_utility_v1/evidence/VALIDATION_RESULTS.json)。

## Activity-degree incremental utility V1

决定性Action `34670357953`完成Development fit/freeze与2024–2025 reusable Validation。冻结模型 SHA256 `89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`。

核心解释：

- current M3 相对 D4-style C 对future log-RMS有额外信息；15m `A vs C` +2.1750%，单项全部gate通过；
- 但相对等复杂度lagged-M3 N，15/30/60m只有 +0.4330% / +0.5793% / +0.1832%，全部低于冻结1% practical gate；
- 15/30m 2023 forward `A vs N`为负；30/60m Development n低于20,000；60m Validation coverage 92.4378%低于95%；
- tail端点全部未晋升；
- 因此六个 endpoint×horizon joint promotion 全部 false。

完整Action证据已原字节保存于 `research/activity_degree_incremental_utility_v1/evidence/`。数值复现audit `34670797290` 证明重复fit输入/schema/n完全一致，最大系数差 `8.16e-15`；决定性Validation使用同一run内精确冻结模型。

禁止把“M3有信息”解释成“current M3 refresh值得进入consumer/state machine”，也禁止调M3 band、30bp surface、ridge、horizon、block、sample gate或删除lagged control救结果。

## 前置科学证据

[risk-coordinate frozen Validation](research/risk_coordinate_validation_v1/RESULT.md) → [执行回执](research/risk_coordinate_validation_v1/EXECUTION_RECEIPT.json)：`RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE`。state-persistence轴复制，但完整M3 amplitude axis因三个Unsafe极端格样本门槛失败，不允许事后调门槛。

- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：current I/V 对指定endpoint有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟因果回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机。

## Reception并行状态

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING` 不变。

[reception程序状态](../research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [云端验收结果](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_RESULTS.md) → [云端回执](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json) → [D5R](../research/reception_clock_adjudication_d5r/RESULTS.md)。

历史没有逐条真实本机`received_at`；云端 recorder/adapter/handoff 验收完成。未来true-reception observations必须来自未来真实feed且服从V2治理。

## 下一执行边界

优先收口历史research backlog；只在发现**不同因果机制**时开新科学题。不得把新题作为current-M3 refresh失败的参数救援。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复交易router、不为V19开V20、不因reception缺口开D6、不提高production authority。
