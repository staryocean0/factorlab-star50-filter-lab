# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓研究当时可知的市场风险环境与下游适用条件，不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前科学结论

最新决定：**`ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [程序状态](research/degree_trajectory_utility_v1/PROGRAM_STATE.json) → [正式结果](research/degree_trajectory_utility_v1/RESULTS.md) → [决定性回执](research/degree_trajectory_utility_v1/DECISIVE_RECEIPT.json) → [原始Action证据](research/degree_trajectory_utility_v1/evidence/VALIDATION_RESULTS.json)。

本轮正式验收 D4/D5 已经传输但从未获得独立预测验证的 one-step degree trajectory / delta 信息。C=own current-I/V baseline；T=C+lag1 confirmed degree；O=C+完全等复杂度lag2 control。current degree已在C中，所以lag1与`current-lag1` delta在新增原始信息上等价。

决定性 run `34680352701` 使用 Validation 前冻结的模型 SHA256：

`04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188`。

15/30/60m Validation n=39,770 / 33,950 / 22,310，coverage均100%。12项 formal comparison 全部低于冻结1% practical gate。

future-RMS relative gains（T vs C / T vs O）：

- 15m：+0.11415% / +0.11321%；
- 30m：**+0.14957% / +0.15160%**；
- 60m：+0.02416% / **-0.04063%**。

30m T-vs-C 的5日调整区间下界略为正，说明最近一步degree并非“零信息”；但T-vs-O区间跨0，而且约0.15%的量级远低于1%。tail全部未获支持，15/30m T-vs-O tail为负，absolute Brier gains均远低于`0.0005`。

因此：**D4/D5 的 `lag_intensity`、`lag_ratio`、`delta_intensity`、`delta_ratio` 可以继续作为描述/诊断/消费字段，但没有独立预测 promotion。** 不变成D5 decision gate，不修改V19。

Validation artifact `10294052627`，ZIP SHA256 `60c9133dbf6632b2f7dcf9795c70038ed50f4d18718fc54aaf2378010ceaeba8`；完整 evidence 已按原字节持久化进研究目录。

禁止用本轮 reusable Validation 结果事后做 lag3/lag4、smoothing/decay、alternate normalizer、单index/state/time slice、transform/ridge/horizon tuning 或删除O control。

## 前置科学结论

- 12-bar historical shock burden：小统计信号但无实用、稳定的shock-specific增量；
- cross-index current degree：不支持增量promotion；
- current M3 refresh：不支持current-refresh practical increment；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：own current I/V 对指定endpoint有限支持；
- [D3](research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：bounded research consumer。

历史 research backlog 已关闭，remaining executable legacy backlog = 0。并行 reception 仍为 `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`。

下一科学题必须是独立、可事前冻结的新因果风险机制；不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`degree_trajectory_incremental_supported=false`; `delta_independent_predictive_promotion=false`; `d5_contract_unchanged=true`; `historical_shock_burden_incremental_supported=false`; `historical_research_backlog_closed=true`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
