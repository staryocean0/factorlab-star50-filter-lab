# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至 DataHub reception 云端工程验收与历史 frozen risk-coordinate Validation 收口。目标仍是把当时可知的K线风险状态、程度与适用性正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的证据层

- V19/V16—V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：当前连续 I/V 对15/30/60m未来波动强度和30m尾部有限支持；15/60m尾部未晋升。
- D5：bounded consumer把状态、连续程度、发布时间/接收时间/失效和缺失语义接通。
- D5R：历史两个指数没有逐条真实本机 `received_at`，历史实测feed/network/processing latency无法恢复；历史行情本身继续直接接受。
- prospective recorder / DataHub adapter / cloud acceptance：云端工程验收完成，完整9,492行handoff与41项测试已固化。
- risk-coordinate Validation v1：恢复了2026-09-09已成功执行但未进入权威树的冻结Validation，并用原blob复现；正式判定“不完全复制、禁止事后调阈值救结果”。

## Reception工程阶段结论

当前主状态：**DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING**。

Action `34666927078`完成handoff ZIP exact bytes/SHA验证、20个manifest文件全量哈希核对、两指数共9,492行完整审计、4,746点跨指数observation grid exact match、41 tests、真实DataHub seam与V2治理validator。

当前接受的最早可控采集边界冻结为：**TDX Python SDK return → DataHub parser之前**。它是SDK-return/DataHub-ingress timing，不是raw TCP/frame arrival；parser自己的`datetime.now(UTC)`不能补成vendor event time或historical received_at。

未来真实本机reception observations仍是物理数据缺口，但不阻塞其他云端研究。

## Risk-coordinate frozen Validation 收口

历史原run：`34303912251`。原结果没有进入current authority tree。

本轮恢复原冻结protocol/runner blob并执行复现run：`34667783528`。两次执行在 **110,911个2024/2025 Validation rows**、全部cell counts、metrics和判定上逐项一致。

正式结论：

**RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE**。

### 稳定复制的部分

state-persistence轴在四个index×year池全部通过：当前Unsafe相对于NonUnsafe，未来15m任一Unsafe概率高约：

- STAR50 2024：+50.4886pp；
- STAR50 2025：+51.6869pp；
- CSI1000 2024：+47.8773pp；
- CSI1000 2025：+48.7915pp。

M3 `>2` 对 `<=0` 的未来15m RMS effect-size gate在全部state/index/year极端比较中也通过，倍率约1.83×–2.71×。

### 未通过的冻结晋升条件

完整M3 amplitude-axis promotion要求每个极端格同时过预注册最小样本量。三个Unsafe格失败：

- STAR50 2025，M3>2：n=19 < 30；
- CSI1000 2024，M3<=0：n=48 < 100；
- CSI1000 2025，M3>2：n=20 < 30。

因此正式frozen verdict仍是 `validation_diagnostic_does_not_fully_replicate`。

不得事后：降低n门槛、合并年份、移动M3 bands、调整1.5 vol-ratio阈值，或把新的增量实验当成对这项失败的“救援”。如果未来重新研究fine-activity，必须是科学上不同且独立预注册的问题。

无2026、无BlackBox、无PnL、无candidate nomination、无production authority。

## 历史研究backlog治理

Action `34668006394` 已扫描112个 `research/*` 分支，把“过去设计了但可能没完成”转成可审计队列：81已有结果；8个Action成功但结果未持久化；1个冻结但未成功执行；2个只有冻结设计；其余为其他状态。

后续优先处理**冻结但未成功执行**或**已执行但未进入权威链**的项目，不凭记忆重新设计版本。

当前首要审计对象：`research/session-aware-information-set-bounds-v0617-20260907`。只有确认其问题仍未被后续证据覆盖，才按原冻结协议执行；否则记录为已被取代并关闭。

## 当前停止线

- 不为V19 accuracy开V20；
- 不因缺reception日志强开D6；
- 不调M3门槛救失败的full-replication test；
- 不恢复payoff/router；
- 不查询BlackBox逐行细节；
- 不计算PnL；
- 不提高production authority。

当前权威链：`CURRENT_RESEARCH.md` → 本文 → reception云端验收链 → `docs/research/risk_coordinate_validation_v1/RESULT.md` / `EXECUTION_RECEIPT.json` → D5R → 原D5/D4/D3/D2/V19证据。

`risk_coordinate_full_replication=false`; `risk_coordinate_threshold_retune_allowed=false`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
