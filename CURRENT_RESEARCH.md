# 当前任务：跨指数 current-degree 增量路径已关闭

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

上一科学决定仍保留：

**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

并行 reception 工程状态：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

历史研究队列：

**`RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`**。

这些状态互不覆盖。

## 当前权威链

最新科学主链：

`research/cross_index_degree_transfer_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json` / `evidence/FROZEN_MODELS.json` / `evidence/SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py`。

M3 主链作为前置证据保留：

`research/activity_degree_incremental_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json`。

历史 backlog 权威：

`docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json` → `RESEARCH_BACKLOG_CLOSEOUT_20260912.md` → `scripts/validate_research_backlog_closeout.py`。

reception 并行链：

`research/prospective_reception_recorder_v1/PROGRAM_STATE.json` → `CLOUD_ACCEPTANCE_RESULTS.md` → `CLOUD_ACCEPTANCE_EXECUTION_RECEIPT.json` → D5R。

治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准。

## 最新科学结果：Cross-index current-degree transfer utility V1

问题：在 target 自己的 confirmed history + current E15 I/V 已知后，**另一个指数同一 E15 的 current I/V** 是否仍有足够大的未来风险增量？

固定三模型：

- C：target own D4-style history + current own I/V；
- X：C + other-index current I/V 的 15-column frozen nonlinear/target-interaction block；
- L：C + 完全同复杂度、只使用 other-index 已确认历史的 lag-I/V block。

每个 endpoint/horizon 只有 `X vs C` 与 `X vs L` **同时通过**才允许晋升。

决定性 frozen Validation run `34677297901`、job `103509323551` 全绿。它直接下载并校验第一次 Development fit 在 Validation 前冻结的原始模型 bytes：

`7eae7142323b38c5ae54618745e9ad9891c00afb09d02e8eb8def4490675f6b6`。

决定性 artifact：`10292433776`，ZIP SHA256：

`1ab8a12d77beb15c7aba5880a588c3475dc7d6270ca121eb95056ef9aa56ba92`。

`VALIDATION_RESULTS.json` SHA256：

`01780af3bcee5d087eb3af4ea02739a210a28b1cd211e08892a5be1de2b4664f`。

完整 Action artifact 已按原字节持久化到 `research/cross_index_degree_transfer_utility_v1/evidence/`。

### Cohort

- 15m：Development 59,614；Validation 39,770；paired coverage 100%；
- 30m：50,890 / 33,950 / 100%；
- 60m：33,442 / 22,310 / 100%。

### 结论

12 个固定 comparison **全部未过冻结 1% practical relative gate**，而且 12 个 5-day Bonferroni adjusted CI 下界全部不大于 0。六个 endpoint×horizon joint promotion 全部 false。

相对 own-C 的 pooled relative gain：

- log future RMS：15m +0.02198%，30m +0.05586%，60m +0.10147%；
- future tail：15m +0.00094%，30m +0.07701%，60m +0.14197%。

相对等复杂度 lag-other L 更小：

- log future RMS：+0.00028% / +0.06299% / +0.03029%；
- future tail：-0.03159% / +0.01541% / +0.00295%。

最大 pooled 点估计也只有 +0.14197%，约为 1% frozen gate 的七分之一；对应 tail absolute Brier gain `0.00011937` 也远低于 frozen `0.0005`。

此外多个 STAR50 target slice 为负、多个 year/tail slice 为负；30m/60m tail 的 X-vs-C 2023 forward Development gain 为负。因此不是“差一点过门槛”的结果。

15m cohort 的 own/other current shock-intensity correlation 约 0.6356，own/other current vol-ratio 约 0.7354，other current vs lag vol-ratio 约 0.9148。解释上，这与 own-I/V 已经吸收大部分共同风险信息、other-current 剩余边际很小一致；这只是描述，不是 gate。

**禁止**事后只挑 `STAR50 -> CSI1000` 或其他单向方向救结果；禁止搜 lag、状态、阈值、horizon 或删除样本救结果。other-current I/V 不进入 D5 consumer，也不成为 V19 新状态。

执行中出现过三次纯工程阻断：descriptive `g.tail` pandas 名称碰撞、refit exact-byte SHA fail-closed、compat wrapper import path；都发生在不改变 frozen protocol/model/gates 的前提下。最终结果使用的是**第一次 Validation 前冻结的精确模型 bytes**，不是后来的 refit。

## 前置科学结果：Activity-degree incremental utility V1

**`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`** 保持不变。

current M3 相对 D4-style own current-I/V baseline 对未来 log-RMS 确有额外信息：15m `A vs C` +2.175%，单项全部 gate 通过；30/60m 点估计也为正。但相对等复杂度 lagged-M3，15/30/60m 只有约 +0.433% / +0.579% / +0.183%，均低于冻结 1% practical gate，tail 也未晋升。因此 M3 不进入 D5/V19，不做参数救援。

## 历史 research backlog

状态仍是 **remaining executable legacy backlog = 0**。112 个研究分支审计标出的 12 个高召回“未闭环”对象已经逐项裁决；不要再按旧 branch 名推断待执行任务。v0.6.17 因冻结协议要求的两个事前 identity 在严格 pre-freeze Git 历史中不存在而永久 fail-closed；old router/PnL 线仍退役。

## Reception 并行状态

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING` 不变。历史没有逐条真实本机 `received_at`；云端 recorder/adapter/handoff 验收已经完成。未来真实 reception 证据只能由未来物理 feed 产生并服从 V2 治理。

## 保持不变的历史结论

- `RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE`；
- V19 冻结，不为 accuracy 开 V20；
- D3 practical negative 不变；
- D4 own-index current I/V endpoint-limited support 不变；
- D5 bounded consumer contract 不变；
- D5R 历史真实 reception clock 不可恢复。

## 下一步

当前 cross-index current-degree specification 已关闭。**不允许**把下一步变成单向 cross-index、lag 搜索、状态筛选或阈值调参来救它。

只有发现一个与 V19 / D4 / M3 / 当前 cross-index 证据真正不同、并能在看结果前冻结的独立因果风险机制时才新开科学实验；否则正确动作是维持并审计当前 authority。

仍然：不读受保护 2026 逐行数据，不查 BlackBox，不算 PnL，不恢复 router，不开 D6/V20，不提高 production authority。

`cross_index_current_degree_incremental_supported=false`; `cross_index_current_degree_consumer_promotion=false`; `current_m3_consumer_promotion=false`; `historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `validation_reused=true`; `fresh_oos=false`; `cloud_acceptance_supported=true`; `measured_feed_latency_supported=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
