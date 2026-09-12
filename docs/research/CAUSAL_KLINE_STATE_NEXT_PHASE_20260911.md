# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至 D5R 接收时钟审计。目标仍是把当时可知的K线风险状态、程度与适用性正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的证据层

- V19/V16—V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：当前连续 I/V 对15/30/60m未来波动强度和30m尾部有限支持；15/60m尾部未晋升。
- D5：本仓样例消费者把状态、连续程度、发布时间/接收时间/失效和缺失语义接通；它证明接口语义，不证明真实本机接收延迟。

## D5R：历史真实 reception clock 不存在

本地只读检索结果已上传到 commit `09cb66a86be6a9bef3a91b52af34b747f812b407` 与 Release `star50-true-reception-raw-20260912`。结论：`NO_TRUE_RECEPTION_TIMESTAMP_AVAILABLE`，quote rows=0。

DataHub recording 相关表为空，`lake/recording` / `ticks.parquet` 未物化。已有 `observation_datetime` / `observation_time` 是市场或重建观察时钟；`available_at` 是历史/派生可得口径；`ingested_at` 是batch导入时钟。它们都不能变成真实本机 `received_at`。

因此当前权威必须明确：

**D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED**。

这不推翻 V19/D2-D5，但阻止把 owner_realtime_assumption、零延迟样例或2秒合成样例描述为实测 feed/network/processing latency。

## 现在正确的研究接口

仍交付三个轴：

1. V19状态上下文与转移；
2. 当前连续风险程度 I/V 与适用的历史对照；
3. observation / decision / published / expiry、确认性质和缺失原因。

当没有真实 reception log 时，接收侧身份只能标记为 `owner_realtime_assumption` / `unmeasured_reception`。不得把缺失补正常，不得把合成 received_at 写成真实记录。

## 真实接收时钟的唯一后续路径

历史数据不能反推 reception。若未来确有实际接入需求，只能前瞻采集真实 recorder 记录。最小字段：symbol、source/vendor/channel、market/event timestamp、timezone-aware local receive wall clock、local monotonic receive timestamp/sequence、price、source sequence/row identity、trading_day、recorder/version identity。

未来采集必须在接收瞬间持久化，不能事后从文件 mtime、batch import 或 observation time构造。采集本身属于基础设施观测，不自动授予生产或交易权限。

## 当前停止线

没有真实 reception 数据时，本仓进入冻结维护；不为缺日志启动 D6/V20，不重跑 V19/D2-D5，不恢复 payoff/router，也不查询 BlackBox/PnL。

只有真实前瞻 reception 记录出现后，才重新打开“实测到达时钟、实际 E15 可用性与真实延迟”的验收问题。

当前权威链：`CURRENT_RESEARCH.md` → 本文 → `research/reception_clock_adjudication_d5r/PROGRAM_STATE.json` → `RESULTS.md` / `DECISIVE_RECEIPT.json` → 本地负结果包 → 原 D5/D4/D3/D2/V19 证据。

`true_reception_timestamp_available=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
