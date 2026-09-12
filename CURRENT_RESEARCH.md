# 当前任务：one-step degree trajectory 增量路径已关闭

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置科学决定继续保留：

- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`。

并行 reception 工程状态仍是：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

历史 research backlog 仍是：

**`RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`**。

## 当前权威链

最新科学主链：

`research/degree_trajectory_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json` / `evidence/FROZEN_MODELS.json` / `evidence/SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py`。

前置权威继续保留：

- 12-bar shock memory：`research/historical_shock_burden_utility_v1/`；
- cross-index current degree：`research/cross_index_degree_transfer_utility_v1/`；
- current M3 refresh：`research/activity_degree_incremental_utility_v1/`；
- D4 / D3 / D2 / V19 / D5；
- backlog closeout：`docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`；
- reception：`research/prospective_reception_recorder_v1/` → D5R。

治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准。

## 最新科学结果：One-step degree-trajectory incremental utility V1

D4/D5 已经传输 `lag_intensity`、`lag_ratio`、`delta_intensity`、`delta_ratio`，但原 contract 明确没有给 delta 独立预测效用验收。本轮正式补上这个科学问题。

由于 current E15 I/V 已经在 baseline C 中，加入上一根 confirmed degree 与加入 `current - lag1` delta 在**原始信息层面一一等价**。因此冻结比较为：

- C：84-column own-index D4-style current-I/V baseline；
- T：C + lag1 confirmed degree 的固定20-column nonlinear/state-interaction block；
- O：C + 完全同复杂度的 lag2 confirmed degree control；
- T/O 都是104 columns，schema、scaling、ridge 完全一致。

只有 `T vs C` 与 `T vs O` 同时通过，才承认最近一步 trajectory 有独立实用价值。

决定性 Action run：`34680352701`。Development 2021–2023 先 fit/freeze，随后同一 run 的 exact frozen artifact 才解锁 2024–2025 reusable Validation。

冻结模型 SHA256：

`04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188`。

Validation artifact：`10294052627`，ZIP SHA256：

`60c9133dbf6632b2f7dcf9795c70038ed50f4d18718fc54aaf2378010ceaeba8`。

`VALIDATION_RESULTS.json` SHA256：

`16e7db8b780f64cfa0fcc5091d3ab1feed4c63658465697381b2ae9dda390763`。

完整决定性 evidence 已按原字节持久化进 `research/degree_trajectory_utility_v1/evidence/`。

### Cohort / coverage

- 15m：Development 59,614；Validation 39,770；trajectory coverage 100%；
- 30m：50,890 / 33,950 / 100%；
- 60m：33,442 / 22,310 / 100%。

### 正式比较

T 的 pooled relative squared-loss reduction：

| Horizon | Endpoint | T vs C | T vs O |
|---|---|---:|---:|
| 15m | log future RMS | +0.11415% | +0.11321% |
| 15m | future tail | +0.03753% | -0.00340% |
| 30m | log future RMS | **+0.14957%** | **+0.15160%** |
| 30m | future tail | +0.03919% | -0.03684% |
| 60m | log future RMS | +0.02416% | -0.04063% |
| 60m | future tail | +0.04523% | +0.01985% |

**12/12 formal comparisons 全部低于冻结 1% practical gate；六个 endpoint×horizon joint promotion 全部 false。**

Tail absolute Brier gains 全部远低于 `0.0005`。

30m log-RMS 是最值得解释、但仍不能晋升的一项：

- T vs C +0.14957%，5-day adjusted CI lower `+0.00002614`，2024/2025 与两个指数符号均非负，2023 forward 也为正；
- T vs O +0.15160%，但 5-day adjusted CI lower `-0.00004682`，跨0；
- 两个点估计都只有约 **0.15%**，约为冻结 1% practical gate 的七分之一。

因此不能说 trajectory/delta 完全没有信息；更准确的是：**最近一步 confirmed degree 对30m future RMS 含少量统计信息，但没有稳定打赢同复杂度 lag2，也没有足够实用幅度。**

15m RMS 约0.11%，区间跨0；60m T-vs-O RMS 已转负。tail 全部明显不支持独立预测 promotion。

### D4/D5 delta 的正式解释

本轮不删除 D4/D5 的 `lag_intensity`、`lag_ratio`、`delta_intensity`、`delta_ratio`。它们继续可以作为**描述/诊断/可观测消费字段**存在于原 contract 中。

但本轮明确冻结：

- `delta_independent_predictive_promotion=false`；
- 不把 delta 变成 D5 decision gate；
- 不修改 V19；
- 不创建新 risk state / threshold / production field。

## Fixed path 已关闭

lag1-vs-lag2 trajectory V1 到此关闭。禁止使用本次 reusable Validation 结果去做：

- lag3/lag4 搜索；
- smoothing / decay；
- alternate normalization；
- 单指数、state、slot、episode 筛选；
- 改 nonlinear transform / ridge / horizon / bootstrap family；
- 删除 O control。

未来若研究 degree dynamics，必须是**真正不同的因果机制假设**，重新事前冻结，而不是围绕本轮小正信号做参数救援。

## 前置科学结果保持不变

- 12-bar cumulative shock burden：有少量统计信号但没有实用、稳定的 shock-specific increment，不进D5/V19；
- cross-index current degree：other-current I/V 在 own-current 已知后不支持增量 promotion；
- current M3：相对 D4 baseline 有信息，但 current-refresh 相对 lagged-M3 未过 practical gate；
- D4 own current I/V：指定 endpoint 有限支持；
- D3 practical negative；
- V19 frozen；
- D5 bounded consumer contract 不变。

## 历史 backlog 与 reception

历史 research backlog 仍是 **remaining executable legacy backlog = 0**，旧 detector/RMR/router/v0.6.17 不重开。

reception 仍是 `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`。历史不存在可恢复的逐条真实本机 `received_at`，未来证据只能由未来物理 feed 产生并服从 V2 治理。

## 下一步边界

本轮 trajectory fixed specification 已关闭。下一科学题必须是与 V19 / D4 / M3 / cross-index / shock-memory / trajectory 都真正不同的因果风险机制，并能在结果前冻结；否则正确动作是维持并审计现有 authority，而不是继续调 lag/window/threshold。

仍然：不读受保护2026逐行数据，不查BlackBox，不算PnL，不恢复router，不开D6/V20，不提高production authority。

`degree_trajectory_incremental_supported=false`; `delta_independent_predictive_promotion=false`; `d5_contract_unchanged=true`; `historical_shock_burden_incremental_supported=false`; `cross_index_current_degree_incremental_supported=false`; `current_m3_consumer_promotion=false`; `historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `validation_reused=true`; `fresh_oos=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
