# STAR50 / CSI1000 当前权威索引

## 最新科学状态：SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED

[当前任务](../CURRENT_RESEARCH.md) → [接续](../CONTINUE_HERE.md) → [程序状态](../research/signed_risk_asymmetry_utility_v1/PROGRAM_STATE.json) → [正式结果](../research/signed_risk_asymmetry_utility_v1/RESULTS.md) → [决定性回执](../research/signed_risk_asymmetry_utility_v1/DECISIVE_RECEIPT.json) → [原始Validation结果](../research/signed_risk_asymmetry_utility_v1/evidence/VALIDATION_RESULTS.json)。

## Signed-risk asymmetry incremental utility V1

冻结问题：own current E15 I/V、previous state 与历史绝对波动信息已知后，前12个有效已完成5m收益的**正负结构**是否还能稳定增加未来非PnL风险信息。

- C = 84-column own D4-style baseline；
- A = C + `SEI12` / `SAI12` signed-asymmetry block；
- M = C + 同12-bar历史、同复杂度 magnitude-only control；
- A/M 均104 columns，schema/state-interactions/ridge/fit rows一致；
- 当前 unfinished bar 通过 `shift(1)` 排除。

决定性 run `34681733485` 使用 Validation 前冻结的 exact model SHA256：

`92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），coverage均100%。六个joint promotion全部false，12项 formal comparison 全部 `supported=false`。

future-RMS relative gains（A vs C / A vs M）：

- 15m +0.35160% / +0.19345%；
- 30m +0.89813% / +0.70577%；
- 60m **+1.35593% / +1.02822%**。

60m pooled 点估计是一个真实提示，但仍不满足冻结 robustness gates：两组 family-adjusted 5-day CI 下界均小于0；`000688.SH` absolute gain 均为负，而 `000852.SH` 均明显为正。正式结论因此不是“完全零信息”，而是**没有证明跨两指数稳健、可独立晋升的共同风险机制**。

禁止把 Validation 后看到的异质性改写成 CSI1000-only 模块。Tail 也不晋升；最强 absolute Brier gain=`0.0004583935491319103`，低于冻结`0.0005`且区间跨0。

完整 Action evidence 按原字节保存在 `research/signed_risk_asymmetry_utility_v1/evidence/`；独立 authority validator：`scripts/validate_signed_risk_asymmetry_utility_v1.py`。

D5 不增加 signed-asymmetry field/gate；V19 frozen；D4/D5 authority 不变；无方向/交易/PnL/production 含义。

Fixed path 已关闭：不做 CSI1000-only、6/24/48-bar、decay/EWMA、skew/downside-count替换、selected index/state/time、变换/正则/horizon/gate tuning，也不删除M control。

## 前置科学状态

- `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`：lag1/delta仅小统计信号，不获predictive promotion；
- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`：固定12-bar累计shock burden不晋升；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`：other-current degree不晋升；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`：current M3 refresh不晋升；
- [D4](../research/continuous_risk_utility_d4/RESULTS.md)：own current I/V endpoint-limited support；
- [D3](../research/causal_state_utility_d3/RESULTS.md)：离散状态实用增量未支持；
- [D2](../research/causal_state_delivery_d2/RESULTS.md)：双时钟因果回放；
- [V19](../research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)：冻结状态机；
- [D5](../research/state_degree_consumer_d5/RESULTS.md)：bounded consumer。

## 历史 research backlog / reception

历史 research backlog 已关闭，remaining executable legacy backlog = 0。backlog closeout 以 `docs/research/RESEARCH_BACKLOG_CLOSEOUT_20260912.json` / 对应 authority ledger 为准。

Reception 并行状态仍为 `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`。历史没有逐条真实本机`received_at`；未来true-reception observations只能来自未来真实feed并服从V2治理。

## 下一执行边界

signed-asymmetry fixed specification 已关闭。下一科学题必须与 V19 / D4 / M3 / cross-index / shock-memory / trajectory / signed-asymmetry 都不同，并在结果前冻结；若完整机制审计找不到这样的独立信息轴，正确状态是 hold / maintain authority，而不是继续窗口、阈值或单指数救援。

不查BlackBox、不读受保护2026逐行数据、不算PnL、不恢复交易router、不为V19开V20、不因reception缺口开D6、不提高production authority。
