# Session-aware information-set bounds v0.6.17 — frozen preanalysis protocol

日期：2026-09-07  
任务：CL-STAR-RISK-20260907  
分支：`research/session-aware-information-set-bounds-v0617-20260907`  
基线：`research/risk-gate-takeover-20260907` / `b5504ba68053e22bcad11aa3149e761b445a64f8`  
状态：**results-blind preanalysis implementation frozen; real authoritative DataHub replay not yet executed**。

## 1. 本协议只回答什么

本阶段只检验：在冻结的 native-leg universe 上，利用 DataHub **真实 source support set**，细尺度位移集中度到底能否由当前信息集精确识别，或只能得到多宽的保证区间。

本阶段不查看、拟合或汇总收益、P&L、回撤、交易、方向、第三浪、OOS结果或任何未来标签。`morphology_replication_not_yet_accepted` 继续有效；本协议通过也不等于形态复刻通过，更不等于风险门控或交易有效。

## 2. 已冻结且不得在本地重定义的统计量

沿用仓库 `src/star50_filter/wave_shape.py::waveform_shape` 中已经使用的 `motion_concentration` 定义，而不是另造指标。

对一个有 `n` 个细尺度步骤的 **log-price** path，记

\[
a_i=|\Delta \log P_i|,\qquad p_i=a_i/\sum_j a_j,
\]

则

\[
C=n\sum_{i=1}^n p_i^2.
\]

含义：位移完全均匀分布时 `C=1`；全部位移集中在一个步骤时 `C=n`。零位移 path 的该统计量无定义，本协议不强行赋值。

因此，对于至少有一个未观测/被 DataHub slicer 丢弃的细步骤，若不附加新的价格路径假设，保证意义下的 universal interval 固定为：

\[
C\in[1,n].
\]

不得为了区间更窄而插值、把缺失步当零收益、删除 session-boundary leg、把相邻 native close 塞进本 bar，或新增平滑/随机路径先验。

## 3. v0.6.15 的错误与 v0.6.17 的唯一拓扑修复

v0.6.15 的失败点是把“相邻 native close”当成“一根 native bar 的完整两端”，并隐含 fixed-five topology。这样在午休、隔夜以及 offset native buckets 附近，会把 DataHub slicer 明确不属于当前 native bar 的分钟/间隙错误塞入当前 OHLC envelope，导致一批本应可比较的 leg 出现 data-consistency failure。

v0.6.17 的修复原则只有两条：

1. **每个 native leg/bar 独立使用 DataHub 实际 membership/support set**；FactorLab 不复刻 bucket SQL，不按时钟自行猜 support，也不从相邻 close 推断 support。
2. **support gap 明确保留为信息缺口**；leg 不因 session edge、offset、午休或隔夜而从总体中删除。只要 expected support 中有任一步未观测，该 leg 就使用完整 `[1,n]` universal interval。

这个修复不改变 frozen published-leg universe、strict-pair overlay 或 qualification overlay；它只改变错误的 hidden-step topology。

## 4. DataHub authority / identity gate

正式 authoritative replay 必须同时满足：

- full authoritative 1m source surface 行数 = **349,923**；
- 必须给出 frozen DataHub identity receipt 中的 source file SHA-256；runner 会逐字节核对；
- 已知 FactorLab `1m_official` **350,561 行**的 surface 明确不等同于 DataHub authority，authoritative mode 会 fail closed；
- `legs` 输入必须给出 v0.6.15 frozen receipt/manifest 中的 SHA-256，防止本地重新筛 universe；
- 每一个 `observed=true` 的 support row 必须通过稳定 source key 回连到刚刚通过 identity gate 的 authoritative source，且 OHLC 数值一致；默认 source key 是 `timestamp`。若 authoritative source 合法存在重复 timestamp，必须改用其稳定 row key，而不是去重；
- support membership / `expected_step_count` 来自 DataHub archived contract/deriver 的实际导出或 diagnostic。FactorLab runner 不允许自行实现 official-v2 / wall-clock-v1 的第二套 bucket 逻辑。

### offset0 caveat

已归档 evidence 中存在 lineage metadata caveat：offset0 文件 metadata 曾标成 wall-clock v1，但 DataHub 实际 5m path 走 official v2；对 **5m offset0**，两套 source-minute→label 映射逐分钟等价，因此不构成本阶段 blocker。不得把这个等价性外推到 15/30/60m。

## 5. 输入合同

### `authoritative_source`

CSV/Parquet。完整 349,923-row DataHub authoritative 1m source surface。至少包含：

- 稳定 key（默认 `timestamp`）；
- `open`, `high`, `low`, `close`。

它不仅用于计数/哈希，也用于逐 support-row 的 source binding。

### `legs`

