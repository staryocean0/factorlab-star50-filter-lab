# 科创50 / 中证1000：因果K线风险属性模块

**状态上下文 + 连续风险程度 + 时间与可用性约束。** 本仓用于研究行情环境与策略适用条件，不开发交易动作、方向、仓位或收益 router。

## 当前：历史真实接收时钟不存在，前瞻 recorder 参考实现已通过

当前断点：**PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING**。

此前 D5R 已确认：两个指数历史存储没有逐条真实本机 `received_at`，所以历史 feed/network/processing latency 不能被补算。现在已经增加一个前瞻参考 recorder：在实际feed callback入口、解析和排队之前，先记录 UTC wall-clock、`monotonic_ns`、本地 sequence 和 raw payload identity，再解析 event time / symbol / price。

[当前任务](CURRENT_RESEARCH.md) → [接续](CONTINUE_HERE.md) → [recorder状态](research/prospective_reception_recorder_v1/PROGRAM_STATE.json) → [协议](research/prospective_reception_recorder_v1/PROTOCOL.md) → [schema](research/prospective_reception_recorder_v1/SCHEMA.json) → [本地接入说明](research/prospective_reception_recorder_v1/LOCAL_INTEGRATION_HANDOFF.md)。

会话内18项合成测试、编译与独立JSONL validator样例通过。没有读取新行情、没有安装到DataHub、没有实测延迟，也没有启动D6/V20。

## 保留的研究结论

- [V19](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结风险状态识别基线；
- [D2](research/causal_state_delivery_d2/RESULTS.md)：因果双时钟历史工程回放；
- [D3](research/causal_state_utility_d3/RESULTS.md)：三状态增量用途未过实际门槛；
- [D4](research/continuous_risk_utility_d4/RESULTS.md)：连续I/V对指定风险目标有限支持；
- [D5](research/state_degree_consumer_d5/RESULTS.md)：本仓样例消费者工程通过；
- [D5R](research/reception_clock_adjudication_d5r/RESULTS.md)：历史真实接收时钟不可用。

## 数据治理

当前日期已过 `2026-08-21`。根据 [V2数据政策](docs/governance/DATA_USAGE_POLICY_V2.md)，新的两指数市场数据可能进入 pending BlackBox-V1。可以安装recorder并在本地受保护层采集，但不能把新逐行timestamp/price直接上传公开GitHub或拿来研究。后续使用必须遵守明确的数据角色或预注册接口。

`measured_feed_latency_supported=false`; `live_recorder_installed=false`; `blackbox_queried=false`; `production_authority=false`。
