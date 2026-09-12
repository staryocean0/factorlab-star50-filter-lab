# STAR50 / CSI1000 当前权威索引

## 当前断点：DATAHUB_RECEPTION_ADAPTER_V1_OFFLINE_CONTRACT_ACCEPTED_LOCAL_WIRING_PENDING

[当前任务](../CURRENT_RESEARCH.md) → [程序状态](../research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [DataHub适配结果](../research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_RESULTS.md) → [接入契约](../research/prospective_reception_recorder_v1/DATAHUB_INTEGRATION.md) → [adapter源码](../research/prospective_reception_recorder_v1/datahub_adapter.py) → [执行回执](../research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_EXECUTION_RECEIPT.json) → 原[recorder协议](../research/prospective_reception_recorder_v1/PROTOCOL.md) / [schema](../research/prospective_reception_recorder_v1/SCHEMA.json)。

真实DataHub源码已经确认最早可控采集边界：TDX Python SDK `get_security_quotes()`返回后、DataHub `parse_quotes()`之前。23项适配层测试通过；原参考recorder 18项测试证据保留。该时钟是SDK-return/DataHub-ingress，不冒充raw TCP/frame到达。

用户交付的2025-06-11 normalized历史样本为两个指数各4,746行，作为有效历史行情与schema语义参考直接使用；没有historical received_at只限制实测延迟声明，不质疑历史行情本身。

## 保持原样的历史阶段证据

- [D5R](../research/reception_clock_adjudication_d5r/RESULTS.md)：历史真实received_at不可用；
- [D5](../research/state_degree_consumer_d5/RESULTS.md)：本仓consumer工程验收；
- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：连续属性分目标有限支持；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：三状态增量效用未过原实际门槛；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟历史工程回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)及V18/V17/V16冻结证据。

## 下一可执行动作

本地只需把已测试wrapper挂到DataHub现有`hq_api`/`quotes_parser`依赖注入点，先用synthetic或治理允许的replay/input验证真实wiring、持久化、重启、坏/重复消息和性能开销。通过后再开始受保护前瞻采集。

当前已过2026-08-21，新采逐行subject数据可能属于pending BlackBox-V1，先留受保护本地层；不直接上传逐行内容或详细研究。

`live_recorder_installed=false`; `measured_feed_latency_supported=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
