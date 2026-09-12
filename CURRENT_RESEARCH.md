# 当前任务：signed-return asymmetry 增量路径已关闭

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置科学决定继续保留：

- `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- D4 current own-index I/V 仅在指定 endpoint 保持有限支持；
- D3 practical negative；V19 frozen；D5 bounded consumer contract 不变。

并行 reception 工程状态仍是：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

历史 research backlog 仍是：

**`RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`**。

## 当前权威链

最新科学主链：

`research/signed_risk_asymmetry_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` → `EXECUTION_RECEIPT.json` → `evidence/VALIDATION_RESULTS.json` / `evidence/FROZEN_MODELS.json` / `evidence/SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py`。

独立 fail-closed 校验：

`scripts/validate_signed_risk_asymmetry_utility_v1.py` + `.github/workflows/signed-risk-asymmetry-authority.yml`。

前置权威继续保留：

- one-step degree trajectory：`research/degree_trajectory_utility_v1/`；
- 12-bar shock memory：`research/historical_shock_burden_utility_v1/`；
- cross-index current degree：`research/cross_index_degree_transfer_utility_v1/`；
- current M3 refresh：`research/activity_degree_incremental_utility_v1/`；
- D4 / D3 / D2 / V19 / D5；
- backlog closeout：`docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json`；
- reception：`research/prospective_reception_recorder_v1/` → D5R。

治理以 `docs/governance/DATA_USAGE_POLICY_V2.md` 为准。

## 最新科学结果：Signed-risk asymmetry incremental utility V1

本轮问的是一个此前未正式验收的信息轴：**最近已完成收益的正负结构**，在 own current E15 intensity / volatility-ratio 与绝对波动历史已知以后，是否还能稳定增加未来非PnL风险信息。

冻结信息只来自当前决策点之前的12个有效已完成5m收益；当前 unfinished bar 通过 `shift(1)` 明确排除。

固定三模型：

- C：84-column own-index D4-style current-I/V baseline；
- A：C + `SEI12` / `SAI12` signed-asymmetry block；
- M：C + 同窗口、同列数、同非线性/状态交互的 magnitude-only control；
- A/M 都是104 columns，ridge、fit rows、复杂度一致。

只有 A 同时打赢 C 和 M，并通过预注册 practical/CI/slice gates，才可晋升。

决定性 Action run：`34681733485`。2021–2023 Development 先 fit/freeze；随后同一 run 的 exact frozen artifact 才解锁 2024–2025 reusable Validation。

冻结模型 SHA256：

`92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2`。

Validation artifact：`10293179281`，ZIP SHA256：

`f9597bb93b91a481b6a07a225dfae22c90c2f9178216079f41e6053f3076af79`。

`VALIDATION_RESULTS.json` SHA256：

`c0ffac04a70fed796bfb766876bd51f1781c788e4648b202eefd3b9ef01b203b`。

完整决定性 evidence 已按原字节持久化进 `research/signed_risk_asymmetry_utility_v1/evidence/`。

### Cohort / coverage

- 15m：Development 59,614；Validation 39,770；coverage 100%；
- 30m：50,890 / 33,950 / 100%；
- 60m：33,442 / 22,310 / 100%。

### 正式比较

A 的 pooled relative squared-loss reduction：

| Horizon | Endpoint | A vs C | A vs M | Joint supported |
|---|---|---:|---:|---|
| 15m | log future RMS | +0.35160% | +0.19345% | No |
| 15m | future tail | +0.19928% | +0.11586% | No |
| 30m | log future RMS | +0.89813% | +0.70577% | No |
| 30m | future tail | +0.30819% | +0.23314% | No |
| 60m | log future RMS | **+1.35593%** | **+1.02822%** | **No** |
| 60m | future tail | +0.54520% | +0.43298% | No |

六个 endpoint×horizon joint promotion 全部 false；12项 formal comparison 全部 `supported=false`。

最值得解释的是60m future-RMS：pooled 点估计确实同时超过冻结1% practical threshold，但**仍不支持晋升**：

- A vs C 5-day family-adjusted CI lower = `-0.0016721298128465787`；
- A vs M 5-day family-adjusted CI lower = `-0.0019976749339485705`；
- STAR50 `000688.SH` 两组绝对 gain 都为负；
- CSI1000 `000852.SH` 两组绝对 gain 都明显为正。

也就是说，这里存在**跨指数异质的统计提示**，不是一个已证明稳定的共同底层风险机制。预注册协议要求调整后区间为正且每个 symbol slice 非负，因此正式拒绝。

Tail 也不通过：最强绝对 Brier gain 只有 `0.0004583935491319103`，仍低于冻结 `0.0005` practical gate，且调整后区间跨0。

### 严格解释边界

不能说 signed asymmetry “完全没信息”；也不能把 pooled 60m >1% 摘出来说成“已支持”。正确结论是：

> 固定12-completed-bar signed-asymmetry 表征在 CSI1000 上出现较强60m RMS 信号，但在 STAR50 上同一表征为负，因此没有证明跨两指数稳健、可独立晋升的未来风险增量。

禁止事后只保留 `000852.SH`。这会直接违反 V1 的冻结 protocol。

本轮因此：

- 不向 D5 增加 signed-asymmetry 字段或 decision gate；
- 不修改 V19；
- D4/D5 authority 不变；
- 不产生方向/交易/PnL含义；
- 不创建新 risk state / threshold / production field。

## Fixed path 已关闭

signed-asymmetry V1 到此关闭。禁止使用本次 reusable Validation 去做：

- 只选 CSI1000；
- 6/24/48-bar window 搜索；
- decay/EWMA；
- 改成 skewness、downside-count 或别的事后 sign 表征；
- state/slot/year/symbol筛选；
- 改 ridge / horizon / bootstrap family / practical gate；
- 删除 magnitude-only M control。

若未来再研究收益符号结构，必须是**真正不同、事前可冻结的因果机制问题**，不能围绕本次 CSI1000 正信号做救援。

## 前置科学结果保持不变

- one-step trajectory/delta：最多约0.15%小信号，不获独立预测 promotion；D4/D5 delta 继续只作描述/诊断；
- 12-bar cumulative shock burden：有少量统计信号但没有实用、稳定的 shock-specific increment；
- cross-index current degree：other-current I/V 在 own-current 已知后不支持增量 promotion；
- current M3：相对 D4 baseline 有信息，但 current-refresh 相对 lagged-M3 未过 practical gate；
- D4 own current I/V：指定 endpoint 有限支持；
- D3 practical negative；V19 frozen；D5 bounded consumer contract 不变。

## 历史 backlog 与 reception

历史 research backlog 仍是 **remaining executable legacy backlog = 0**，旧 detector/RMR/router/v0.6.17 不重开。

reception 仍是 `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`。历史不存在可恢复的逐条真实本机 `received_at`，未来证据只能由未来物理 feed 产生并服从 V2 治理。

## 下一步边界

signed-asymmetry fixed specification 已关闭。下一科学题必须与 V19 / D4 / M3 / cross-index / shock-memory / trajectory / signed-asymmetry 都真正不同，且能在结果前冻结；若仓库审计找不到这样的独立机制，正确动作就是 **hold / maintain authority**，不是继续制造窗口、阈值或单指数救援。

仍然：不读受保护2026逐行数据，不查BlackBox，不算PnL，不恢复router，不开D6/V20，不提高production authority。

`signed_return_asymmetry_incremental_supported=false`; `pooled_60m_rms_one_percent_gate_met=true`; `cross_symbol_robustness_supported=false`; `single_index_rescue_authorized=false`; `signed_asymmetry_consumer_promotion=false`; `degree_trajectory_incremental_supported=false`; `delta_independent_predictive_promotion=false`; `d5_contract_unchanged=true`; `historical_shock_burden_incremental_supported=false`; `cross_index_current_degree_incremental_supported=false`; `current_m3_consumer_promotion=false`; `historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `validation_reused=true`; `fresh_oos=false`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
