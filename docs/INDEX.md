# STAR50 / CSI1000 当前权威索引

## 最新科学状态：HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [程序状态](../research/historical_shock_burden_utility_v1/PROGRAM_STATE.json) → [正式结果](../research/historical_shock_burden_utility_v1/RESULTS.md) → [决定性回执](../research/historical_shock_burden_utility_v1/DECISIVE_RECEIPT.json) → [原始Validation结果](../research/historical_shock_burden_utility_v1/evidence/VALIDATION_RESULTS.json)。

## Historical shock-burden incremental utility V1

冻结问题：target own current E15 I/V、previous state 和 recent-shock age 已知后，最近12个有效已完成交易return bars中的确认3σ shock count/excess是否仍有实用未来风险增量。

- C = 84-column own D4-style causal baseline；
- S = C + 20-column shock-memory block；
- H = C + 完全等复杂度 high-vol-memory control；
- S/H均104 columns且schema一致。

决定性 run `34679293167` 使用 Validation 前冻结的 exact model SHA256：

`65f9403e3aae00873432403f833c1d8772429c5172fc7f3fd76581a19a4222d3`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），memory coverage均100%。12项 `S vs C/H × endpoint × horizon` 全部低于冻结1% practical relative gate；六个joint promotion全部false。

future-RMS relative gains：

- 15m +0.16994% / +0.16951%；
- 30m +0.18307% / +0.19834%；
- 60m +0.24096% / +0.34717%。

15m S-vs-C的5日调整区间下界略为正，但S-vs-H区间跨0，而且所有relative gains远低于1%。tail relative gains均<0.05%，absolute Brier gains均<`0.0005`。

因此：固定12-bar累计shock memory可能含少量短期统计信息，但没有证明在current degree + recent-shock-age之外具有足够稳定、实用的shock-specific增量。它不进入D5/V19。

本轮不允许事后改成6/24 bar、decay、threshold、单index/state/time subset或删除H control。

完整Action evidence按原字节保存在 `research/historical_shock_burden_utility_v1/evidence/`。

## 前置科学状态

### Cross-index current degree

`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`。other-current I/V 在 own-current I/V 已知后所有frozen comparison均未过1% practical gate，不做单向/lag/state rescue。

### Current M3

`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`。M3相对own current-I/V包含future-RMS信息，但current-vs-lagged-M3 refresh增量未过冻结1% practical gate。

## 核心历史证据

- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：own current I/V endpoint-limited support；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟因果回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D5](../research/state_degree_consumer_d5/RESULTS.md)：bounded consumer；
- [risk-coordinate frozen Validation](research/risk_coordinate_validation_v1/RESULT.md)：禁止事后降门槛救M3 amplitude axis。

V5 的 recurrent-shock clock-reset finding 不被本轮否定；本轮只否定累计12-bar burden作为额外可晋升坐标。

## 历史 research backlog：已关闭

112个research分支的高召回审计对象已经逐项裁决，**remaining executable legacy backlog = 0**。

[机器closeout ledger](research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json) → [人类说明](research/RESEARCH_BACKLOG_CLOSEOUT_20260912.md) → [v0.6.17 closeout](research/session_aware_information_set_bounds_v0617/CLOSEOUT_RECEIPT_20260912.json)。

## Reception并行状态

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING` 不变。历史没有逐条真实本机`received_at`；未来true-reception observations只能来自未来真实feed并服从V2治理。

## 下一执行边界

12-bar historical shock-memory fixed specification 已关闭。下一科学题必须是不同因果机制，且在结果前冻结问题/比较器/门槛；不得把memory window/decay/threshold/subgroup tuning当下一步。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复交易router、不为V19开V20、不因reception缺口开D6、不提高production authority。
