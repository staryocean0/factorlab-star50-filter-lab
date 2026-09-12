# 当前任务：DataHub reception 云端工程验收已完成；历史冻结研究继续收口

更新：2026-09-12。使命不变：把当时可知的K线状态、连续风险程度和适用性信息交给下游研究进程。本仓不开发交易动作。

## 当前正式状态

**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING**。

历史事实仍是 `D5R_TRUE_RECEPTION_CLOCK_UNAVAILABLE_HISTORICAL_LIVE_LATENCY_UNVERIFIED`：历史行情继续作为项目历史数据直接使用；历史存储没有逐条真实本机 `received_at`，因此不能从旧数据补算实测本机接收延迟。

## 当前权威链

reception主线：`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `CLOUD_ACCEPTANCE_RESULTS.md` → `CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json` → `DATAHUB_ADAPTER_RESULTS.md` → `DATAHUB_INTEGRATION.md` → `PROTOCOL.md` / `SCHEMA.json`。

历史研究收口新增：`docs/research/risk_coordinate_validation_v1/RESULT.md` → `EXECUTION_RECEIPT.json` → 原冻结 `FROZEN_PROTOCOL.md` / `run_validation.py`。

数据治理仍以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准；D5R及D5/D4/D3/D2/V19证据保持封存，不改判。

## DataHub reception 云端验收

GitHub Actions run `34666927078` 已成功完成：

- 从既有 handoff 分支直接恢复用户已上传的 ZIP；
- ZIP 328,518 bytes、SHA256 `866824b8966b237ed8463afd6280186301db95c450876112da77787d5d50fa0d` 校验通过；
- manifest 20个文件逐一 bytes/SHA256 全匹配；
- 完整读取并独立审计 `000688.SH` 4,746行 + `000852.SH` 4,746行，共 **9,492行**；
- 两指数 4,746点 observation-time 网格完全一致；
- 18项 recorder + 23项 adapter = **41项测试全通过**；
- 真实 DataHub `realtime.py` 注入 seam 再验证：`get_security_quotes` line 105 在 `parse_quotes` line 112 之前；
- compile 与 V2 data governance validator 通过；
- evidence artifact id `10288693269`。

当前最早可控采集边界冻结为 **TDX Python SDK return → DataHub parser之前**。它是SDK-return/DataHub-ingress timing，不是wire-level arrival；parser自己的`datetime.now(UTC)`也不是vendor event time或historical received_at。

## 新收口：risk-coordinate Validation v1

历史分支 `research/risk-coordinate-validation-v1-20260909` 并非“未执行”：审计恢复出原成功 run `34303912251`，但其结果从未写回当前权威树。本轮用**完全相同的冻结 protocol/runner blob**重新执行 run `34667783528`，110,911个2024/2025 Validation rows与旧run逐项复现。

正式结论：

**RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE**。

更具体地说：

- state-persistence轴在STAR50/CSI1000 × 2024/2025四个池全部通过，Unsafe对未来15m继续Unsafe概率的增量约 **+47.88pp 至 +51.69pp**；
- M3 `>2` 对 `<=0` 的未来15m RMS effect-size gate 在全部 state/index/year 极端比较中通过，倍率约 **1.83×–2.71×**；
- 但完整 amplitude-axis promotion 在三个 Unsafe 极端格因冻结最小样本门槛失败：STAR50-2025 `>2` n=19<30；CSI1000-2024 `<=0` n=48<100；CSI1000-2025 `>2` n=20<30；
- 因此 frozen full-replication verdict 仍是 `validation_diagnostic_does_not_fully_replicate`；
- 不允许事后降低n门槛、合并年份、移动M3 band或调阈值救结果；
- 不自动启动“M3对D4增量价值”作为救援实验。

原run artifact id `10086030669`；复现run artifact id `10289539266`。无2026、无BlackBox、无PnL、无candidate nomination、无production authority。

## 研究 backlog 审计

为避免继续靠记忆接管旧设计，已对 **112个 `research/*` 分支**做云端扫描。run `34668006394` 全绿：

- 81：RESULT_PRESENT；
- 8：EXECUTED_RESULT_NOT_PERSISTED；
- 1：FROZEN_NOT_SUCCESSFULLY_EXECUTED；
- 2：FROZEN_DESIGN_ONLY；
- 1：EXECUTED_NO_RESULT_MARKER；
- 19：OTHER。

当前优先级不是再发明新版本，而是先审计真正冻结但未成功执行的 `research/session-aware-information-set-bounds-v0617-20260907`，确认其是否仍科学相关、是否已被后续机制取代，再决定是否原样接管执行。

## 当前证据边界

reception线唯一仍不可由云端创造的证据，是未来本机真实feed运行后产生的true-reception observations；它不阻塞其他云端研究。

继续研究时仍遵守停止线：不为V19 accuracy开V20；不因缺日志强开D6；不查询BlackBox逐行细节；不计算PnL；不恢复交易router；不提高production authority。

`historical_market_data_accepted=true`; `cloud_acceptance_supported=true`; `risk_coordinate_full_replication=false`; `risk_coordinate_threshold_retune_allowed=false`; `live_recorder_installed=false`; `true_reception_rows_collected=false`; `measured_feed_latency_supported=false`; `external_consumer_accepted=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
