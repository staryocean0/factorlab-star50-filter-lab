# 当前任务：current M3 refresh 已关闭，历史 research backlog 已清零

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

并行 reception 工程状态：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

历史研究队列状态：

**`RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`**。

三者互不覆盖。M3 决定回答新坐标是否值得晋升；reception 状态回答本机真实 arrival 证据边界；backlog closeout 只裁决旧分支是否仍是待执行任务，不创造新科学候选。

## 当前权威链

科学主链：

`research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json` / `evidence/SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py`。

历史 backlog 权威：

`docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json` → `RESEARCH_BACKLOG_CLOSEOUT_20260912.md` → `scripts/validate_research_backlog_closeout.py`。

v0.6.17 特殊关闭：

`docs/research/session_aware_information_set_bounds_v0617/CLOSEOUT_RECEIPT_20260912.json` → `CLOSEOUT_20260912.md`。

reception 并行链：

`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `CLOUD_ACCEPTANCE_RESULTS.md` → `CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json` → D5R。

治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准。

## 最新科学结果：Activity-degree incremental utility V1

问题是在继承的 `pre5m_range < 30bp` 表面上，同一 E15 决策点的 current M3 是否：

1. 在历史 + previous-state/age + 当前 I/V 的 **C** 信息集之外仍有实际增量；且
2. 能打赢完全等复杂度、只把 current M3 换成上一根 same-half-session M3 的 **N** 对照。

A = C + current M3；N = C + lagged M3。每个 endpoint/horizon 只有 **A vs C 与 A vs N 同时过门槛** 才能晋升。

决定性 Action run `34670357953` 两阶段全绿：Development 先 fit/freeze，随后才读 2024–2025 reusable Validation。冻结模型 SHA256：

`89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`。

相对 C，current M3 在未来波动强度上确有额外信息：

- 15m log future RMS：+2.1750%，`A vs C` 单项全部 gate 通过；
- 30m：+2.8055%，但 Development n=19,365 < 20,000；
- 60m：+3.6193%，但 Development n=11,779 < 20,000，Validation coverage 92.4378% < 95%。

因此不能说“M3 在 I/V 之外没有信息”。

但相对等复杂度 lagged-M3 N，current refresh 的 log-RMS 相对改进只有：

- 15m：+0.4330%，且 2023 forward gain 为负；
- 30m：+0.5793%，且 forward 为负、Development 样本不足；
- 60m：+0.1832%，同时样本/coverage 等门槛失败。

全部低于冻结的 **1% practical gate**。15/30/60m tail 也均未过 1% relative 与 `0.0005` absolute Brier 门槛。

所以正式状态是 `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`：**M3 有信息，但没有证明“现在刷新一次 M3”相对上一根 M3 有足够大的实际新增价值。**

禁止移动 M3 band、30bp surface、ridge、horizon、block、最小样本门槛，或删除 lagged-M3 对照来救结果。current M3 不进入 D5 consumer、不进入 V19 state machine。

Validation coverage：15m 95.9036%、30m 95.1844%、60m 92.4378%。完整 Validation artifact 已原字节写入 `research/activity_degree_incremental_utility_v1/evidence/`；artifact `10290917834`，ZIP SHA256 `a734a0083c9d197188591fa548668cdbc3f2a86df00b783f68f41acfecf69940`。

重复 Development fit 的 JSON SHA 不同，但 audit run `34670797290` 证明输入 SHA、feature schema、样本数完全相同，最大系数差 `8.16e-15`，全部数值差 < `1e-10`；决定性 Validation 使用同一 run 内先冻结的精确模型字节。

## 历史 research backlog 已正式关闭

112 个 `research/*` 分支的审计曾标出 12 个高召回“未闭环”分支：8 个 Action 成功但没有结果 marker，1 个 frozen 后未成功科学执行，2 个 frozen design only，1 个 executed no result marker。

逐项回读原 Action 与后继机制后，**12/12 都已裁决，当前 executable backlog = 0**：

- first-shock minute Development：完成但不晋升，后续 seconds/support/state 链取代；
- V7：60s detector recall 77.21% 未过 90%，不具 Validation 资格；
- V8/V9/V10 Development：各自完成，V8/V10 后继 Validation 存在，最终被 V17/V19 authority 吸收；
- V10 Validation：2024–25 可用子集通过，但没有查询 2026；后续 V17/V19 取代当前调度权；
- 两个 RMR reversal 分支：均正式 `broad_signal_source_not_established`，且 reversal/direction 本就不属于当前风险属性 scope；
- v0.6.17：实现测试通过，但原 frozen protocol 要求的事前 349,923-row source identity 与 v0.6.15 leg-universe identity 在严格 pre-v0.6.17 Git 历史中均为 0，故永久 fail-closed，不能事后补 hash；
- V11 2026-09-11：重复 frozen design；2026-09-10 的正式 V11 已因 60m state-rank crossover 判 `validation_eligible=false`，V12 又否定简单 shock-expiry 解释；
- risk-gate-takeover：交接/协调容器，不是缺失 standalone experiment，已由 V16–V19/D2–D5链取代；
- old highvol-router：历史 Development audit 虽写 `router_freeze_eligible=true`，但它包含 route/hold/cost/PnL/Sharpe/MDD，属于当前 scope 明确退役对象，不恢复。

完整逐项 run/job/artifact/verdict 见 `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`。历史分支全部保留，原 verdict 不重写；只是明确它们不再是当前待执行任务。

v0.6.17 的严格身份审计 run `34670259559`：70 commits / 4,412 text blobs；qualifying source identity=0，v0.6.15 leg identity=0，unreachable object census empty。正式状态：

**`V0617_PRIOR_IDENTITY_IRRECOVERABLE_REPLAY_PERMANENTLY_BLOCKED_UNDER_FROZEN_PROTOCOL`**。

这不是负的市场科学结果，而是原 preregistration 自己要求的 identity 前置条件无法恢复。

## 保持不变的历史结论

- `RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE` 不变；
- V19 不为 accuracy 再开 V20；
- D3 negative practical decision 不变；
- D4 endpoint-limited I/V support 不变；
- D5 bounded consumer contract 不变；
- D5R 仍是历史真实本机 `received_at` 不可恢复；
- reception cloud acceptance 仍等待未来治理允许的真实 reception observations。

## 下一步

**没有遗留分支需要继续补跑。**

只有出现一个与现有 V19/D4/M3 证据不同的、可事前冻结的**独立因果风险机制问题**，才新开科学实验；不能把新题变成 M3、V19 或旧 detector/router 的参数救援。

在没有这种独立机制、没有新的治理允许数据、也没有未来真实 reception observations 时，正确动作是维持/审计当前 authority，而不是为了“继续”强造新版本。

仍然：不读 2026 受保护逐行数据，不查 BlackBox，不算 PnL，不恢复 router，不开 D6/V20，不提高 production authority。

`historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `current_m3_consumer_promotion=false`; `m3_contains_incremental_information_vs_C=true`; `current_m3_refresh_practical_increment_supported=false`; `validation_reused=true`; `fresh_oos=false`; `cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
