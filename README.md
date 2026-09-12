# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓用于研究行情环境与策略适用条件，不开发交易动作、方向、仓位或收益 router。

## 当前：DataHub reception 云端工程验收已完成

当前断点：**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING**。

历史 D5R 仍确认没有逐条真实本机 `received_at`；这只限制历史实测延迟声明，不影响历史行情数据使用。前瞻 recorder、DataHub adapter 与完整 handoff 云端验收现已全部完成。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [程序状态](research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [云端验收结果](research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_RESULTS.md) → [云端回执](research/prospective_reception_recorder_v1/CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json) → [DataHub adapter结果](research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_RESULTS.md)。

GitHub Actions run `34666927078` 已实际完成：

- 既有 handoff ZIP bytes/SHA256 验证；
- 20个manifest文件逐一校验；
- 两指数各4,746行，共 **9,492行**完整审计；
- 两指数4,746点 observation grid 完全一致；
- 18项recorder + 23项adapter = **41项测试全部通过**；
- 真实DataHub源码 `get_security_quotes` → `parse_quotes` seam再验证；
- V2 data-governance validator通过；
- evidence artifact id `10288693269`。

当前源码支持的最早可控测量边界是 **TDX Python SDK返回之后、DataHub parser之前**。它是SDK-return/DataHub-ingress timing，不是raw TCP/frame arrival；parser自己的`datetime.now(UTC)`也不是vendor event time或历史received_at。

GitHub runner上的synthetic wrapper增量开销 median约59.3µs/两quote iteration，仅为描述性工程数据，不是live feed latency或production gate。

## 保留的研究结论

[V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)、[D2](research/causal_state_delivery_d2/RESULTS.md)、[D3](research/causal_state_utility_d3/RESULTS.md)、[D4](research/continuous_risk_utility_d4/RESULTS.md)、[D5](research/state_degree_consumer_d5/RESULTS.md)、[D5R](research/reception_clock_adjudication_d5r/RESULTS.md)均保持原判。本轮不是D6/V20，也不是新预测证据。

## 当前剩余边界

云端可执行工程验收已完成。reception线现在真正缺的是未来本机真实feed运行后才会产生的true-reception observations；GitHub Actions不能制造这种物理到达数据。

当前已过 `2026-08-21`，未来新subject逐行数据可能属于pending BlackBox-V1，必须先受保护存储并服从V2数据角色。没有治理允许的真实reception evidence之前，不声明实测延迟、不查询BlackBox细节、不提高production authority。

`cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `live_recorder_installed=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
