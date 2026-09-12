# One-step degree-trajectory incremental utility V1 — frozen protocol

Date: 2026-09-12  
Source main: `e29c44cd61cdfcead7321a036850d7cd1b33006b`  
Status at freeze: **results-blind for this V1 comparison**. D4 current-degree, M3 refresh, cross-index degree and 12-bar shock-burden results are already known, so 2024–2025 is reusable/adaptive Validation, not fresh OOS.

## 1. Question

D4 and D5 already expose `lag_intensity`, `lag_ratio`, `delta_intensity` and `delta_ratio`, but their contract explicitly says delta fields are descriptive and have no independent incremental-utility acceptance.

This V1 asks a narrower risk-information question:

> After the target index's own current causal E-15 shock intensity / volatility ratio, confirmed-history controls, previous state and recent-shock age are already known, does the **immediately preceding confirmed degree** add practically material future-risk information beyond both (a) the current-level baseline and (b) an equal-complexity two-valid-return-bars-back degree control?

Because current degree is already in C, adding lag-1 degree is a one-to-one raw-information equivalent of adding the current-minus-lag-1 delta. This study therefore tests whether the **one-step trajectory information itself** is useful. It does not claim to validate every possible nonlinear encoding of D5's delta columns.

Risk research only: no direction, trade, PnL, router, position, V20 transition or production authority.

## 2. Distinction from prior work

- D4 proved current E-15 I/V can add utility vs historical/lagged controls for specified endpoints, but delta fields were descriptive only.
- D5 transports lag/delta fields but explicitly does not prove delta predictive utility.
- M3 tests a different fine-scale activity coordinate and its current-vs-lag refresh.
- Cross-index V1 tests the other index's current degree.
- Historical shock-burden V1 tests cumulative 12-bar thresholded memory.

This V1 tests **own-index one-step continuous degree trajectory** and is not a retune/rescue of those paths.

## 3. Frozen causal ancestry

Use the accepted own-index D4-style E-15 reconstruction from:

- `research/cross_index_degree_transfer_utility_v1/run_study.py`, Git blob `b4d3c72e58706b2eb9ae8425f7e7f5439ba002c5`;
- inherited activity/D4-style parent blob `b148d8ccf1d13651434b7b14b42a27dc4b31f5e6`.

For current bar end T, decision time is T-15s. Current I/V use only the latest stable 3-second row at or before decision and confirmed 5m history. Current final close/return/state/future are forbidden.

Baseline C is exactly the inherited 84-column own-index D4-style design: symbol/slot, previous state, recent-shock age bucket, confirmed rolling volatility/background/previous absolute-return history, and current E-15 I/V nonlinear/state interactions.

## 4. Frozen lag-1 degree T

Use the same confirmed-history convention already inherited by D4:

- `lag1_intensity = previous valid completed intraday return absolute value / current confirmed bg48`;
- `lag1_ratio = std of the 12 valid completed intraday returns ending one valid return before current / current confirmed bg48`.

No current final value is needed. With current `I_t,V_t` already present in C:

- `delta1_intensity = I_t - lag1_intensity`;
- `delta1_ratio = V_t - lag1_ratio`.

The pair `(I_t,V_t,lag1_I,lag1_V)` and `(I_t,V_t,delta1_I,delta1_V)` are bijective at the raw-coordinate level. T therefore adds the raw information needed to know the delivered D4/D5 one-step deltas.

T adds a fixed 20-column block from lag-1 degree:

- `u=log1p(lag1_intensity)`;
- `v=log(max(lag1_ratio,1e-12))`;
- `u^2`, `v^2`, `u*v`;
- each of the five terms interacted with the three previous-state indicators.

No thresholding or sign/direction feature.

## 5. Equal-complexity lag-2 control O

Construct the same coordinates two valid completed intraday returns back, always normalized by the **same current confirmed bg48**:

- `lag2_intensity = abs(r_{valid,-2}) / current bg48`;
- `lag2_ratio = std of 12 valid completed intraday returns ending two valid returns before current / current bg48`.

O = C plus the exact same 20-column transform/state-interaction schema as T, replacing lag-1 values with lag-2 values. T and O must have identical feature names/counts/scaling/ridge.

`T vs O` is the critical recency/trajectory comparison. It prevents promotion merely because any extra explicit degree history helps.

## 6. Valid-return clock and availability

