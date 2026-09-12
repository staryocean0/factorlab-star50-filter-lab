# 接续入口：12-bar historical shock-burden 已关闭

最新科学状态：**`HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置状态继续有效：

- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`；
- `RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`。

## 先读

1. `CURRENT_RESEARCH.md`
2. `research/historical_shock_burden_utility_v1/PROGRAM_STATE.json`
3. `research/historical_shock_burden_utility_v1/RESULTS.md`
4. `research/historical_shock_burden_utility_v1/DECISIVE_RECEIPT.json`
5. `research/historical_shock_burden_utility_v1/EXECUTION_RECEIPT.json`
6. `research/historical_shock_burden_utility_v1/evidence/VALIDATION_RESULTS.json`
7. cross-index / M3 / D4 / D3 / D2 / V19 与 V2治理。
8. 历史分支问题读 `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`；reception读 `research/prospective_reception_recorder_v1/` 和 D5R。

## 最新结论

问题是：own current E15 I/V、previous state 和 recent-shock age 已知后，最近12个有效已完成交易return bars中的确认 shock count / excess 是否还有实用未来风险增量。

C=own D4-style baseline；S=C+shock-memory；H=C+完全等复杂度 high-vol-memory control。只有 S 同时打赢 C 和 H 才允许晋升。

决定性 run `34679293167` 使用 Validation 前冻结的 exact model SHA：

`65f9403e3aae00873432403f833c1d8772429c5172fc7f3fd76581a19a4222d3`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），memory coverage均100%。

12项 formal comparison 的 relative gain 全部低于冻结1% practical gate。最强点估计也只是60m RMS `S vs H` **+0.34717%**。tail absolute Brier gains 全部 < `0.0005`。

15m RMS 确实有一点统计信号：S vs C +0.16994%，其5日调整区间下界略为正；但 S vs H 只有 +0.16951%，区间跨0，而且两者都离1%门槛很远。因此不能晋升为新的 shock-specific memory coordinate。

2023 forward 对15m tail、30m S-vs-C RMS/tail、60m所有endpoint均有负项，也不支持扩大解释。

因此：

- 12-bar shock-memory 不进入D5 consumer；
- 不修改V19；
- 不把V5“reshock resets clock”偷换成“累计shock burden值得新增字段”；
- 不做6/24 bar、decay、threshold、单index/state/time筛选救援。

完整决定性 evidence 已按原字节持久化在 `research/historical_shock_burden_utility_v1/evidence/`。

## 前置结论

cross-index current-degree 与 current-M3 两条 incremental utility 规格均已关闭且不晋升。D4 own current I/V endpoint-limited support、D3 negative、V19 frozen、D5 bounded consumer均不变。

## 接下来执行边界

本轮 fixed 12-bar memory 规格正式关闭。下一科学题必须是**真正不同的因果风险机制**，并在看结果前冻结问题/比较器/门槛；不能把“继续”解释成调整 memory window、decay、threshold 或 subgroup。

不查BlackBox，不读受保护2026逐行数据，不算PnL，不恢复router，不开D6/V20，不提高production authority。
