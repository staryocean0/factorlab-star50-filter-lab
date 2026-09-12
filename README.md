# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓研究当时可知的市场风险环境与下游适用条件，不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前科学结论

最新决定：**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [M3程序状态](research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json) → [M3结果](research/activity_degree_incremental_utility_v1/RESULTS.md) → [执行回执](research/activity_degree_incremental_utility_v1/EXECUTION_RECEIPT.json) → [原始Action证据](research/activity_degree_incremental_utility_v1/evidence/VALIDATION_RESULTS.json)。

在继承的 `<30bp` 低幅度表面上，current M3 相对 D4-style current-I/V baseline **确有额外 future-RMS 信息**：15m `A vs C` Validation相对 squared-loss 改进约 +2.175%，单项全部gate通过；30/60m点估计约 +2.806% / +3.619%，但Development支持不足。

但 promotion 需要 current M3 同时打赢等复杂度 lagged-M3 对照。15/30/60m `A vs N` 只有约 +0.433% / +0.579% / +0.183%，均低于冻结1% practical gate；15/30m 2023 forward为负，30/60m还存在Development样本不足，60m Validation coverage仅92.438%。tail全部不晋升。

因此结论是：**M3有信息，但没有证据支持把“当前刷新一次M3”晋升为D4/D5之外的新实用风险坐标。** 不调M3 bands、30bp surface、ridge、horizon、sample gate或lagged control救结果。

决定性 Action run `34670357953`；Validation artifact `10290917834`，ZIP SHA256 `a734a0083c9d197188591fa548668cdbc3f2a86df00b783f68f41acfecf69940`。完整证据已原字节保存在研究目录。重复fit数值审计最大系数差 `8.16e-15`，freeze-before-Validation链保持完整。

## 并行 reception 状态

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`** 继续有效。历史D5R仍确认没有逐条真实本机`received_at`；DataHub recorder/adapter/handoff云端工程验收已完成，未来真实arrival只能等待未来物理feed生成且受V2治理允许的数据。

## 保留的历史结论

- [risk-coordinate frozen Validation](docs/research/risk_coordinate_validation_v1/RESULT.md)：不完全复制，禁止事后降门槛救M3 amplitude axis；
- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D2](research/causal_state_delivery_d2/RESULTS.md)：因果双时钟回放；
- [D3](research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：current I/V 分目标有限支持；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：bounded research consumer；
- [D5R](research/reception_clock_adjudication_d5r/RESULTS.md)：历史实测reception时钟不可恢复。

下一步优先清理历史 research backlog，区分“结果未持久化 / 已被后续证据覆盖 / 因原事前身份条件缺失而不可执行”。不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复router、不为V19开V20、不因缺reception日志开D6、不提高production authority。

`current_m3_consumer_promotion=false`; `current_m3_refresh_practical_increment_supported=false`; `cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
