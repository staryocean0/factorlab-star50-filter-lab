# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓研究当时可知的市场风险环境与下游适用条件，不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前科学结论

最新决定：**`HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [程序状态](research/historical_shock_burden_utility_v1/PROGRAM_STATE.json) → [正式结果](research/historical_shock_burden_utility_v1/RESULTS.md) → [决定性回执](research/historical_shock_burden_utility_v1/DECISIVE_RECEIPT.json) → [原始Action证据](research/historical_shock_burden_utility_v1/evidence/VALIDATION_RESULTS.json)。

固定问题是：own current E15 I/V、previous state 和 recent-shock age 已知以后，最近12个有效已完成交易return bars中的确认 3σ shock count / excess 是否仍提供实用未来风险增量。

C=own D4-style baseline；S=C+shock-memory；H=C+完全等复杂度 high-vol-memory control。S/H 均为104 columns，C为84 columns。只有S同时打赢C和H才允许晋升。

决定性 run `34679293167` 使用 Validation 前冻结的模型 SHA256：

`65f9403e3aae00873432403f833c1d8772429c5172fc7f3fd76581a19a4222d3`。

15/30/60m Validation样本分别39,770 / 33,950 / 22,310，memory coverage 100%。12项正式comparison全部未过冻结1% practical gate；tail absolute Brier gains全部远低于`0.0005`。

future-RMS pooled gain：

- 15m：S-vs-C +0.16994%，S-vs-H +0.16951%；
- 30m：+0.18307% / +0.19834%；
- 60m：+0.24096% / +0.34717%。

15m S-vs-C的5日调整区间下界略为正，说明不能说shock-memory完全没信息；但S-vs-H区间跨0，且所有点估计距离1%实用门槛很远。因此**没有证据支持把累计shock burden晋升为own current I/V + recent-shock-age之外的新风险坐标。**

这不推翻V5的“reshock resets recovery clock”。本轮测试的是累计burden在timing/current-degree之外是否有额外实用价值，答案是否定的。

完整决定性 artifact `10294046103`（ZIP SHA256 `943d44b741888307c978b4504edeb704ecdeedb75ecdf8f521eec07a4809f215`）已按原字节持久化进研究目录。

禁止用本轮 reusable Validation 结果事后调 12→6/24 bar、decay、3σ/1.5 threshold、单index/state/time slice、horizon、ridge或删除H control。S不进入D5/V19。

## 前置科学结论

- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`：other-current I/V 在 own current I/V 已知后边际不足，不进D5/V19；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`：M3 current-refresh 相对等复杂度lagged-M3未过1% practical gate；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：own current I/V 对指定endpoint有限支持；
- [D3](research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：bounded research consumer。

## 历史 backlog 与 reception

112个research分支审计标出的旧对象已全部裁决，**remaining executable legacy backlog = 0**。不要按旧branch名重开已关闭实验。

并行 reception 状态仍是 **`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。历史D5R确认没有真实逐条本机`received_at`；未来arrival证据只能由未来物理feed生成并受V2治理。

本轮12-bar shock-memory规格已经关闭。只有发现独立、可事前冻结的**新因果风险机制**时才开新实验；不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`historical_shock_burden_incremental_supported=false`; `cross_index_current_degree_incremental_supported=false`; `current_m3_consumer_promotion=false`; `historical_research_backlog_closed=true`; `cloud_acceptance_supported=true`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
