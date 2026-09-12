# 接续入口：signed-return asymmetry V1 已关闭

最新科学状态：**`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**。

前置状态继续有效：

- `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`；
- `DATAHUB_RECEPTION_CLOUD_ACCEPTANCE_V1_SUPPORTED_TRUE_RECEPTION_EVIDENCE_PENDING`；
- `RESEARCH_BACKLOG_20260912_CLOSED_NO_EXECUTABLE_LEGACY_BRANCH`。

## 先读

1. `CURRENT_RESEARCH.md`
2. `research/signed_risk_asymmetry_utility_v1/PROGRAM_STATE.json`
3. `research/signed_risk_asymmetry_utility_v1/RESULTS.md`
4. `research/signed_risk_asymmetry_utility_v1/DECISIVE_RECEIPT.json`
5. `research/signed_risk_asymmetry_utility_v1/EXECUTION_RECEIPT.json`
6. `research/signed_risk_asymmetry_utility_v1/evidence/VALIDATION_RESULTS.json`
7. trajectory / shock-memory / cross-index / M3 / D4 / D3 / D2 / V19 / D5 与 V2 治理。

## 最新结论

本轮正式验收了此前未回答的 signed-history 风险轴：过去12个有效已完成5m收益的正负结构，是否在 own current E15 I/V 与绝对幅度历史之外增加未来非PnL风险信息。

固定比较：

- C = 84-column own-index D4-style baseline；
- A = C + signed energy / signed absolute-return imbalance；
- M = C + 同窗口、同复杂度 magnitude-only control；
- A/M = 104 columns，同 schema、state interactions、ridge 与 fit rows。

当前 unfinished 5m bar 通过 `shift(1)` 排除。禁止把本研究解释成方向/交易信号。

决定性 run `34681733485`；Validation 前冻结模型 SHA256：

`92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2`。

Validation n=39,770 / 33,950 / 22,310（15/30/60m），coverage 均100%。

关键结果：

- 15m RMS：A/C +0.35160%，A/M +0.19345%；
- 30m RMS：+0.89813%，+0.70577%；
- 60m RMS：**+1.35593%，+1.02822%**；
- 60m tail：+0.54520%，+0.43298%。

但六个 endpoint×horizon joint promotion 全部 false，12项 formal comparison 全部 `supported=false`。

60m RMS 的 pooled 点估计虽然同时越过冻结1%，仍被两道预注册 robustness gate 否决：

- A/C 与 A/M 的 family-adjusted 5-day CI lower 都小于0；
- `000688.SH` 两组 absolute gain 均为负，而 `000852.SH` 均明显为正。

因此这是**跨指数异质的统计提示**，不是稳健共同机制。禁止事后改成“只给中证1000用”。

Tail 的 strongest absolute Brier gain=`0.0004583935491319103`，低于冻结 `0.0005`，且区间跨0。

完整决定性 evidence 已按原字节持久化在 `research/signed_risk_asymmetry_utility_v1/evidence/`；独立 authority validator 已通过。

## Consumer / authority 边界

- 不向 D5 增加 signed-asymmetry field 或 gate；
- V19 frozen；D4/D5 决定不变；
- 不创建新 state/threshold/production field；
- 不查 BlackBox，不读受保护2026逐行数据，不算PnL，不开D6/V20。

## Closed path

禁止用这次 reusable Validation 去做：CSI1000-only rescue、6/24/48-bar、decay/EWMA、skew/downside-count替换、selected state/slot/year/symbol、改 ridge/horizon/bootstrap/gate，或删除 M control。

下一科学题必须是**真正不同的因果风险机制**。若完整仓库审计找不到未回答的独立机制，正确接续点就是 hold / maintain authority，而不是继续制造 signed/window/lag 参数搜索。
