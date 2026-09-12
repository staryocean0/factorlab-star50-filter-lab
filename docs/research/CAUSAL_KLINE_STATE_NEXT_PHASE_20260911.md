# 权威叙事：状态上下文 + 连续风险程度 + 因果适用性

2026-09-11建立；2026-09-12更新至 signed-risk asymmetry incremental utility V1 完成。目标始终是把**当时可知**的K线风险状态、程度、适用性与缺失/时钟语义正确交给下游研究，不把实用导向偷换成交易动作。

## 已完成的核心证据层

- V19/V16–V18：冻结状态识别与恢复基线；不为accuracy开V20。
- D2：E15/CLOSE双时钟历史工程回放支持。
- D3：三状态表达未达到原实际增量门槛，`D3_INCREMENTAL_UTILITY_NOT_SUPPORTED` 不变。
- D4：current E15 I/V 对15/30/60m未来波动强度和30m尾部有限支持；这是当前连续程度轴的主要实用证据。
- D5：bounded consumer把状态、连续程度、时间/失效/缺失语义接通。
- D5R + reception recorder/adapter/cloud acceptance：历史真实本机received_at不可恢复；云端工程验收完成；未来真实arrival仍需未来物理feed。
- risk-coordinate frozen Validation：state-persistence轴复制；M3极端effect-size存在，但完整amplitude axis未过冻结support门槛。
- Activity-degree incremental utility V1：current M3相对D4-style I/V有future-RMS信息，但相对等复杂度lagged-M3的current refresh未过1% practical gate，`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`。
- Cross-index current degree：own-current I/V已知后，other-current degree不支持独立promotion，`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`。
- Historical shock burden：固定12-bar累计shock memory只有小统计信号，没有稳定、实用的shock-specific increment，`HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`。
- One-step degree trajectory：lag1/delta相对current-level/lag2只有约0.15%量级的小信号，不支持独立predictive promotion，`ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`。
- **Signed-risk asymmetry V1**：过去12个已完成收益的正负结构出现跨指数异质信号，但不满足预注册稳健性门，`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`。
- 历史 research backlog closeout：旧research分支已经裁决，当前 executable legacy backlog = 0。

## 最新：Signed-risk asymmetry 的含义

本轮不是做方向预测，而是问过去收益的**正负结构**是否能提高未来非PnL风险刻画。所有 sign 特征都来自前12个有效已完成5m收益；当前 unfinished bar 不进入。

冻结三套同cohort ridge信息集：

- C：84-column own D4-style current-I/V baseline；
- A：C + signed energy imbalance / signed absolute-return imbalance；
- M：C + 同窗口、同20-column复杂度的 magnitude-only control。

决定性 Action `34681733485`：Development先fit/freeze，随后同一run exact frozen artifact读取2024–2025 reusable Validation。冻结模型 SHA256：

`92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2`。

60m future-RMS pooled relative gains达到：

- A vs C：+1.35593%；
- A vs M：+1.02822%。

但**这不是support**。两组 family-adjusted 5-day CI lower 都小于0；同时 STAR50 (`000688.SH`) 两组 absolute gain 都为负，而 CSI1000 (`000852.SH`) 都明显为正。冻结 protocol 要求 adjusted interval >0 且每个symbol slice非负，因此六个endpoint×horizon joint promotion全部false，12项formal comparison全部`supported=false`。

这说明存在一个值得记录的**异质统计提示**：同一固定 sign 表征对 CSI1000 的60m future-RMS有明显正信息，但对 STAR50 不成立。因为这个差异是在 Validation 后看到的，不能再把 V1 事后改成 CSI1000-only 模块。

Tail也不获promotion；最强absolute Brier gain为`0.0004583935491319103`，低于冻结`0.0005`且调整区间跨0。

因此：signed-asymmetry 不进入D5、不修改V19、不创建新state/threshold/production field，也不产生交易方向或PnL含义。

## 前置 negative paths 的治理含义

### Current M3

M3相对C有信息，但相对等复杂度lagged-M3没有达到current-refresh practical increment。不能调M3 band/30bp surface/ridge/horizon/bootstrap/sample gate或删除lagged control来救结果。

### Cross-index current degree

两个指数同时刻的other-current I/V在own-current已知后没有足够独立增量。不能把cross-index contemporaneous transfer改造成新的consumer gate。

### Historical shock memory

最近12个已完成bar里的shock count/excess burden没有证明独立shock-specific实用增量。不能再改窗口/decay/state筛选救援。

### One-step degree trajectory / delta

D4/D5的`lag_intensity`、`lag_ratio`、`delta_intensity`、`delta_ratio`仍可作为描述/诊断字段存在，但没有独立predictive promotion；不能升级成D5 decision gate。

### Signed asymmetry

不能做CSI1000-only、6/24/48-bar、EWMA/decay、skew/downside-count替换、selected state/slot/year/symbol、改ridge/horizon/bootstrap/gate，或删除M control。

## Historical backlog closeout 的含义

旧分支不删除，原verdict不重写。closeout只是把历史实际状态恢复清楚：旧first-shock/detector/RMR/router不属于当前未执行任务；有效祖先结果已被后继Validation吸收；v0.6.17的frozen scientific replay因为所需事前identity在严格Git历史里不存在而永久blocked，不能现在重算hash伪装成旧identity。

当前 `remaining_executable_legacy_backlog=0`。

## 当前推荐的交付对象

研究consumer仍以三层为主：

1. V19状态上下文与转移；
2. D4支持范围内的current连续风险程度 I/V；
3. observation / decision / published / expiry、确认性质和缺失原因。

以下均**不获得新的consumer promotion**：current M3、cross-index current degree、historical shock burden、one-step delta/trajectory、signed-return asymmetry。

## Reception并行结论

`DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`不变。历史没有逐条真实本机`received_at`可恢复；未来true-reception evidence只能来自未来真实feed并服从V2治理。

## 下一阶段治理

当前没有遗留分支需要补跑。新科学实验必须满足两个条件：

1. 信息轴/机制与 V19 / D4 / M3 / cross-index / shock-memory / trajectory / signed-asymmetry **真正不同**；
2. 在看结果前冻结问题、信息集、比较器、门槛与停止规则。

若完整仓库机制审计找不到这样的独立风险机制，正确状态是 **hold / maintain authority**，而不是为了“继续”强造 window、lag、threshold、subgroup 或版本号。

停止线：不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复payoff/router、不为V19开V20、不因reception缺口开D6、不提高production authority。

`signed_return_asymmetry_incremental_supported=false`; `single_index_rescue_authorized=false`; `signed_asymmetry_consumer_promotion=false`; `degree_trajectory_incremental_supported=false`; `historical_shock_burden_incremental_supported=false`; `cross_index_current_degree_incremental_supported=false`; `current_m3_consumer_promotion=false`; `historical_research_backlog_closed=true`; `remaining_executable_legacy_backlog=0`; `d4_decision_unchanged=true`; `d5_contract_unchanged=true`; `v19_frozen=true`; `blackbox_queried=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`。