CSV/Parquet。必须是 frozen v0.6.15 published-leg universe/overlays，不在本地重算。必需字段：

- `leg_id`：唯一；
- `expected_step_count`：DataHub support topology 下该 leg 应有的细步骤数。

可带且 runner 原样透传：

- `published`, `strict_pair`, `qualified`；
- `offset`, `session_id`, `boundary_class`, `native_bar_id`；
- `native_open`, `native_high`, `native_low`, `native_close`。

若提供 native OHLC，complete support 必须能够独立聚合回同一 OHLC；不一致时该 leg fail closed 到 universal interval，标记 `data_consistency_mismatch`，不能伪称 oracle-comparable。

### `support`

CSV/Parquet。DataHub actual-support topology，一行对应一个 expected fine step 的 source membership。必需字段：

- `leg_id`；
- `step_ordinal`，从 `0` 到 `expected_step_count-1`，不能重复；
- `observed`；
- source key（默认 `timestamp`）；
- `open`, `high`, `low`, `close`。

被 DataHub 明确丢弃的 expected step 可以保留 placeholder 并设 `observed=false`；其 OHLC 不被用于 oracle。只要 ordinals 不完整或有 `observed=false`，该 leg 使用 universal interval。

## 6. 细路径的冻结构造

对 complete actual support，细路径固定为：

`[first source-minute open, source close at ordinal 0, source close at ordinal 1, ...]`

随后转为 log price 再计算 `motion_concentration`。

关键约束：**不在路径前面拼 previous native close**。因此 session gap / lunch gap / overnight gap 不会被偷塞进当前 native OHLC；若这些 gap 本来属于冻结 leg 定义但 DataHub 没有 source support，则通过 `expected_step_count` / placeholder 明确体现为缺失信息，并得到 universal interval。

## 7. results-blind gate

`legs` 和 `support` 中若出现明显 realized economic/trading outcome 字段（例如 `pnl`, `return`, `profit`, `drawdown`, `sharpe`, `future_ret`, `oos_result` 等），runner 直接拒绝执行。

本阶段允许按以下冻结结构做分层 summary：`offset`、`boundary_class`、`published`、`strict_pair`、`qualified`。summary 只报告 support coverage、oracle-comparable 数量、OHLC mismatch、区间宽度；不报告事件结果、交易结果或未来收益。

## 8. frozen outputs

正式 runner 固定输出：

1. `leg_information_bounds_v0617.csv`
   - `leg_id`
   - `protocol_version`
   - `expected_step_count`, `observed_step_count`
   - `support_complete`, `support_gap`
   - `ohlc_consistency`
   - `oracle_comparable`
   - `motion_total_log`
   - `motion_concentration_oracle`
   - `concentration_lower`, `concentration_upper`, `bound_width`
   - `universal_bound_used`, `bound_reason`
   - `data_identity_status`
   - 已存在的 frozen overlays
2. `summary_v0617.json`：只含 topology / interval tightness / identity diagnostics。
3. `replay_receipt_v0617.json`：输入输出路径及 SHA-256、identity gates、results-blind 声明。

## 9. acceptance / rejection gates

### 代码层 PASS

只有当当前 commit 的 CI 实际执行并通过 repository tests，特别是以下 synthetic invariants，才可称 implementation test PASS：

- 均匀 log displacement → `C=1`；
- 单一步承载全部 displacement → `C=n`；
- variable support count（包括 6-step synthetic case）不被 fixed-five 假设拒绝；
- session-edge/support-gap leg 被保留并得到 `[1,n]`；
- current native open 被用于 bar 内路径，不注入 previous close；
- native OHLC mismatch 不得成为 false oracle；
- 350,561-row FactorLab surface 在 authoritative mode 被拒绝；
- future/trading outcome columns 被 results-blind gate 拒绝。

### real replay PASS

真实 replay 必须先通过 source hash/row count、legs hash、support→source binding 三个 identity gates。之后才能评价：

- frozen universe 中多少 leg exact/oracle-comparable；
- 哪些 offset / session boundary 只能得到 universal interval；
- interval 是否足够窄，足以支持后续 identifiability 研究。

本协议**不预先规定**一个为了“通过”而方便的 coverage/tightness 数值阈值；首次 authoritative replay 先如实形成 measurement result，再按事前科学问题裁决是否值得进入下一阶段。不得用删除边界样本提高 coverage。

## 10. 明确冻结的后续边界

即使 v0.6.17 real replay 很漂亮，也仍然只允许进入“information-set identifiability”下一步；不能自动解冻：

- morphology replication acceptance；
- direction / third-wave labels；
- returns / P&L / MDD；
- OOS；
- trading / position sizing / production。

任何修改集中度公式、support topology、leg universe、缺失值处理、offset contract interpretation 的行为都需要新协议版本，不能在本地 replay 时临时调整。
