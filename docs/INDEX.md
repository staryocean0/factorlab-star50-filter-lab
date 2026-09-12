# STAR50 / CSI1000 当前权威索引

## 最新科学状态：ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [程序状态](../research/degree_trajectory_utility_v1/PROGRAM_STATE.json) → [正式结果](../research/degree_trajectory_utility_v1/RESULTS.md) → [决定性回执](../research/degree_trajectory_utility_v1/DECISIVE_RECEIPT.json) → [原始Validation结果](../research/degree_trajectory_utility_v1/evidence/VALIDATION_RESULTS.json)。

## One-step degree-trajectory incremental utility V1

冻结问题：own current E15 I/V、previous state、recent-shock age 与 confirmed history 已知后，立即上一根 confirmed degree 是否有独立实用未来风险增量。

- C = 84-column own D4-style current-I/V baseline；
- T = C + lag1 degree 的固定20-column block；
- O = C + 完全同复杂度 lag2 degree control；
- T/O 均104 columns且schema/scaling/ridge一致；
- current 已在 C 中，因此 lag1 raw degree 与 current-minus-lag1 delta 的新增原始信息一一等价。

决定性 run `34680352701` 使用 Validation 前冻结的 exact model SHA256：

`04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），trajectory coverage均100%。12项正式comparison全部低于冻结1% practical gate；六个joint promotion全部false。

future-RMS relative gains（T vs C / T vs O）：

- 15m +0.11415% / +0.11321%；
- 30m **+0.14957% / +0.15160%**；
- 60m +0.02416% / -0.04063%。

30m T-vs-C的5日调整区间下界略为正，但T-vs-O区间跨0，且量级只有约0.15%。tail全不支持，15/30m T-vs-O tail为负，absolute Brier gains均远低于`0.0005`。

因此不能说trajectory/delta完全没信息；正式结论是：**没有足够稳定、实用的独立增量来获得predictive promotion。**

D4/D5 的 `lag_intensity`、`lag_ratio`、`delta_intensity`、`delta_ratio` 继续保留为描述/诊断/消费字段，不成为D5 decision gate，不修改V19。

完整Action evidence按原字节保存在 `research/degree_trajectory_utility_v1/evidence/`。

Fixed path 已关闭：不做 lag3/lag4、smoothing/decay、alternate normalizer、selected index/state/time、变换/正则/horizon tuning，也不删除O control。

## 前置科学状态

- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`：固定12-bar累计shock burden不晋升；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`：other-current degree不晋升；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`：current M3 refresh不晋升；
- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：own current I/V endpoint-limited support；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟因果回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D5](../research/state_degree_consumer_d5/RESULTS.md)：bounded consumer。

## 历史 research backlog / reception

历史 research backlog 已关闭，remaining executable legacy backlog = 0。机器 ledger：`research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`。

Reception 并行状态仍为 `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`。历史没有逐条真实本机`received_at`；未来true-reception observations只能来自未来真实feed并服从V2治理。

## 下一执行边界

trajectory fixed specification 已关闭。下一科学题必须是与 V19 / D4 / M3 / cross-index / shock-memory / trajectory 都不同的因果机制，并在结果前冻结；不得把lag/window/smoothing/subgroup tuning当下一步。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复交易router、不为V19开V20、不因reception缺口开D6、不提高production authority。
