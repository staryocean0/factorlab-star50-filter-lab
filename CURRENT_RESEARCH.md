# 当前任务：DataHub reception adapter 离线契约已通过，待本地 wiring

更新：2026-09-12。使命不变：把当时可知的K线状态、连续风险程度和适用性信息交给下游研究进程。本仓不开发交易动作。

## 当前权威链

数据治理仍以 `docs/governance/DATA_USAGE_POLICY_V2.md` 与研究桶边界为准。
方向：`docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md`。
当前执行状态：`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `DATAHUB_ADAPTER_RESULTS.md` → `DATAHUB_INTEGRATION.md` → `DATAHUB_ADAPTER_EXECUTION_RECEIPT.json` → 原 `PROTOCOL.md` / `SCHEMA.json`。
历史接收时钟判定保留在 `research/reception_clock_adjudication_d5r/`；D5及更早证据保持封存。

## 当前正式状态

**DATAHUB_RECEPTION_ADAPTER_V1_OFFLINE_CONTRACT_ACCEPTED_LOCAL_WIRING_PENDING**。

历史事实仍是 `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`：历史行情本身继续作为项目历史数据使用，但两个指数没有逐条真实本机 `received_at`，所以不能把历史 observation/available/batch 时间冒充实测接收延迟。

## DataHub 真实接口已经定位

用户交付的 DataHub 源码与 2025-06-11 历史 normalized sample 已直接用于本轮接口审计。历史数据不再要求更底层 vendor 字节证明。

真实源码显示：`TdxRemoteRealtimeAdapter` 本来就对 `hq_api` 与 `quotes_parser` 做依赖注入；`TdxHqApiAdapter.get_security_quotes()` 在 Python SDK `api.get_security_quotes(...)` 返回后给出 list，随后才调用 `quotes_parser.parse_quotes(raw_quotes)`。

因此当前源码可观测到的最早 DataHub 控制边界冻结为：

**TDX Python SDK return → DataHub quote parser**。

这不是 TCP/wire 到达时间。未来若在此测量，名称必须是 `tdx_hq_sdk_return` / DataHub ingress timing，包含 SDK 返回之前的网络/SDK处理时间。

现有 DataHub TDX parser 会自己生成 `timestamp=datetime.now(UTC)`；它只是 parser-time metadata，不是 vendor event time，也不是 `received_at`。

## 已实现并实际测试

新增 `datahub_adapter.py`：

- `TdxReceptionHqTap` 包装既有 HqApiPort；SDK返回后、parser前立即生成不可变 receipt；
- `ReceptionAwareQuotesParser` 包装既有 parser，并把解析结果与原 receipt 绑定；
- 返回的 SDK payload 对象与 DataHub parser 输出均保持原对象/原内容；
- SDK对象用确定性 canonical JSON 做 identity/hash，明确不是 wire-frame hash；
- payload 在 capture 与 parser 之间被改写时拒绝；
- parser 报错时 receipt 仍保留；
- parser 改变 cardinality 时拒绝并记录；
- source sequence 只有原 SDK 行真实存在时才保留；
- 当前 parser 生成的 now(UTC) 不会被升级成 market event time。

当前会话实际执行 **23项适配层测试全部通过**，adapter/tests compile 通过。原 prospective recorder 的18项测试证据保持不变。

## 历史 sample 的正确用途

交接 commit `bc84b65ba0510d164dbc90a01d3a98692982fc97` 的 manifest 明确给出：

- `000688.SH`：4,746行；
- `000852.SH`：4,746行；
- 日期：2025-06-11；
- `NORMALIZED_SOURCE_ROWS`；
- source：`baidu_netdisk_market_index_transaction_3s`。

这些行是有效历史行情，用于 DataHub schema / 字段语义对照；它们不含 historical `received_at`，这不影响历史行情研究本身。当前云端连接器没有把两个多MB JSONL完整落到本地文件系统，所以本轮不冒称又做了一次9,492行独立数值回放；也不需要以此作为接受历史数据的前提。

## 下一实际动作

把已经测试的两个 wrapper 挂到本地 DataHub 现有 `hq_api` / `quotes_parser` 注入点。第一阶段只用 synthetic 或治理允许的 replay/input，核验：真实 wiring、receipt/parsed 持久化、进程重启 instance、错误/重复消息、性能开销和失败恢复。

通过后才启动受保护的 prospective capture。当前已经晚于2026-08-21，新采两指数逐行行情/接收时间可能属于 pending BlackBox-V1，必须先保留在受保护本地数据层，不能因 recorder 已实现就直接上传逐行数据或用于诊断调参。

## 保持原样的研究结论

V19、D2、D3、D4、D5、D5R均不改判。本轮不是D6/V20，不提高D3/D4预测证据等级，不计算PnL，不接交易router或生产registry。

`historical_market_data_accepted=true`; `live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
