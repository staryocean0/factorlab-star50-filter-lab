# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至 current-M3 incremental utility V1 完成。目标仍是把**当时可知**的K线风险状态、程度、适用性与缺失/时钟语义正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的证据层

- V19/V16–V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：current E15 I/V 对15/30/60m未来波动强度和30m尾部有限支持；这是当前连续程度轴的主要实用证据。
- D5：bounded consumer把状态、连续程度、时间/失效/缺失语义接通。
- D5R + reception recorder/adapter/cloud acceptance：历史真实本机received_at不可恢复；云端工程验收完成；未来真实arrival仍需未来物理feed。
- risk-coordinate frozen Validation：state-persistence轴复制；M3极端effect-size存在，但完整amplitude axis因冻结support门槛未过，不调阈值救结果。
- **Activity-degree incremental utility V1**：直接检验 current M3 在 D4-style I/V 之外、并相对等复杂度 lagged-M3 的实际增量；正式判定 `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`。

## 为什么 M3 增量实验是必要且已经回答完的问题

之前的M3工作只说明细尺度活动surprise与未来RMS存在Development/结构性关系；risk-coordinate Validation只说明幅度轴与状态持续轴结构上可分。它们没有回答：**如果current I/V已经知道，current M3刷新本身还有没有足够大的新增信息？**

V1固定三套同cohort ridge信息集：

- C：历史数值 + previous confirmed state/age + current I/V；
- A：C + current M3固定非线性/状态交互块；
- N：C + 完全同尺寸的lagged-M3块。

只有A同时打赢C和N才允许promotion。

## 决定性结果

Action run `34670357953`：Development先fit/freeze，后读2024–2025 reusable Validation。冻结模型SHA256 `89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`。

### M3不是“没信息”

相对C，current M3对log future RMS有明显正增量：

- 15m +2.1750%，个别A-vs-C比较全部门槛通过；
- 30m +2.8055%；
- 60m +3.6193%。

但30/60m的Development n分别仅19,365/11,779，不能通过冻结support gate；60m Validation coverage也仅92.4378%。

### current refresh 没有证明足够实用

相对等复杂度N，log-RMS相对改进只有：

- 15m +0.4330%；
- 30m +0.5793%；
- 60m +0.1832%。

全部低于冻结1% practical gate。15/30m的2023 forward A-vs-N gain为负；tail所有horizon也未过1% relative与0.0005 absolute Brier门槛。

因此六个endpoint×horizon joint promotion均为false，正式决定：

**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

正确解释是：fine-activity层有持续性风险信息，但没有证据支持把“当前这一根M3刷新”作为D4/D5之外的新实用风险坐标。不能通过调M3 band、30bp surface、ridge、horizon、bootstrap、sample gate或删掉lagged control来救结果。

## 当前推荐的交付对象仍是什么

研究consumer仍以三层为主：

1. V19状态上下文与转移；
2. D4支持范围内的current连续风险程度 I/V；
3. observation / decision / published / expiry、确认性质和缺失原因。

current M3 **不进入**consumer contract，不进入V19 state machine。M3可作为历史描述性/研究属性保留，但没有新promotion authority。

## Reception并行结论

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`不变。真实DataHub最早可控边界仍是TDX Python SDK return→parser之前；这不是wire-level arrival。历史行情可继续使用，但历史本机实测latency不可恢复。

## 下一阶段治理

先清理历史research backlog：把“Action已成功但结果没持久化”“被后续机制取代”“原frozen preregistration前置身份缺失而不可执行”分开并正式收口。

只有出现**不同的因果机制问题**，而不是current-M3失败的参数变体，才允许新开科学实验。

停止线：不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复payoff/router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`current_m3_consumer_promotion=false`; `current_m3_refresh_practical_increment_supported=false`; `d4_decision_unchanged=true`; `v19_frozen=true`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
