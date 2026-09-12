# 接续入口：cross-index current-degree 已关闭

最新科学状态：**`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

上一科学状态：**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**，保持有效。

并行 reception 工程状态：**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

历史研究队列：**`RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`**。

## 先读

1. `CURRENT_RESEARCH.md`
2. `research/cross_index_degree_transfer_utility_v1/PROGRAM_STATE.json`
3. `research/cross_index_degree_transfer_utility_v1/RESULTS.md`
4. `research/cross_index_degree_transfer_utility_v1/DECISIVE_RECEIPT.json`
5. `research/cross_index_degree_transfer_utility_v1/EXECUTION_RECEIPT.json`
6. `research/cross_index_degree_transfer_utility_v1/evidence/VALIDATION_RESULTS.json`
7. M3 / D4 / D3 / D2 / V19 与 V2治理；历史分支问题再读 `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`。
8. reception问题再读 `research/prospective_reception_recorder_v1/` 和 D5R。

## 最新结论

固定问题是：target 自己的 D4-style current I/V 已知以后，other index 同一 E15 的 current I/V 是否还能带来实用未来风险增量。

C=own baseline；X=C+other-current；L=C+完全等复杂度 other-lag。只有 X 同时打赢 C 和 L 才能晋升。

决定性 Action run `34677297901` 使用第一次 Development fit 在 Validation 前冻结的精确模型 SHA：

`7eae7142323b38c5ae54618745e9ad9891c00afb09d02e8eb8def4490675f6b6`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），paired coverage 都是100%。

12项正式比较全部未过冻结1% practical relative gate，全部5日块Bonferroni区间下界<=0。最大 pooled 改进也只有60m tail X-vs-C的 **+0.14197%**；绝对Brier gain仅`0.00011937`，低于`0.0005`。

多个STAR50 target slice为负，而CSI1000部分slice为正；这不能成为事后改成“只做STAR50→CSI1000”的理由。协议已经明确禁止按方向、lag、state、threshold或horizon救结果。

因此：

- other-current I/V 不进入 D5 consumer；
- 不给 V19 增加 cross-index state；
- 不开单向 cross-index rescue；
- 不恢复 relative-value / router / PnL 线。

完整 Action evidence 已按原字节持久化到 `research/cross_index_degree_transfer_utility_v1/evidence/`。

## 前置 M3 结论

M3 有 own-I/V 之外的 future-RMS 信息，但 current-vs-lagged-M3 的实际 refresh 增量没有达到冻结1%门槛，因此仍是 `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`，不进入 D5/V19。

## 历史 backlog

remaining executable legacy backlog = 0。不要再把旧 detector、RMR、V11 duplicate、risk-gate takeover、old router 或 v0.6.17 当成待执行任务。v0.6.17 的事前 identity 缺口不可事后补造。

## 接下来执行边界

本轮 cross-index current-degree 规格已经正式关闭。下一项只有在出现**真正不同的因果风险机制**且能在看结果前冻结问题/比较器/门槛时才允许开启；不能把“继续研究”解释成修改本轮方向、lag、状态或阈值。

不查 BlackBox，不读受保护2026逐行数据，不算PnL，不恢复router，不开D6/V20，不提高production authority。
