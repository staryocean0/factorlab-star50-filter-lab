# 接续入口：前瞻 reception recorder 参考实现已通过，待本地接入

当前状态：**PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING**。
历史接收判定仍是 **D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

先读：
1. `CURRENT_RESEARCH.md`
2. `research/prospective_reception_recorder_v1/PROGRAM_STATE.json`
3. `research/prospective_reception_recorder_v1/PROTOCOL.md`
4. `research/prospective_reception_recorder_v1/SCHEMA.json`
5. `research/prospective_reception_recorder_v1/LOCAL_INTEGRATION_HANDOFF.md`
6. `research/prospective_reception_recorder_v1/EXECUTION_RECEIPT.json`
7. `research/reception_clock_adjudication_d5r/RESULTS.md`
8. 原 D5/D4/D3/D2/V19 证据与 V2 数据治理。

## 已完成

参考 recorder 与独立 validator 已实现。会话内18项合成测试、编译和一个独立JSONL CLI验证样例通过；没有读取新行情、没有Actions、没有安装到DataHub、没有真实received_at行。

核心语义：真实feed callback入口先打本机UTC wall-clock、monotonic_ns、本地sequence和raw payload identity，再解析event time/symbol/price。wall-clock可因NTP回拨而倒退，monotonic不得倒退；重启后新 recorder_instance_id，不跨进程偷接monotonic。

## 下一实际动作

按 LOCAL_INTEGRATION_HANDOFF 在本地 DataHub 真正的 feed callback 中接入该语义。第一阶段只用synthetic/允许的replay数据，验证插桩位置、重复/坏消息、重启、持久化与性能开销；不要把这一步叫实测feed延迟。

当前已过2026-08-21。真实新行情可能属于pending BlackBox-V1，因此即使recorder开始运行，逐行新行情/接收时间也必须留在受保护本地数据层，不上传公开GitHub/聊天、不直接研究。后续使用需要明确数据角色或预注册聚合接口。

不要重做V19/D2-D5，不开D6/V20，不用available_at/batch ingested_at/mtime代替received_at，不接交易router或生产registry。

`live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `production_authority=false`。
