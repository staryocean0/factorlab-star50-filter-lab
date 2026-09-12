# 当前任务：cross-index residual dislocation V1 已关闭，研究进入 HOLD

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

研究程序状态：

**`HOLD_CURRENT_AUTHORITY`**。

这里的 HOLD 表示：在完成旧 backlog 与独立机制审计后，当前仓库中已经没有一个**已识别、可事前冻结、且不依赖已看 Validation 做事后选择**的独立风险信息轴可以继续直接执行。它不意味着未来永远不存在新机制；若出现真正新的 pre-outcome causal mechanism 或新的 prospective data，仍可重新开启新的预注册研究。

前置科学决定全部继续有效：

- `INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- D4 current own-index I/V 仅在指定 endpoint 保持有限支持；
- D3 practical negative；V19 frozen；D5 bounded consumer contract 不变。

并行 reception 工程状态仍是：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

## 最新研究：cross-index residual dislocation

重复审计确认，该轴不同于已关闭的 `cross_index_degree_transfer_utility_v1`：后者只问“另一指数当前 I/V”在 own I/V 已知后是否增量；本轮问的是两个指数当前相对位置是否偏离过去 48 个已确认 5m 配对收益形成的动态关系。

机制身份来自 2026-09-09 已冻结的旧 `rmr_cross_index_relative_dislocation_v1`，但本轮去掉 rich/cheap 方向和未来均值回归交易含义，只研究未来非 PnL 风险，因此不是从刚完成的 intrabar Validation 中事后挑出来的候选。

冻结三模型：

- `B = 99 columns`：own D4-style current E15 baseline + other-index current I/V nuisance block；
- `R = 107`：`B + RZ48`，48-paired-return trailing-OLS absolute residual severity；
- `Q = 107`：`B + QZ48`，同一历史/当前配对上的 equal-weight spread severity control；
- `R/Q` 同 rows、同 8-column expansion、同 ridge `0.01`；
- RZ48/QZ48 对全局收益符号翻转不变，不编码交易方向。

## 决定性执行

正式 Actions run：`34688304454`。

- Development fit job `103539075057`：success；
- reusable Validation job `103539290902`：success；
- frozen-model artifact `10296505999`，ZIP SHA256 `76efc29fcae706e698bc1ea6ae7918389f72766756f5b3ad90a0ba75929ea827`；
- Validation artifact `10295914902`，ZIP SHA256 `80da5740e89582c47e147a7ce3a590c75eabee9599a35b5f52bc110f4403fb33`；
- frozen model SHA256 `8f37d237172a86c23aa75baf3f69f2f5b8948cbbd12c267bdde5da6864607d94`；
- `VALIDATION_RESULTS.json` SHA256 `2cc44ce7baff43dfd84884e6ce1ebf81aada12c2644e1bbe48384ac4d8f82654`。

2021–2023 Development 先 fit/freeze；冻结字节完成后才打开 2024–2025 reusable Validation。未读取受保护 2026 逐行数据，未使用 synthetic 2026，未查 BlackBox，未算 PnL。

## 正式结果

六个 endpoint×horizon joint promotion 全部 false，12 个 formal comparison 全部 `supported=false`。

| Horizon | Endpoint | R vs B | R vs Q |
|---|---|---:|---:|
| 15m | log future RMS | +0.11686% | -0.01174% |
| 15m | future tail | +0.23570% | +0.08571% |
| 30m | log future RMS | +0.20754% | +0.04428% |
| 30m | future tail | +0.17887% | +0.07457% |
| 60m | log future RMS | +0.19959% | +0.03745% |
| 60m | future tail | +0.22107% | +0.07897% |

这个结果不能表述成“完全没信息”。`R vs B` 六个 pooled 点估计全部为正；其中 30m future-RMS 的 family-adjusted 5-day absolute-gain interval 为 `[0.00002458597848098955, 0.0007121645590173982]`，且两个指数和 2024/2025 slices 全部为正，存在一个干净的**弱统计提示**。

但它不能晋升：

- 最大 `R vs B` relative gain 只有 `+0.23570%`，远低于冻结 `1.00%` practical gate；
- 相对等复杂度 `Q` 后，residual-specific 增量最大只有 `+0.08571%`，15m RMS 还是负的；
- 没有任何 `R vs Q` 的调整后 5-day lower bound > 0；
- 最大 tail absolute Brier gain `0.00018560800053409512`，低于 `0.0005`。

因此正确解释是：**跨指数相对错位有少量未来风险信息，但动态 beta residual geometry 没有证明比简单 pairwise spread severity 更有实用、可独立晋升的价值。**

Availability 不是拒绝原因：Development 与 Validation 对所有 horizon 的 common relationship/control coverage 都是 100%，样本量与 tail event 数均满足门槛。

## 当前权威链

最新主链：

`research/cross_index_residual_dislocation_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` → `EXECUTION_RECEIPT.json` → `evidence/EVIDENCE_SOURCE.json` / exact `FIT_RECEIPT.json` / `comparisons.csv` / `MODEL_SHA256.txt` / `ARTIFACT_SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py` / `test_study.py`。

独立 fail-closed 校验：

`scripts/validate_cross_index_residual_dislocation_utility_v1.py` + `.github/workflows/cross-index-residual-dislocation-authority.yml`。

## Closed path / 禁止 rescue

本 V1 禁止：

- 改 48-return window；
- robust/ridge/rolling correlation/cointegration 关系模型搜索；
- 改或删 `QZ48` control；
- residual sign、rich/cheap 或 beta-direction rescue；
- 单指数/year/state/slot/horizon 筛选；
- 移动 E15 或读取 final current-bar close；
- 降低 1% / 0.0005 practical gates；
- 重开 directional RMR、intrabar ordering、signed asymmetry 或 multiscale-volatility 路线。

## HOLD 边界

历史 executable backlog 继续为 0。此次独立机制审计后：isolated-shock/event-overshoot 等旧 RMR 路线仍属于方向/反转问题；relative residual 这条可转译为非方向风险问题的独立轴也已正式验收并关闭。

因此下一步不是再制造窗口、关系模型或 control 变体，而是 **maintain current authority / wait for a genuinely new preregisterable causal mechanism or new prospective data**。

仍然：不向 D5 增加 residual-dislocation 字段或 gate；D4/D5 authority 不变；V19 frozen；不读受保护 2026；不查 BlackBox；不算 PnL；不开 D6/V20；不提高 production authority。

`cross_index_residual_dislocation_incremental_supported=false`; `all_R_vs_B_pooled_gains_positive=true`; `residual_specific_practical_increment_supported=false`; `one_percent_gate_met_any=false`; `tail_0005_gate_met_any=false`; `distinct_executable_axis_remaining=false`; `research_hold=true`; `d5_contract_unchanged=true`; `validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `synthetic_2026_used=false`; `blackbox_queried=false`; `pnl_computed=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
