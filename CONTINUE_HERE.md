# 接续入口：current M3 refresh 已判不晋升

最新科学状态：**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

并行 reception 工程状态仍是：**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

## 先读

1. `CURRENT_RESEARCH.md`
2. `research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json`
3. `research/activity_degree_incremental_utility_v1/RESULTS.md`
4. `research/activity_degree_incremental_utility_v1/EXECUTION_RECEIPT.json`
5. `research/activity_degree_incremental_utility_v1/evidence/VALIDATION_RESULTS.json`
6. `docs/research/risk_coordinate_validation_v1/RESULT.md`
7. D4 / D3 / D2 / V19 与 V2治理；reception问题再读 `research/prospective_reception_recorder_v1/` 和 D5R。

## 最新结论怎么理解

在继承的低幅度表面上，current M3 相对 D4-style C（历史 + previous-state/age + current I/V）对未来 log-RMS 有明显正增量；15m `A vs C` 单独通过全部 gate，Validation相对改进约 **+2.175%**。

但真正的 promotion 问题要求 current M3 还必须打赢**等复杂度 lagged-M3**：15/30/60m `A vs N` 只有约 **+0.433% / +0.579% / +0.183%**，均未过冻结的1% practical gate；15/30m 2023 forward还为负，30/60m Development样本也不足。tail全部未晋升。

因此：

- 不把 current M3 加进 D5 consumer；
- 不把 M3 变成 V19 state threshold；
- 不移动M3 band、30bp surface、ridge、horizon、block或sample gate救结果；
- 不删除lagged-M3对照；
- 不把“M3有信息”偷换成“current refresh值得上线”。

决定性 Action run `34670357953`；完整artifact已写入 `research/activity_degree_incremental_utility_v1/evidence/`。数值复现audit run `34670797290` 证明重复fit最大系数差仅 `8.16e-15`，同一run内freeze-before-Validation链完整。

## 接下来执行什么

先收口历史 research backlog，而不是继续造 M3 变体。把旧分支分为：

- 已执行、结果未持久化；
- 已被后续正式机制取代；
- 因原 frozen preregistration 所需的事前身份/输入证据缺失而不可合法执行。

只有审计后出现一个**独立的新因果机制问题**，才新开实验。

reception线不再向本地追历史raw；云端代码/历史样本验收已完成。只有未来真实本机feed产生、且治理允许使用的true-reception observations才能升级实测延迟证据。

不查BlackBox，不读受保护2026逐行数据，不算PnL，不恢复router，不开D6/V20，不提高production authority。
