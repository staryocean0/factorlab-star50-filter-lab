# 当前任务：intrabar temporal reversal V1 已关闭

更新：2026-09-12。使命不变：研究并交付**当时可知**的 K 线风险状态、连续风险程度、适用性和时间/缺失语义；本仓不开发交易动作、方向、仓位、收益 router 或生产策略。

## 当前正式状态

最新科学决定：

**`INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置决定继续有效：

- `SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- D4 current own-index I/V 只在指定 endpoint 保持有限支持；
- D3 practical negative；V19 frozen；D5 bounded consumer contract 不变。

并行 reception 工程状态仍是：

**`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`**。

## 最新研究：current-bar temporal ordering

本轮正式测试的是旧 backlog 中仍可能独立的一条 E15 信息轴：**当前 5 分钟内部的时间顺序/相邻折返结构**。

重复审计已确认它不同于旧 `rmr-activity-pressure-reversal-v1-20260909`：旧分支把最近五个 1m return 压成净 `R5`，研究未来价格是否反转；本轮则只看当前 unfinished 5m bar 在 E15 以前的 19 个严格 15s return 的排列顺序对未来非 PnL 风险是否有增量。

冻结三模型：

- `C`：84-column D4-style own-index current E15 baseline；
- `T`：`C + ARF19/LAC19`，order-sensitive；
- `O`：`C + FRMS19/NPE19`，同一批 19 returns 的 equal-complexity order-invariant control；
- `T/O = 104 columns`，同 rows、同 nonlinear expansion、同 state interactions、同 ridge `0.01`。

`ARF19/LAC19` 对整条路径全局乘 `-1` 不变，因此不编码交易方向。

## 决定性执行

正式 Actions run：`34685234360`。

- Development fit job `103530973458`：success；
- reusable Validation job `103531117262`：success；
- frozen-model artifact `10295610761`，ZIP SHA256 `cc1602a19c3dd802737a279c19ebe2ac42a51dd46d6e88dfc42d52f75b84ec2c`；
- Validation artifact `10294993214`，ZIP SHA256 `3066af6fc8963fb5948d6ac6d0afd26de7fa87746d00294c22630b62dc4f3a0e`；
- frozen model SHA256 `bd01e23def9300781c64a03f8377247ff30c67d0191c6cd213329d382ff8262c`；
- `VALIDATION_RESULTS.json` SHA256 `67b267af11802562f4f576d151472b064323c82af2a34e4451e471beb99b2cdc`。

2021–2023 Development 先 fit/freeze，冻结字节完成后才打开 2024–2025 reusable Validation。未读取受保护 2026 逐行数据，未用 2026 synthetic data，未查 BlackBox，未算 PnL。

## 正式结果

六个 endpoint×horizon joint promotion 全部 false；12 个 formal comparison 全部 unsupported。更强的是：**12/12 个 pooled Validation point estimate 都是负的**。

| Horizon | Endpoint | T vs C | T vs O |
|---|---|---:|---:|
| 15m | log future RMS | -0.11882% | -3.39167% |
| 15m | future tail | -0.03582% | -1.20147% |
| 30m | log future RMS | -0.16112% | -4.87737% |
| 30m | future tail | -0.02648% | -1.41548% |
| 60m | log future RMS | -0.19747% | -6.13570% |
| 60m | future tail | -0.00902% | -2.00825% |

所以这不是“有正信号但没过 CI/1% 门”的边缘失败。固定 `ARF19/LAC19` 顺序块在所有正式比较上都没有增量，而且相对于同栏 order-invariant `FRMS19/NPE19` 控制，劣势随 RMS horizon 扩大。

60m RMS 的 `T vs O` family-adjusted 5-day interval 也整体为负：`[-0.009490820998304195, -0.0043866678382002994]`，两个 index slice 都负。

Tail 方面所有 absolute gain 也都为负，因此没有任何一个能接近冻结的 `+0.0005` Brier practical gate。

## Availability 边界

Validation common-path coverage 通过 95% 门：

- 15m：96.9902%；
- 30m：96.5891%；
- 60m：95.0515%。

Development availability 明显较低（约 52–53%），且 60m Development `n=17,549 < 20,000`，因此 60m formal sample-size gate 也失败。但主科学拒绝不依赖这一点：Validation 的增量点估计本身已经全部为负。

## 当前权威链

最新主链：

`research/intrabar_temporal_reversal_utility_v1/PROGRAM_STATE.json` → `RESULTS.md` → `DECISIVE_RECEIPT.json` → `EXECUTION_RECEIPT.json` → `evidence/EVIDENCE_SOURCE.json` / exact `FIT_RECEIPT.json` / `comparisons.csv` / `MODEL_SHA256.txt` / `ARTIFACT_SHA256SUMS.txt` → frozen `PROTOCOL.md` / `run_study.py` / `test_study.py`。

完整 Validation/FROZEN_MODELS 原始字节的 Actions artifact identity、artifact ZIP digest 和文件 SHA256 已固定在 evidence source/checksum manifest 中。

独立 fail-closed 校验：

`scripts/validate_intrabar_temporal_reversal_utility_v1.py` + `.github/workflows/intrabar-temporal-reversal-authority.yml`。

## Closed path / 禁止 rescue

`intrabar_temporal_reversal_utility_v1` 到此关闭。禁止围绕本轮结果做：

- raw 3s grid / 不同 sampling grid；
- 把 E15 往 close 推；
- run length、entropy、crossing-count、motif、DTW、shape search；
- 改 zero-return treatment；
- state/slot/year/horizon/symbol 筛选；
- 单指数 rescue；
- 改 ridge 或 practical gates；
- 删除 `O` control；
- 重新打开 multiscale volatility 或 signed-asymmetry。

这不等于“所有 intrabar ordering 永远无信息”；它只关闭这个事前冻结的 ARF19/LAC19 specification。若下一步没有**真正不同且可事前冻结**的 causal mechanism，正确动作是 hold / maintain authority，而不是继续制造 feature/window rescue。

## Authority boundary

- 不向 D5 增加 temporal-reversal 字段或 gate；
- D4/D5 authority 不变；
- V19 frozen；
- 不开 D6/V20；
- 不产生方向、交易、仓位、PnL、router 或 production authority。

`intrabar_temporal_reversal_incremental_supported=false`; `all_12_validation_point_estimates_negative=true`; `temporal_reversal_consumer_promotion=false`; `signed_asymmetry_remains_closed=true`; `multiscale_volatility_remains_closed=true`; `validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `synthetic_2026_used=false`; `blackbox_queried=false`; `pnl_computed=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
