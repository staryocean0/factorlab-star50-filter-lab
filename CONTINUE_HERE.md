# 接续入口：DataHub reception adapter 离线契约已通过，待本地 wiring

当前状态：**DATAHUB_RECEPTION_ADAPTER_V1_OFFLINE_CONTRACT_ACCEPTED_LOCAL_WIRING_PENDING**。
历史接收判定仍是 **D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

先读：
1. `CURRENT_RESEARCH.md`
2. `research/prospective_reception_recorder_v1/PROGRAM_STATE.json`
3. `research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_RESULTS.md`
4. `research/prospective_reception_recorder_v1/DATAHUB_INTEGRATION.md`
5. `research/prospective_reception_recorder_v1/datahub_adapter.py`
6. `research/prospective_reception_recorder_v1/DATAHUB_ADAPTER_EXECUTION_RECEIPT.json`
7. 原 prospective recorder `PROTOCOL.md` / `SCHEMA.json`
8. D5R、D5/D4/D3/D2/V19 证据与 V2 治理。

## 已完成

真实 DataHub 源码已审计，不再追历史 vendor raw。当前最早可控 seam 为 `TdxHqApiAdapter.get_security_quotes()` 的 Python SDK 返回之后、DataHub `parse_quotes()` 之前。适配层利用既有 `hq_api` / `quotes_parser` 依赖注入，无需重写轮询、fallback、stream coordinator 或 recording coordinator。

当前会话实际执行23项适配层测试全部通过并通过compile检查。SDK payload保持不变；receipt先于parser；parser失败也保留receipt；payload中途改写/cardinality漂移会失败关闭；当前parser生成的`timestamp=now(UTC)`不会被误称vendor event time或received_at。

用户交付的2025-06-11 normalized历史样本为两个指数各4,746行，继续作为有效历史行情和schema语义参考使用。不存在历史received_at只限制历史实测延迟声明，不质疑历史行情本身。

## 下一实际动作

把 `TdxReceptionHqTap` 与 `ReceptionAwareQuotesParser` 挂到本地 DataHub 真实依赖注入点。第一阶段仅用synthetic或治理允许的replay/input验证 wiring、持久化、重启instance、重复/坏消息、性能开销与失败恢复；通过后再开始受保护前瞻采集。

当前已过2026-08-21，新采逐行subject数据可能属于pending BlackBox-V1。真实采集行先留受保护本地层，不上传公开GitHub/聊天、不直接做详细研究。

不要重做V19/D2-D5，不开D6/V20，不把SDK-return timing叫raw TCP latency，不用parser `now()`/available_at/batch ingested_at代替received_at，不接交易router或生产registry。

`live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `production_authority=false`。
