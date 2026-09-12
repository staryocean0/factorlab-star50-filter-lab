# 当前任务：DataHub reception 云端工程验收已完成

更新：2026-09-12。使命不变：把当时可知的K线状态、连续风险程度和适用性信息交给下游研究进程。本仓不开发交易动作。

## 当前正式状态

**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING**。

历史事实仍是 `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`：历史行情继续作为项目历史数据直接使用；历史存储没有逐条真实本机 `received_at`，因此不能从旧数据补算实测本机接收延迟。

## 当前权威链

`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `CLOUD_ACCEPTANCE_RESULTS.md` → `CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json` → `DATAHUB_ADAPTER_RESULTS.md` → `DATAHUB_INTEGRATION.md` → `PROTOCOL.md` / `SCHEMA.json`。

数据治理仍以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准；D5R及D5/D4/D3/D2/V19证据保持封存，不改判。

## 云端实际完成的验收

GitHub Actions run `34666927078` 已成功完成：

- 从既有 handoff 分支直接恢复用户已上传的 ZIP；
- ZIP 328,518 bytes、SHA256 `866824b8966b237ed8463afd6280186301db95c450876112da77787d5d50fa0d` 校验通过；
- manifest 20个文件逐一 bytes/SHA256 全匹配；
- 完整读取并独立审计 `000688.SH` 4,746行 + `000852.SH` 4,746行，共 **9,492行**；
- 两指数 4,746点 observation-time 网格完全一致；
- symbol/day/source/source_file/row_index/archive/dataset-version/价格与时间顺序检查全部通过；
- 无伪造 reception 字段；
- 真实 DataHub `realtime.py` 的注入 seam 通过 AST 再验证：`get_security_quotes` line 105 在 `parse_quotes` line 112 之前；
- 18项 recorder + 23项 adapter = **41项测试全通过**；
- compile 通过；
- V2 data governance validator: OK；
- 证据 artifact id `10288693269`，artifact ZIP SHA256 `627f7fb8e20f96133baa2691a3fcaaaf7d0fbc0dba6481645b516550f17b0ded`。

因此，之前“云端无法完整执行9,492行独立数值检查”的缺口已经关闭。

## DataHub 接收边界

当前真实源码能支持的最早 DataHub 控制边界冻结为：

**TDX Python SDK `get_security_quotes()` 返回 → DataHub `parse_quotes()` 之前**。

它是 `tdx_hq_sdk_return` / DataHub ingress timing，不是 raw TCP/frame arrival。DataHub parser 自己生成的 `datetime.now(UTC)` 仍只是 parser-time metadata，不是 vendor event time，也不是历史 `received_at`。

## 性能证据边界

Action 在 GitHub runner 上做了3,000次、每次2 quote的纯合成 wrapper 开销测试：增量 median 59,296 ns、p95 95,610 ns、p99 109,112 ns；6,000 receipt 与6,000 parsed records全部完成，pending batch=0。

这只是 Python wrapper 的云端描述性开销，不是本地DataHub性能、feed/network latency或生产门槛。

## 现在真正还缺的是什么

云端可执行的 recorder/adapter/schema/full-sample/governance 工程验收已经完成。当前缺口不再是“让本地模型做 wiring/测试”，而是一个未来才可能存在的数据证据：**真实本机 feed 运行后产生的 prospective reception observations**。

GitHub Actions不能制造真实本机到达时钟。因此在没有治理允许使用的未来 true-reception 数据之前：

- 不启动D6/V20；
- 不把合成时钟冒充实测延迟；
- 不查询BlackBox逐行细节；
- 不计算PnL；
- 不提高production authority。

与此同时，可以继续推进**不依赖真实 reception clock 的云端研究线**；是否启动具体新题由已有证据和治理决定，不因“缺日志”强造新模型。

`historical_market_data_accepted=true`; `cloud_acceptance_supported=true`; `full_normalized_sample_numerical_replay_performed=true`; `live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
