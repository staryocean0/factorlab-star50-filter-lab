# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓用于研究行情环境与策略适用条件，不开发交易动作、方向、仓位或收益 router。

## 当前：DataHub reception adapter 离线契约已通过

当前断点：**DATAHUB_RECEPTION_ADAPTER_V1_OFFLINE_CONTRACT_ACCEPTED_LOCAL_WIRING_PENDING**。

历史 D5R 仍确认两个指数没有逐条真实本机 `received_at`；这只限制历史实测延迟声明，不影响既有历史行情数据的使用。前瞻 recorder 参考实现已通过，现又基于用户实际交付的 DataHub 源码完成接入层：当前源码中最早可控测量点是 **TDX Python SDK `get_security_quotes()` 返回之后、DataHub `parse_quotes()` 之前**。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [程序状态](research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [DataHub结果](research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_RESULTS.md) → [接入契约](research/prospective_reception_recorder_v1/DATAHUB_INTEGRATION.md) → [adapter源码](research/prospective_reception_recorder_v1/datahub_adapter.py)。

当前会话实际执行23项DataHub适配层测试全部通过；原recorder 18项测试证据保留。适配器不改变SDK返回对象或DataHub parser输出，parser失败仍保留receipt，payload被中途修改会拒绝；DataHub parser生成的`timestamp=now(UTC)`不会被冒充vendor event time或received_at。

用户交付的2025-06-11历史 normalized 样本（`000688.SH` / `000852.SH` 各4,746行）作为有效历史行情与schema参考直接使用，不再要求更底层vendor raw证明。它没有历史received_at，这与历史行情有效性是两件事。

## 保留的研究结论

[V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)、[D2](research/causal_state_delivery_d2/RESULTS.md)、[D3](research/causal_state_utility_d3/RESULTS.md)、[D4](research/continuous_risk_utility_d4/RESULTS.md)、[D5](research/state_degree_consumer_d5/RESULTS.md)、[D5R](research/reception_clock_adjudication_d5r/RESULTS.md)均保持原判。本轮不是D6/V20，也不是新预测证据。

## 下一步与治理

下一步只是在本地 DataHub 把已测试的 `TdxReceptionHqTap` / `ReceptionAwareQuotesParser` 挂到现有依赖注入点，先用synthetic或治理允许的replay/input核验真实wiring、持久化、重启、错误/重复消息与性能开销；然后才可开始受保护 prospective capture。

当前已过 `2026-08-21`，未来新subject逐行数据可能属于pending BlackBox-V1，必须先留受保护本地层，不直接上传公开GitHub/聊天或详细研究。

`measured_feed_latency_supported=false`; `live_recorder_installed=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
