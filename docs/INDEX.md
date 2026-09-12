# STAR50 / CSI1000 当前权威索引

## 最新科学状态：CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [程序状态](../research/cross_index_degree_transfer_utility_v1/PROGRAM_STATE.json) → [正式结果](../research/cross_index_degree_transfer_utility_v1/RESULTS.md) → [决定性回执](../research/cross_index_degree_transfer_utility_v1/DECISIVE_RECEIPT.json) → [原始Validation结果](../research/cross_index_degree_transfer_utility_v1/evidence/VALIDATION_RESULTS.json)。

## Cross-index current-degree transfer utility V1

冻结问题：target own D4-style history + own current I/V 已知后，other index 同一 E15 的 current I/V 是否仍有实用未来风险增量。

- C = target own baseline；
- X = C + other-current I/V frozen 15-column block；
- L = C + 等复杂度 other-lag I/V block。

决定性 run `34677297901` 使用第一次 Development fit 在 Validation 前冻结的 exact model SHA256：

`7eae7142323b38c5ae54618745e9ad9891c00afb09d02e8eb8def4490675f6b6`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），paired coverage均100%。12项 `X vs C/L × endpoint × horizon` 全部未过1% practical relative gate，全部5日块Bonferroni CI跨0；六个joint promotion全部false。

最大 pooled 点估计只有60m tail X-vs-C +0.14197%，absolute gain `0.00011937`，也没过tail `0.0005` gate。多个STAR50 slice为负，不允许事后只挑CSI1000方向救援。

完整Action证据按原字节在 `research/cross_index_degree_transfer_utility_v1/evidence/`。

## 前置科学状态：CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED

[M3程序状态](../research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json) → [M3结果](../research/activity_degree_incremental_utility_v1/RESULTS.md)。

current M3 相对 own current-I/V 对 future RMS 有额外信息，但相对等复杂度 lagged-M3 的 refresh 增量没有达到冻结1% practical gate。因此 M3不进入D5/V19，也不允许调bands/30bp surface/ridge/horizon/sample gate救结果。

## 历史 research backlog：已关闭

112个 `research/*` 分支的高召回审计曾标出12个“可能未闭环”分支。逐项回读原Action、后继Validation与治理后，12/12均已裁决，**remaining executable legacy backlog = 0**。

[机器closeout ledger](research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json) → [人类说明](research/RESEARCH_BACKLOG_CLOSEOUT_20260912.md) → [v0.6.17严格身份closeout](research/session_aware_information_set_bounds_v0617/CLOSEOUT_RECEIPT_20260912.json)。

旧detector/first-shock/RMR要么失败要么被V17/V19取代；V11 9/11是重复设计；risk-gate-takeover只是协调容器；old router/PnL线退役；v0.6.17因事前identity不可恢复永久fail-closed。

## 前置科学证据

[risk-coordinate frozen Validation](research/risk_coordinate_validation_v1/RESULT.md)：`RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE`。

- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：own current I/V 对指定endpoint有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟因果回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机。

## Reception并行状态

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING` 不变。

[reception程序状态](../research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [云端验收结果](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_RESULTS.md) → [D5R](../research/reception_clock_adjudication_d5r/RESULTS.md)。

历史没有逐条真实本机`received_at`；未来true-reception observations只能来自未来真实feed并服从V2治理。

## 下一执行边界

cross-index current-degree fixed specification 已关闭。不能按index方向、lag、state、threshold或horizon事后救援。只有发现**不同因果风险机制**并能在结果前冻结问题/比较器/门槛时才开新科学题。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复交易router、不为V19开V20、不因reception缺口开D6、不提高production authority。
