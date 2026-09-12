# 本地接续：前瞻真实 reception recorder 待接入 DataHub

当前权威见 `CURRENT_RESEARCH.md`、`CONTINUE_HERE.md` 与 `research/prospective_reception_recorder_v1/`。

历史本地只读检索已经证明 `000688.SH` / `000852.SH` 没有逐条真实本机 `received_at`；D5R 原结论保持 `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`。不要再从历史 `available_at`、batch `ingested_at`、mtime、observation time 或 row_index 反推接收时钟。

云端现在已经实现参考 recorder 与独立 validator，并通过18项合成测试、编译和一组CLI验证。当前状态：`PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING`。

本地下一任务不是重跑旧研究，而是按 `research/prospective_reception_recorder_v1/LOCAL_INTEGRATION_HANDOFF.md` 将 stamp 语义放到真实feed callback最前端：先记录UTC wall-clock、monotonic_ns、本地sequence和raw payload identity，再解析/排队。第一阶段只能用synthetic/允许replay验证位置、开销、重启和持久化，不声称实测feed latency。

当前日期已过2026-08-21。真实新行情可能属于pending BlackBox-V1；实际采集开始后，逐行行情和接收时间必须留在受保护本地层，不上传公开GitHub或聊天，不直接用于调参/诊断，直到治理明确允许。

V19/D2/D3/D4/D5原结论、其他仓和生产registry不改。`live_recorder_installed=false`; `measured_feed_latency_supported=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
