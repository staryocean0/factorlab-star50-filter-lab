# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓研究当时可知的市场风险环境与下游适用条件，不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前科学结论

最新决定：**`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [程序状态](research/cross_index_degree_transfer_utility_v1/PROGRAM_STATE.json) → [正式结果](research/cross_index_degree_transfer_utility_v1/RESULTS.md) → [决定性回执](research/cross_index_degree_transfer_utility_v1/DECISIVE_RECEIPT.json) → [原始Action证据](research/cross_index_degree_transfer_utility_v1/evidence/VALIDATION_RESULTS.json)。

问题是在 target 自己的 D4-style current I/V 已知后，另一指数同一 E15 的 current I/V 是否仍提供实用未来风险增量。X=current-other，L=完全等复杂度 lagged-other；只有 X 同时打赢 own-C 和 L 才允许晋升。

决定性 run `34677297901` 使用 Validation 前第一次冻结的模型 SHA256：

`7eae7142323b38c5ae54618745e9ad9891c00afb09d02e8eb8def4490675f6b6`。

15/30/60m Validation 样本分别 39,770 / 33,950 / 22,310，paired coverage 100%。12项 comparison 全部未过冻结1% practical gate，且全部5日块Bonferroni区间跨0。最大 pooled 点估计也只有60m tail X-vs-C **+0.14197%**，绝对Brier gain `0.00011937` < `0.0005`。

因此：**other index current degree 与 own degree 高度相关，但 own current I/V 已知后，剩余边际不足以晋升。** 不把它加进D5/V19，也不允许按单向index、lag、state、threshold、horizon事后救结果。

完整决定性 artifact `10292433776`（ZIP SHA256 `1ab8a12d77beb15c7aba5880a588c3475dc7d6270ca121eb95056ef9aa56ba92`）已经按原字节持久化进研究目录。

## 前置 M3 结论

`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 保持不变。current M3 相对 own current-I/V baseline 对future-RMS有额外信息，但相对等复杂度 lagged-M3 的refresh增量只有约 +0.433% / +0.579% / +0.183%，低于冻结1% practical gate，因此不进D5/V19。

## 历史 research backlog 已关闭

112个research分支审计标出的12个高召回“未闭环”对象已经逐项裁决，当前 **remaining executable legacy backlog = 0**。

[机器closeout ledger](docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json) → [人类说明](docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.md) → [v0.6.17 identity closeout](docs/research/session_aware_information_set_bounds_v0617/CLOSEOUT_RECEIPT_20260912.json)。

旧detector已失败或被V17/V19吸收；两个RMR reversal未建立broad signal且不属当前scope；old highvol-router含PnL/route/hold/cost等已退役；v0.6.17因原协议要求的两个事前identity在严格历史审计中都不存在而永久fail-closed。

## 并行 reception 状态

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`** 继续有效。历史D5R仍确认没有逐条真实本机`received_at`；recorder/adapter/handoff云端工程验收已完成，未来真实arrival只能等待未来物理feed生成且受V2治理允许的数据。

## 保留的历史结论

- [risk-coordinate frozen Validation](docs/research/risk_coordinate_validation_v1/RESULT.md)：不完全复制，禁止事后降门槛救M3 amplitude axis；
- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D2](research/causal_state_delivery_d2/RESULTS.md)：因果双时钟回放；
- [D3](research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：own current I/V 分目标有限支持；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：bounded research consumer；
- [D5R](research/reception_clock_adjudication_d5r/RESULTS.md)：历史实测reception时钟不可恢复。

当前 cross-index current-degree 规格已经关闭。只有发现一个独立、可事前冻结的**新因果风险机制**时才开新实验；不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`cross_index_current_degree_incremental_supported=false`; `historical_research_backlog_closed=true`; `current_m3_consumer_promotion=false`; `cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