The lag clock follows the inherited D4 confirmed-return history:

- valid observations are completed intraday 5m close-to-close returns;
- the first 5m bar of a trading day has no intraday return and does not create a synthetic overnight return;
- lunch/overnight are never turned into returns;
- historical valid returns remain available across session/day gaps as inherited rolling history;
- 2020 supplies warm-up only.

Scientific rows require finite lag-1 and lag-2 coordinates. C/T/O are scored on the exact same cohort.

## 7. Data roles

`DATA_USAGE_POLICY_V2` is binding.

- 2020 warm-up only;
- Development: 2021–2023;
- 2023 forward diagnostic: fit 2021–2022, score 2023;
- reusable Validation: 2024–2025 only;
- 2026 physically excluded;
- BlackBox-V1 not queried.

Subjects only `000688.SH` and `000852.SH`.

## 8. Future-risk endpoints

Exactly inherit the D4 family, current bar excluded and never crossing half-session/lunch/overnight:

1. 15/30/60m `log_future_sigma = log(max(RMS(next H/5 complete 5m returns),1e-12))`;
2. 15/30/60m `future_tail = 1[max(abs(next H/5 returns)) >= 3*bg48_at_decision]`.

Missing future windows are unavailable, never negatives.

## 9. Fixed model family

Models: `C`, `T`, `O`.

All use:

- ridge lambda 0.01;
- Development-column mean / population-SD scaling;
- unpenalized intercept;
- squared loss;
- [0,1] clipping only for tail;
- no hyperparameter/window/threshold/interaction search.

Expected feature counts: C=84, T=104, O=104. T/O schemas must be identical.

## 10. Execution order

1. Verify protocol/parent blobs, input hashes, V2 governance, and physical absence of 2026 data.
2. Build confirmed lag-1/lag-2 coordinates before attaching current E-15 snapshots.
3. Causal tests: perturb current final return/close cannot alter current lag coordinates; future perturbation cannot alter current features; lag-1/delta raw identity reconstructs exactly; T/O schemas identical and C is their exact subset.
4. Fit 2021–2022, score 2023, record all 12 forward comparison signs without changing protocol.
5. Fit final 18 probes on 2021–2023 and freeze exact model bytes.
6. Only after frozen model identity exists may 2024–2025 reusable Validation be opened.

## 11. Formal comparisons and gates

Family = 12:

- `T vs C` and `T vs O`;
- 2 endpoints;
- 3 horizons.

Primary uncertainty:

- both indices on same trading day stay together;
- non-overlapping five-trading-day blocks within year;
- 5000 stratified bootstrap repetitions;
- seed `20260917`;
- Bonferroni two-sided family-12 interval;
- 20-trading-day blocks sensitivity only.

Each individual comparison passes only if all are true:

- Validation n >= 10,000;
- Development n >= 20,000;
- each Validation year and symbol n >= 1,000;
- tail has >=100 positives;
- relative squared-loss reduction >=1.0%;
- tail additionally absolute Brier reduction >=0.0005;
- adjusted 5-day interval lower bound >0;
- 2024, 2025, STAR50 and CSI1000 absolute-gain signs all nonnegative;
- lag-1/lag-2 trajectory coverage among otherwise own-base+future-feasible rows >=95%;
- corresponding 2023 forward Development gain nonnegative.

Endpoint/horizon support requires **both `T vs C` and `T vs O` pass**.

Formal outcomes:

- at least one joint pass: `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`;
- no joint pass: `ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`.

A T-vs-C win alone is insufficient.

## 12. Required diagnostics — not rescue gates

Report:

- lag-1/lag-2/current/delta distributions and correlations;
- trajectory availability coverage;
- gains by symbol/year/previous-state/slot;
- future RMS/tail by deciles of frozen T-vs-C prediction increment;
- observation-age distribution.

No diagnostic may alter the frozen gates.

## 13. Interpretation / stopping rule

Support would mean only that one-step own-index degree trajectory carries useful additional risk information for specified endpoints. It would not automatically authorize D5 promotion, a V19 change, or production use; exact consumer-field admission remains separate.

A negative result closes this fixed lag-1 vs lag-2 one-step trajectory specification. Do not rescue it by testing lag3/lag4, smoothing/decay, alternative normalizers, selected states/times/symbols, moved thresholds, altered ridge/horizons, or dropping O on the same reusable Validation.

Always record:

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
