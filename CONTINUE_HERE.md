# 接续入口：one-step degree trajectory 已关闭

最新科学状态：**`ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置状态继续有效：

- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`；
- `RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`。

## 先读

1. `CURRENT_RESEARCH.md`
2. `research/degree_trajectory_utility_v1/PROGRAM_STATE.json`
3. `research/degree_trajectory_utility_v1/RESULTS.md`
4. `research/degree_trajectory_utility_v1/DECISIVE_RECEIPT.json`
5. `research/degree_trajectory_utility_v1/EXECUTION_RECEIPT.json`
6. `research/degree_trajectory_utility_v1/evidence/VALIDATION_RESULTS.json`
7. shock-memory / cross-index / M3 / D4 / D3 / D2 / V19 / D5 与 V2治理。

## 最新结论

D4/D5 已经输出 lag/delta 字段，但此前没有独立预测效用验收。本轮以 C/T/O 固定比较正式验收：

- C = 84-column own D4-style current-I/V baseline；
- T = C + lag1 confirmed degree；
- O = C + 完全等复杂度 lag2 degree control；
- T/O = 104 columns，同schema、scaling、ridge。

current I/V 已经在 C 中，因此 lag1 raw degree 与 `current-lag1` delta 的新增原始信息一一等价。

决定性 run `34680352701`；Validation 前冻结模型 SHA256：

`04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），trajectory coverage均100%。

12项 formal comparison 全部低于冻结1% practical gate。最强是30m future-RMS：

- T vs C +0.14957%，5-day adjusted CI lower略为正；
- T vs O +0.15160%，但adjusted CI跨0；
- 两者都只有约0.15%，远低于1%。

15m RMS约0.11%；60m T-vs-O RMS转负。tail全部未获支持，15/30m T-vs-O tail为负，absolute Brier gains全部远低于`0.0005`。

因此不能说delta完全没信息，但**没有证据支持其独立预测 promotion**。D4/D5 的 `lag_intensity` / `lag_ratio` / `delta_intensity` / `delta_ratio` 继续保留为描述/诊断/消费字段；不把它们变成D5 decision gate，不修改V19。

完整决定性 evidence 已按原字节持久化在 `research/degree_trajectory_utility_v1/evidence/`。

## Closed path

禁止用这次 reusable Validation 去做 lag3/lag4、smoothing/decay、alternate normalization、selected symbol/state/slot、变换/正则/horizon tuning，或删除 O control。

下一科学题必须是**真正不同的因果风险机制**；不能把“继续”解释成围绕 trajectory 小正信号调参数。

不查BlackBox，不读受保护2026逐行数据，不算PnL，不恢复router，不开D6/V20，不提高production authority。
