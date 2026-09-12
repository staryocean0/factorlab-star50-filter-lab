# 当前任务：当前 M3 refresh 增量效用已完成并关闭

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前两个正式状态

最新科学决定：

**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

并行 reception 工程状态保持：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

两者互不覆盖。前者回答“当前细尺度活动 surprise 是否值得在 D4 风格 I/V 之外作为新 refresh 坐标晋升”；后者说明 DataHub recorder/adapter 云端工程已验收，但未来真实本机 arrival 仍只能由未来物理 feed 产生。

## 当前权威链

科学主链：

`research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json` / `evidence/SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py`。

其前置证据仍包括：

- `docs/research/risk_coordinate_validation_v1/RESULT.md`：结构性 risk-coordinate Validation 不完全复制、禁止事后调门槛；
- D4：当前 I/V 对指定 future-risk endpoints 有有限、分目标支持；
- D3：离散状态增量效用未达到原实际门槛；
- D2/V19：因果状态事件与冻结状态机。

reception 并行链：`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `CLOUD_ACCEPTANCE_RESULTS.md` → `CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json` → D5R。

治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准。

## 最新科学结果：Activity-degree incremental utility V1

问题不是“再测一次 M3”，而是：在继承的 `pre5m_range < 30bp` 表面上，同一 E15 决策点的 current M3 是否：

1. 在历史 + previous-state/age + 当前 I/V 的 **C** 信息集之外仍有实际增量；且
2. 能打赢完全等复杂度、只把 current M3 换成上一根 same-half-session M3 的 **N** 对照。

A = C + current M3；N = C + lagged M3。A/N 的新增列数、非线性、状态交互和 ridge 规则完全相同。每个 endpoint/horizon 只有 **A vs C 与 A vs N 同时过门槛** 才能晋升。

决定性 Action run `34670357953` 两阶段全绿：Development 先 fit/freeze，随后才读 2024–2025 reusable Validation。冻结模型 SHA256：

`89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`。

### 能支持什么

相对 C，current M3 在未来波动强度上确有额外信息：

- 15m log future RMS：+2.1750%，个别 `A vs C` 比较全部 gate 通过；
- 30m：+2.8055%，但 Development n=19,365 < 20,000；
- 60m：+3.6193%，但 Development n=11,779 < 20,000，Validation coverage 也仅 92.4378%。

因此不能说“M3 在 I/V 之外没有信息”。

### 为什么仍然不晋升 current refresh

相对等复杂度 lagged-M3 N，current refresh 的 log-RMS 相对改进只有：

- 15m：+0.4330%，且 2023 forward gain 为负；
- 30m：+0.5793%，且 forward 为负、Development 样本不足；
- 60m：+0.1832%，同时样本/coverage 等门槛失败。

全部低于冻结的 **1% practical gate**。15/30/60m tail 也均未过 1% relative 与 `0.0005` absolute Brier 门槛。

所以正式状态是 `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`：**M3 有信息，但没有证明“现在刷新一次 M3”相对上一根 M3 有足够大的实际新增价值。**

禁止通过移动 M3 band、30bp surface、ridge、horizon、block、最小样本门槛，或删除 lagged-M3 对照来救结果。当前 M3 不进入 D5 consumer、不进入 V19 state machine。

Validation coverage 已复核：15m 95.9036%、30m 95.1844%、60m 92.4378%；门槛执行与结果 JSON 一致。

## 数值复现与证据固化

完整 Validation artifact 已原字节写入 `research/activity_degree_incremental_utility_v1/evidence/`。Validation artifact id `10290917834`，ZIP SHA256 `a734a0083c9d197188591fa548668cdbc3f2a86df00b783f68f41acfecf69940`。

重复 Development fit 的 JSON SHA 不同，但专门 audit run `34670797290` 证明输入 SHA、feature schema、样本数完全相同，最大系数差仅 `8.16e-15`，全部数值差 < `1e-10`。决定性 Validation 始终使用**同一 run 内先冻结的精确模型字节**，freeze-before-Validation 未破坏。

## 保持不变的历史结论

- `RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE` 不变；
- V19 不为 accuracy 再开 V20；
- D3 negative practical decision 不变；
- D4 endpoint-limited I/V support 不变；
- D5 bounded consumer contract 不变；
- D5R 仍是历史真实本机 `received_at` 不可恢复；
- reception cloud acceptance 仍等待未来治理允许的真实 reception observations。

## 下一步

先完成历史 research backlog 的**证据/状态收口**，把“Action 已成功但结果未持久化”“已被后续正式机制取代”“因原 preregistration 前置证据缺失而不可执行”三类彻底分开。只有出现一个**不同的因果机制问题**，才新开科学实验；不得把新题变成对 current-M3 refresh 失败的参数救援。

仍然：不读 2026 受保护逐行数据，不查 BlackBox，不算 PnL，不恢复 router，不开 D6/V20，不提高 production authority。

`current_m3_consumer_promotion=false`; `m3_contains_incremental_information_vs_C=true`; `current_m3_refresh_practical_increment_supported=false`; `validation_reused=true`; `fresh_oos=false`; `cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
