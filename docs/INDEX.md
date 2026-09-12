# STAR50 / CSI1000 当前权威索引

## 当前主断点：DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [reception程序状态](../research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [云端验收结果](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_RESULTS.md) → [云端执行回执](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json)。

## 最新历史研究收口

[risk-coordinate Validation正式结果](research/risk_coordinate_validation_v1/RESULT.md) → [执行回执](research/risk_coordinate_validation_v1/EXECUTION_RECEIPT.json) → 原冻结协议/runner。

正式结论：**RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE**。

原Action `34303912251` 与复现Action `34667783528` 在110,911个2024/2025 Validation rows及所有检查上逐项一致。state-persistence轴四个index×year池全部复制；M3极端band的未来15m RMS effect-size gate全部通过，但三个Unsafe极端格未达到冻结最小n门槛，因此M3完整amplitude axis不晋升。不得事后调门槛、合并年份或移动M3 bands救结果。

## Reception云端验收

Action `34666927078` 成功：handoff ZIP与20个manifest文件全量校验；9,492行完整审计；两指数4,746点observation grid exact match；41项recorder/adapter测试PASS；真实DataHub源码seam与V2治理validator通过。

DataHub最早可控采集边界是 **TDX Python SDK `get_security_quotes()`返回后、DataHub `parse_quotes()`之前**，不是wire-level arrival。历史行情有效性不受historical received_at缺失影响。

## 历史backlog接管

Action `34668006394` 扫描112个research分支：81 RESULT_PRESENT；8 EXECUTED_RESULT_NOT_PERSISTED；1 FROZEN_NOT_SUCCESSFULLY_EXECUTED；2 FROZEN_DESIGN_ONLY；1 EXECUTED_NO_RESULT_MARKER；19 OTHER。

下一优先审计：`research/session-aware-information-set-bounds-v0617-20260907`，先判断是否已被后续证据取代，再决定是否按冻结协议原样执行。

## 保持原样的历史阶段证据

- [D5R](../research/reception_clock_adjudication_d5r/RESULTS.md)：历史真实received_at不可用；
- [D5](../research/state_degree_consumer_d5/RESULTS.md)：bounded consumer工程验收；
- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：连续属性分目标有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：三状态增量效用未过原实际门槛；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟历史工程回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)及V18/V17/V16冻结证据。

不为V19 accuracy开V20，不因缺日志强开D6，不查BlackBox逐行细节，不计算PnL，不恢复交易router，不提高production authority。

`risk_coordinate_full_replication=false`; `risk_coordinate_threshold_retune_allowed=false`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `production_authority=false`。
