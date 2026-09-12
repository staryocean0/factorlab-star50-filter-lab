# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至 DataHub reception 云端工程验收完成。目标仍是把当时可知的K线风险状态、程度与适用性正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的证据层

- V19/V16—V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：当前连续 I/V 对15/30/60m未来波动强度和30m尾部有限支持；15/60m尾部未晋升。
- D5：样例消费者把状态、连续程度、发布时间/接收时间/失效和缺失语义接通；接口语义通过，但不证明历史真实本机接收延迟。
- D5R：历史两个指数没有逐条真实本机 `received_at`，历史实测 feed/network/processing latency 无法恢复。
- prospective recorder V1：参考recorder、validator与时钟/重启/失败语义通过。
- DataHub adapter V1：基于真实DataHub源码的SDK-return/parser seam适配层通过。
- DataHub cloud acceptance V1：GitHub Actions 对既有handoff ZIP、完整9,492行历史样本、真实DataHub源码契约、41项测试和V2治理做了可重复验收并全绿。

## reception 工程阶段的正式结论

当前状态：

**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING**。

Action run `34666927078` 是首个决定性云端回执。它完成：

- handoff ZIP exact bytes/SHA验证；
- manifest 20个文件全量哈希核对；
- 000688.SH / 000852.SH 各4,746行、共9,492行完整审计；
- 两指数4,746点observation grid exact match；
- 18 recorder + 23 adapter = 41 tests PASS；
- 真实DataHub `get_security_quotes` line 105 → `parse_quotes` line 112 顺序与依赖注入复核；
- V2 data usage policy validator通过；
- evidence artifact id `10288693269`。

因此不再需要为了这层工程判断向本地模型追历史raw、让本地模型写代码或做wiring测试。

## 当前接受的 reception 边界

真实DataHub源码中最早可控点冻结为：

**TDX Python SDK return → DataHub parser之前**。

该测量若未来启用，应称 `tdx_hq_sdk_return` / DataHub ingress timing，不得称raw TCP/frame arrival。parser自身生成的`datetime.now(UTC)`只是parser-time metadata，不是vendor event time，也不能补成historical received_at。

GitHub runner上3000次两quote synthetic wrapper测试的描述性增量：median 59.296µs、p95 95.610µs、p99 109.112µs。它不构成live/production性能门槛。

## 数据治理与未来真实证据

当前日期晚于 `2026-08-21`。未来新subject逐行行情/接收时间可能进入 pending BlackBox-V1。

云端Actions能够验证代码、历史样本和契约，但不能制造“某条未来行情何时真正到达用户本机”这一物理事实。因此 reception 线下一次证据升级只能来自未来真实运行后产生、且治理允许使用的true-reception observations。

真实新行必须先在受保护数据层保存；不能因为recorder工程已通过就直接公开逐行数据、做BlackBox详细诊断或调参。

## 现在正确的研究接口

仍交付三个轴：
1. V19状态上下文与转移；
2. 当前连续风险程度 I/V 与适用的历史对照；
3. observation / decision / published / expiry、确认性质和缺失原因。

历史没有真实reception log时，接收侧继续标记`owner_realtime_assumption` / `unmeasured_reception`。云端工程验收不会改变这一事实。

## 当前停止线与可继续研究范围

reception工程阶段在云端已做到现有数据和权限能够支持的边界。不要以“还没实测received_at”为理由重复造adapter版本，也不要把这个物理数据缺口变成用户的工程待办。

可以继续推进**不依赖真实reception clock**的云端科学研究；新题必须来自当前证据链中的明确未决科学问题，并服从Dev/Validation/BlackBox治理。仍然：

- 不为V19 accuracy开V20；
- 不因缺日志强开D6；
- 不恢复payoff/router；
- 不查询BlackBox逐行细节；
- 不计算PnL；
- 不提高production authority。

当前权威链：`CURRENT_RESEARCH.md` → 本文 → `research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `CLOUD_ACCEPTANCE_RESULTS.md` / `CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json` → D5R → 原D5/D4/D3/D2/V19证据。

`cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `live_recorder_installed=false`; `true_reception_rows_collected=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
