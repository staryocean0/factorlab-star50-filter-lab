# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓研究当时可知的市场风险环境与下游适用条件，不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前科学结论

最新决定：**`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [程序状态](research/signed_risk_asymmetry_utility_v1/PROGRAM_STATE.json) → [正式结果](research/signed_risk_asymmetry_utility_v1/RESULTS.md) → [决定性回执](research/signed_risk_asymmetry_utility_v1/DECISIVE_RECEIPT.json) → [原始Action证据](research/signed_risk_asymmetry_utility_v1/evidence/VALIDATION_RESULTS.json)。

本轮正式验收此前未回答的 signed-history 风险轴：过去12个有效已完成5m收益的正负结构，在 own current E15 intensity / volatility-ratio 与绝对幅度历史已知以后，是否还能稳定增加未来非PnL风险信息。

固定比较为 C/A/M：

- C = 84-column own-index D4-style baseline；
- A = C + signed-energy / signed-absolute-return imbalance；
- M = C + 同窗口、同复杂度 magnitude-only control；
- A/M = 104 columns，同 schema、state interactions、ridge 与 fit rows；
- 当前 unfinished 5m bar 通过 `shift(1)` 明确排除。

决定性 run `34681733485` 使用 Validation 前冻结的模型 SHA256：

`92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2`。

15/30/60m Validation n=39,770 / 33,950 / 22,310，coverage 均100%。六个 endpoint×horizon joint promotion 全部 false，12项 formal comparison 全部 `supported=false`。

最强的是60m future-RMS：

- A vs C：**+1.35593%**；
- A vs M：**+1.02822%**。

但这两个 pooled 点估计即使都越过冻结1% practical threshold，仍不能晋升：family-adjusted 5-day CI 下界都小于0，而且 `000688.SH` 两组 absolute gain 都为负，`000852.SH` 两组都明显为正。预注册协议要求 adjusted interval >0 且每个 symbol slice 非负，因此正式拒绝。

所以正确解释是：**signed asymmetry 在 CSI1000 上有较强60m RMS提示，但在 STAR50 上同一固定表示为负，尚未证明跨两指数稳健的共同底层风险机制。** 禁止事后只保留中证1000。

Tail 也未获支持；最强 absolute Brier gain=`0.0004583935491319103`，低于冻结 `0.0005`，且调整后区间跨0。

Validation artifact `10293179281`，ZIP SHA256 `f9597bb93b91a481b6a07a225dfae22c90c2f9178216079f41e6053f3076af79`；`VALIDATION_RESULTS.json` SHA256 `c0ffac04a70fed796bfb766876bd51f1781c788e4648b202eefd3b9ef01b203b`。完整 evidence 已按原字节持久化进研究目录。

因此：不向D5增加 signed-asymmetry field/gate，不修改V19，不产生方向/交易/PnL含义，不创建新state/threshold/production field。禁止用本轮 reusable Validation 做 CSI1000-only、6/24/48-bar、decay/EWMA、skew/downside-count、selected slice 或 gate/regularization rescue。

## 前置科学结论

- one-step degree trajectory/delta：最多约0.15%小信号，不支持独立预测promotion；D4/D5 delta继续只作描述/诊断；
- 12-bar historical shock burden：小统计信号但无实用、稳定的shock-specific增量；
- cross-index current degree：不支持增量promotion；
- current M3 refresh：不支持current-refresh practical increment；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：own current I/V 对指定endpoint有限支持；
- [D3](research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：bounded research consumer。

历史 research backlog 已关闭，remaining executable legacy backlog = 0。并行 reception 仍为 `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`。

下一科学题必须是与 V19 / D4 / M3 / cross-index / shock-memory / trajectory / signed-asymmetry 真正不同、且可事前冻结的新因果风险机制；如果仓库审计找不到这样的独立机制，正确动作是 hold / maintain authority，而不是继续制造窗口、阈值或单指数救援。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`signed_return_asymmetry_incremental_supported=false`; `pooled_60m_rms_one_percent_gate_met=true`; `cross_symbol_robustness_supported=false`; `single_index_rescue_authorized=false`; `signed_asymmetry_consumer_promotion=false`; `degree_trajectory_incremental_supported=false`; `delta_independent_predictive_promotion=false`; `d5_contract_unchanged=true`; `historical_shock_burden_incremental_supported=false`; `historical_research_backlog_closed=true`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
