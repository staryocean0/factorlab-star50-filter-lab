# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至前瞻 reception recorder 参考实现。目标仍是把当时可知的K线风险状态、程度与适用性正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的证据层

- V19/V16—V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：当前连续 I/V 对15/30/60m未来波动强度和30m尾部有限支持；15/60m尾部未晋升。
- D5：本仓样例消费者把状态、连续程度、发布时间/接收时间/失效和缺失语义接通；它证明接口语义，不证明真实本机接收延迟。
- D5R：历史两个指数没有逐条真实本机 `received_at`，历史实测 feed/network/processing latency 无法恢复。

## 前瞻 reception recorder V1

既然历史接收时钟不存在，唯一合理的数据路径是从未来开始真实采集。本轮已经完成参考实现和冻结协议，但尚未安装到 DataHub/live feed。

核心要求：在真实feed callback入口、任何解析/排队/归一化之前，先保存本机UTC wall-clock、monotonic_ns、本地sequence和raw payload identity；随后才解释market/event time、symbol、price和source sequence。

wall-clock允许因NTP/系统调整回拨，monotonic用于同一recorder实例内的顺序和时差；进程重启必须新建recorder_instance_id，不跨实例偷接monotonic。解析失败不能删除原始receipt，重复源消息不在recorder层去重。

参考代码和validator位于 `research/prospective_reception_recorder_v1/`。会话内18项合成测试、编译和一组独立JSONL validator CLI样例通过。没有新行情读取、没有实测延迟、没有DataHub安装或生产授权。

## 数据治理：安装可以先做，真实新行必须隔离

当前日期已经晚于 `2026-08-21`。按照 `DATA_USAGE_POLICY_V2.md`，新的两指数观测可能进入 pending BlackBox-V1。

因此可以先把recorder代码接入本地callback并用synthetic/允许replay测试，但真实新行情一旦开始采集，逐行timestamp/price必须留在受保护本地数据层，不能上传公开GitHub/当前聊天，也不能直接用于研究调参或详细诊断。后续使用必须经过明确数据角色或预注册聚合接口。

这一区分很重要：**建立测量能力不等于获得读取新市场数据的权限。**

## 现在正确的研究接口

仍交付三个轴：
1. V19状态上下文与转移；
2. 当前连续风险程度 I/V 与适用的历史对照；
3. observation / decision / published / expiry、确认性质和缺失原因。

当没有真实 reception log 时，接收侧只能标记 `owner_realtime_assumption` / `unmeasured_reception`。未来只有 recorder 真正产生、并在治理允许下使用的记录，才能升级 measured reception 证据。

## 当前停止线与下一动作

当前状态：`PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING`。

下一步不是新模型，而是在本地 DataHub 的真实 feed callback 路径中按 `LOCAL_INTEGRATION_HANDOFF.md` 接入 recorder；第一阶段只做 synthetic/允许replay、开销、重启和持久化验收。通过后才启动受保护的前瞻采集。

不因缺历史日志启动 D6/V20，不重跑 V19/D2-D5，不恢复 payoff/router，不查询 BlackBox 细节，不计算PnL。

当前权威链：`CURRENT_RESEARCH.md` → 本文 → `research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `PROTOCOL.md` / `SCHEMA.json` / `EXECUTION_RECEIPT.json` → D5R → 原D5/D4/D3/D2/V19证据。

`measured_feed_latency_supported=false`; `live_recorder_installed=false`; `true_reception_rows_collected=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
