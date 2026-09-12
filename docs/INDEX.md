# STAR50 / CSI1000 当前权威索引

## 最新科学状态：CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [M3程序状态](../research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json) → [正式结果](../research/activity_degree_incremental_utility_v1/RESULTS.md) → [执行回执](../research/activity_degree_incremental_utility_v1/EXECUTION_RECEIPT.json) → [原始Validation结果](../research/activity_degree_incremental_utility_v1/evidence/VALIDATION_RESULTS.json)。

## 历史 research backlog：已关闭

112个 `research/*` 分支的高召回审计曾标出12个“可能未闭环”分支。逐项回读原Action、后继Validation与治理后，12/12均已裁决，**remaining executable legacy backlog = 0**。

[机器closeout ledger](research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json) → [人类说明](research/RESEARCH_BACKLOG_CLOSEOUT_20260912.md) → [v0.6.17严格身份closeout](research/session_aware_information_set_bounds_v0617/CLOSEOUT_RECEIPT_20260912.json)。

`execution-audit` 现执行 `scripts/validate_research_backlog_closeout.py`，确保这12项不会因后续文档漂移重新被误当成当前待办。

关键分类：

- first-shock minute、V7、两个RMR：已执行但未形成当前可晋升机制；
- V8/V9/V10：祖先Development/Validation链已被V17/V19吸收；
- V11 2026-09-11：重复frozen设计，正式V11已失败，V12又否定简单expiry解释；
- risk-gate-takeover：交接协调分支，不是漏跑实验；
- old highvol-router：包含route/hold/cost/PnL/Sharpe/MDD，当前scope明确退役；
- v0.6.17：实现通过，但严格pre-v0.6.17 Git审计找不到协议要求的两个事前identity，故 `V0617_PRIOR_IDENTITY_IRRECOVERABLE_REPLAY_PERMANENTLY_BLOCKED_UNDER_FROZEN_PROTOCOL`，不能事后补hash。

历史分支和原verdict全部保留，closeout不删除、不改写历史证据，也不创造新candidate。

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

没有旧分支需要继续补跑。只有发现**不同因果风险机制**、并能在结果前冻结问题/比较器/门槛时才开新科学题。不得把新题作为current-M3、V19、旧detector、reversal或router的参数救援。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复交易router、不为V19开V20、不因reception缺口开D6、不提高production authority。
