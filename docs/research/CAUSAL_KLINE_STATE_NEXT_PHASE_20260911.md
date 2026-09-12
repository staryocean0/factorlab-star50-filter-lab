# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至 current-M3 incremental utility 完成、历史 research backlog 全部收口。目标仍是把**当时可知**的K线风险状态、程度、适用性与缺失/时钟语义正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的证据层

- V19/V16–V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：current E15 I/V 对15/30/60m未来波动强度和30m尾部有限支持；这是当前连续程度轴的主要实用证据。
- D5：bounded consumer把状态、连续程度、时间/失效/缺失语义接通。
- D5R + reception recorder/adapter/cloud acceptance：历史真实本机received_at不可恢复；云端工程验收完成；未来真实arrival仍需未来物理feed。
- risk-coordinate frozen Validation：state-persistence轴复制；M3极端effect-size存在，但完整amplitude axis因冻结support门槛未过，不调阈值救结果。
- Activity-degree incremental utility V1：current M3相对D4-style I/V仍有future-RMS信息，但相对等复杂度lagged-M3的current refresh未过1% practical gate，正式 `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`。
- **2026-09-12 historical research backlog closeout**：112个research分支审计标出的12个高召回“未闭环”对象全部已裁决，当前 executable legacy backlog = 0。

## M3 增量结论

V1固定三套同cohort ridge信息集：

- C：历史数值 + previous confirmed state/age + current I/V；
- A：C + current M3固定非线性/状态交互块；
- N：C + 完全同尺寸的lagged-M3块。

只有A同时打赢C和N才允许promotion。

决定性Action `34670357953`：Development先fit/freeze，后读2024–2025 reusable Validation。冻结模型SHA256 `89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`。

相对C，current M3对log future RMS的Validation相对增量：15m +2.1750%、30m +2.8055%、60m +3.6193%。15m A-vs-C单项通过全部门槛；30/60m Development n不足，60m coverage也不足。

相对N，15/30/60m仅 +0.4330% / +0.5793% / +0.1832%，全部低于冻结1% practical gate；15/30m 2023 forward为负，tail所有horizon也未过1% relative与0.0005 absolute Brier门槛。

因此六个endpoint×horizon joint promotion均为false。正确解释是：fine-activity层有持续性风险信息，但没有证据支持把“当前这一根M3刷新”作为D4/D5之外的新实用风险坐标。不能调M3 band、30bp surface、ridge、horizon、bootstrap、sample gate或删掉lagged control来救结果。

## Historical backlog closeout 的含义

closeout 权威：`docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`。

它不是把旧研究都宣布成功，而是把旧分支的实际状态恢复清楚：

- first-shock minute、V7、两个RMR分支没有形成当前可晋升机制；
- V8/V9/V10的有效祖先结果已有后继Validation并被V17/V19吸收；
- V11 2026-09-11是重复frozen design，正式V11已失败，V12又否定简单shock-expiry解释；
- risk-gate-takeover只是handoff/coordinator；
- old highvol-router含route/hold/cost/PnL/Sharpe/MDD，当前风险属性scope明确退役；
- v0.6.17实现层通过，但其frozen scientific replay要求两个必须**事前存在**的identity。严格pre-v0.6.17 Git audit检查70 commits、4,412 text blobs，两个qualifying identity候选均为0，因此正式 `V0617_PRIOR_IDENTITY_IRRECOVERABLE_REPLAY_PERMANENTLY_BLOCKED_UNDER_FROZEN_PROTOCOL`。不得现在重算hash补成旧expected identity。

历史分支不删除，原verdict不重写。`execution-audit` 现强制验证12项closeout ledger，防止以后重新误判为待执行任务。

## 当前推荐的交付对象

研究consumer仍以三层为主：

1. V19状态上下文与转移；
2. D4支持范围内的current连续风险程度 I/V；
3. observation / decision / published / expiry、确认性质和缺失原因。

current M3 **不进入**consumer contract，不进入V19 state machine。M3可作为历史描述性/研究属性保留，但没有新promotion authority。

## Reception并行结论

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`不变。真实DataHub最早可控边界仍是TDX Python SDK return→parser之前；这不是wire-level arrival。历史行情可继续使用，但历史本机实测latency不可恢复。

## 下一阶段治理

当前没有遗留分支需要补跑。只有出现**不同的因果风险机制问题**，并能在看结果前冻结问题、比较器与门槛，才允许新开科学实验。不得为了“继续”而恢复M3参数救援、V19 accuracy优化、旧detector、reversal、router或PnL研究。

如果没有新的合法机制、新的治理允许数据或未来真实reception observations，正确动作是维持/审计当前authority，而不是强造版本号。

停止线：不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复payoff/router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `current_m3_consumer_promotion=false`; `current_m3_refresh_practical_increment_supported=false`; `d4_decision_unchanged=true`; `v19_frozen=true`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
