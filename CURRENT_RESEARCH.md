# 当前任务：12-bar historical shock-burden 增量路径已关闭

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置科学决定继续保留：

- **`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**；
- **`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

并行 reception 工程状态：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

历史研究队列：

**`RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`**。

这些状态互不覆盖。

## 当前权威链

最新科学主链：

`research/historical_shock_burden_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json` / `evidence/FROZEN_MODELS.json` / `evidence/SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py`。

前置科学链继续保留：

- cross-index current degree：`research/cross_index_degree_transfer_utility_v1/`；
- current M3 refresh：`research/activity_degree_incremental_utility_v1/`；
- D4 / D3 / D2 / V19；
- 历史 backlog closeout：`docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`；
- reception 并行链：`research/prospective_reception_recorder_v1/` → D5R。

治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准。

## 最新科学结果：Historical shock-burden incremental utility V1

问题：在 target 自己的 confirmed history、previous state / recent-shock age、以及 current E15 D4-style I/V 都已经知道后，过去最近 12 个**有效已完成交易 return bars** 中累计出现多少次 3σ shock、超出 3σ 多少，是否仍有独立且实用的未来风险信息。

固定三模型：

- C：84-column own-index D4-style causal baseline；
- S：C + 12-bar confirmed shock count / excess 的 20-column fixed nonlinear/state-interaction block；
- H：C + 完全同复杂度的 confirmed high-vol count / excess control block。

S/H 都是 104 columns，schema、scaling、ridge penalty 完全一致。只有 `S vs C` 和 `S vs H` **同时过门槛**，才能说 shock-specific memory 值得晋升。

决定性 Action run `34679293167`：Development 先 fit/freeze，随后才由同一 run 的 exact frozen artifact 解锁 2024–2025 reusable Validation。冻结模型 SHA256：

`65f9403e3aae00873432403f833c1d8772429c5172fc7f3fd76581a19a4222d3`。

Validation artifact `10294046103`，ZIP SHA256：

`943d44b741888307c978b4504edeb704ecdeedb75ecdf8f521eec07a4809f215`。

`VALIDATION_RESULTS.json` SHA256：

`8fa3f332a033e8f57ebf3240e3891295444dd9b48a8e2f699e2244928eb2f8bd`。

完整 36-file Action evidence 已按原字节持久化到 `research/historical_shock_burden_utility_v1/evidence/`。

### Cohort 与 coverage

- 15m：Development 59,614；Validation 39,770；memory coverage 100%；
- 30m：50,890 / 33,950 / 100%；
- 60m：33,442 / 22,310 / 100%。

### 正式比较

S 的 pooled relative squared-loss reduction：

| Horizon | Endpoint | S vs C | S vs H |
|---|---|---:|---:|
| 15m | log future RMS | +0.16994% | +0.16951% |
| 15m | future tail | +0.03773% | +0.02048% |
| 30m | log future RMS | +0.18307% | +0.19834% |
| 30m | future tail | +0.03925% | +0.03670% |
| 60m | log future RMS | +0.24096% | +0.34717% |
| 60m | future tail | +0.03330% | +0.04419% |

**12/12 formal comparisons 全部低于冻结 1% practical gate；六个 endpoint×horizon joint promotion 全部 false。**

Tail absolute Brier gains 约 `0.000006`–`0.000037`，全部远低于冻结 `0.0005` gate。

15m log-RMS 是最值得解释但仍不能晋升的结果：

- S vs C +0.16994%，5-day adjusted CI lower `+0.00001510`，两个指数和两个年份符号均非负，2023 forward 也为正；
- 但 S vs H 仍只有 +0.16951%，5-day adjusted CI lower `-0.00003330`，并且两者都远低于 1%。

因此不能说“完全没有统计信息”；更准确的是：**有一点短期统计信号，但没有达到独立且实用的 shock-specific memory 增量门槛。**

30/60m 的主区间跨0，且多个 `S vs C` 2023 forward 为负。tail 全部明显失败。Validation 的 shock memory 本身也很稀疏：15m cohort 中 33,316 行过去12 bar无 shock，5,464 行仅1次，990 行>=2次；这个描述绝不能被事后转成 multi-shock 子样本筛选。

### 科学解释

这不推翻 V5 的“recurrent shock resets recovery clock”。recent-shock age 已经进入现有 recovery/state ancestry。本轮问的是：**在 timing + current degree 已经知道后，累计 shock burden 是否还应该成为新的风险坐标。** 冻结答案是不支持。

12-bar specification 到此关闭。禁止用本次 reusable Validation 结果去调：

- 12 → 6/24 或其他窗口；
- decay；
- 3σ / 1.5 threshold；
- 单指数、状态、时段、episode 筛选；
- ridge / horizon / bootstrap family；
- 删除 H control。

S 不进入 D5 consumer，也不修改 V19 state machine。

## 前置科学结果保持不变

### Cross-index current degree

`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`。other-current I/V 在 own current I/V 已知后，12项 frozen comparison 全部低于1%，不进入D5/V19，不做单向/lag/state救援。

### Current M3

`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`。M3 相对 own current-I/V 对 future RMS 有额外信息，但相对等复杂度 lagged-M3 的 current-refresh 实用增量未达到冻结1%门槛，不进入D5/V19。

## 历史 backlog 与 reception

历史 research backlog 仍是 **remaining executable legacy backlog = 0**。旧 detector/RMR/router/v0.6.17 等 closeout 不重开。

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING` 不变。历史没有逐条真实本机 `received_at`；未来真实 reception evidence 只能由未来物理 feed 产生并服从 V2 治理。

## 保持不变的核心结论

- `RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE`；
- V19 冻结，不为 accuracy 开 V20；
- D3 practical negative；
- D4 own current I/V endpoint-limited support；
- D5 bounded consumer contract；
- D5R 历史 true-reception clock 不可恢复。

## 下一步边界

本轮 12-bar shock-memory fixed specification 已关闭。**不允许**把下一步做成 window/decay/threshold/subgroup rescue。

只有出现与 V19 / D4 / M3 / cross-index / 本轮 memory 证据真正不同、并能在结果前冻结的独立因果风险机制时才开新科学实验；否则维持并审计当前 authority。

仍然：不读受保护2026逐行数据，不查BlackBox，不算PnL，不恢复router，不开D6/V20，不提高production authority。

`historical_shock_burden_incremental_supported=false`; `historical_shock_burden_consumer_promotion=false`; `cross_index_current_degree_incremental_supported=false`; `current_m3_consumer_promotion=false`; `historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `validation_reused=true`; `fresh_oos=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
