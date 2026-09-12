# STAR50 / CSI1000 当前权威索引

## 当前断点：DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING

[当前任务](../CURRENT_RESEARCH.md) → [程序状态](../research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [云端验收结果](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_RESULTS.md) → [云端执行回执](../research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json) → [DataHub适配结果](../research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_RESULTS.md) → [接入契约](../research/prospective_reception_recorder_v1/DATAHUB_INTEGRATION.md) → 原[recorder协议](../research/prospective_reception_recorder_v1/PROTOCOL.md) / [schema](../research/prospective_reception_recorder_v1/SCHEMA.json)。

## 最新云端验收

GitHub Actions run `34666927078` 成功：完整恢复并验证用户既有handoff ZIP；20个manifest文件全匹配；完整审计9,492行（两指数各4,746）；4,746点跨指数observation grid完全一致；41项recorder/adapter测试PASS；DataHub源码seam复核与V2治理validator通过。artifact id `10288693269`。

真实DataHub源码的最早可控采集边界仍是 **TDX Python SDK `get_security_quotes()`返回后、DataHub `parse_quotes()`之前**。这是SDK-return/DataHub-ingress，不是wire-level arrival。

历史行情有效性不受historical received_at缺失影响。D5R只说明历史实测本机到达时钟不可恢复。

## 保持原样的历史阶段证据

- [D5R](../research/reception_clock_adjudication_d5r/RESULTS.md)：历史真实received_at不可用；
- [D5](../research/state_degree_consumer_d5/RESULTS.md)：本仓consumer工程验收；
- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：连续属性分目标有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：三状态增量效用未过原实际门槛；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟历史工程回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)及V18/V17/V16冻结证据。

## 下一研究边界

云端工程验收已经完成，不再把“本地wiring测试”当成用户待办。reception线若要提升到实测层，只能等待未来真实本机feed产生、且治理允许使用的true-reception evidence。

在此之前仍可继续不依赖reception clock的云端研究，但不因缺日志启动D6/V20，不查BlackBox逐行细节，不计算PnL，不接生产authority。

`cloud_acceptance_supported=true`; `live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
