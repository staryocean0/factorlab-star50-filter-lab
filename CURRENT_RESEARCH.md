# 当前任务：前瞻真实 reception recorder 已完成参考实现，待本地安装

更新：2026-09-12。使命不变：把当时可知的K线状态、连续风险程度和适用性信息交给下游研究进程。本仓不开发交易动作。

## 当前权威链

数据治理仍以 `docs/governance/DATA_USAGE_POLICY_V2.md` 与研究桶边界为准。
方向：`docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md`。
当前执行状态：`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `PROTOCOL.md` → `SCHEMA.json` → `EXECUTION_RECEIPT.json`。
历史接收时钟判定保留在 `research/reception_clock_adjudication_d5r/`；D5及更早证据保持封存。

## 当前正式状态

**PROSPECTIVE_RECEPTION_RECORDER_V1_REFERENCE_ACCEPTED_LOCAL_INSTALL_PENDING**。

历史事实仍是 `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`：本地不存在两个指数逐条真实 `received_at`，不能从历史数据反推实测 feed/network/processing latency。

为解决未来证据缺口，本轮已实现一个标准库参考 recorder：在真实行情回调入口、任何解析/排队/归一化之前，先记录本机 UTC wall-clock、`monotonic_ns`、本地 sequence、raw payload SHA/size 和 recorder instance；随后解析市场 event time、symbol、price、source sequence。坏时间戳也保留原 receipt，不允许因解析失败丢掉到达证据。

## 已执行的参考验收

当前会话实际执行：

- 18项合成单元测试：PASS；
- `compileall`：PASS；
- 独立 JSONL validator 的一组 receipt/parsed CLI 样例：PASS。

覆盖 sequence 连续性、wall-clock 回拨、monotonic 不回拨、raw payload hash、解析不改接收时钟、非法 event time 保留、跨 recorder instance 拒绝、append-only JSONL 等。

这只证明参考语义和代码路径，不代表 DataHub 已安装 recorder，也没有读取新行情或生成真实 reception rows。完整仓库 checkout/治理 validator 本轮未在会话环境重跑；治理文件从 GitHub 读取且没有修改。

## 数据治理特别限制

当前日期已晚于 `2026-08-21`。根据 DATA_USAGE_POLICY_V2，新产生的两指数行情可能进入 pending BlackBox-V1。

因此下一步可以在本地安装 recorder，但真实新行必须进入受保护的数据层：不得把逐行 timestamp/price 上传到公开仓库或当前聊天，也不得直接用于调参/诊断。先完成 synthetic/replay 接入测试、开销测试、重启/持久化语义，再开始受保护的前瞻采集。

## 保持原样的研究结论

- V19：冻结风险状态识别基线；
- D2：双时钟历史工程回放；
- D3：`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- D4：连续I/V对15/30/60m未来波动、30m尾部有限支持；
- D5：本仓样例消费者工程验收通过；
- D5R：历史真实接收时钟不存在，实测延迟未验收。

本轮不是D6/V20，也不提高D3/D4证据等级。

## 直接下一步

按 `research/prospective_reception_recorder_v1/LOCAL_INTEGRATION_HANDOFF.md`，在本地 DataHub 的真实feed callback路径中接入 stamp 语义，但第一阶段只用 synthetic/允许的 replay 输入验证位置、顺序、开销、崩溃/重启和存储。通过后再启动受保护的 prospective capture。

在真实、治理允许使用的 reception 数据出现前：`measured_feed_latency_supported=false`，`external_consumer_accepted=false`。

`live_recorder_installed=false`; `true_reception_rows_collected=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
