# Cross-index current-degree transfer utility V1 — frozen protocol

Date: 2026-09-12  
Source main: `165cfb0a56aaf3ac7c616f9d2eadd27501f2e0e6`  
Status at freeze: **results-blind for this V1 comparison**. Prior cross-index first-shock/reversal studies, D4 own-index continuous-risk results, V19 state results, and reusable 2024–2025 Validation history are already known. Therefore the coming 2024–2025 evaluation is adaptive reusable Validation, never fresh OOS.

## 1. Question

At the same E-15 decision time, after a target index's own causal history and own current shock-intensity / volatility-ratio coordinates are already known, does the **other index's current causal risk degree** add practically material information about the target index's future risk?

The experiment is bidirectional:

- CSI1000 current degree -> STAR50 future risk;
- STAR50 current degree -> CSI1000 future risk.

This is a non-PnL risk-information study. It does not test relative-value mean reversion, direction, first-shock prediction, trading, routing, position sizing or production.

## 2. Why this is not a repeat of earlier cross-index work

The frozen 2026-09-09 `rmr_cross_index_relative_dislocation_v1` tested whether a trailing-OLS STAR50-vs-CSI1000 residual displacement mean-reverted over the next 15 minutes. It rejected that mean-reversion mechanism and did not condition on or compare against D4-style own-index E-15 I/V.

Earlier cross-index risk-gate work studied event overlap / warning structure rather than the fixed incremental predictive comparison below.

V1 therefore asks a distinct question: **incremental future-risk information from the contemporaneous other-index causal degree after own-index current degree is already in the model**.

## 3. Frozen ancestry and causal coordinates

The own-index baseline construction is frozen to the already accepted Activity-degree V1 reconstruction of D4-style E-15 I/V, whose runner on source main has Git blob `b148d8ccf1d13651434b7b14b42a27dc4b31f5e6`.

At target bar end `T`, decision time is `T-15s`.

For each index independently:

- use the latest 3-second observation at or before decision time that is still inside the current native 5-minute bar;
- never use the final current-bar close;
- `partial_return = log(partial_price / previous_confirmed_5m_close)`;
- `bg48` uses the previous 48 valid confirmed 5-minute returns and excludes current partial return;
- `I_t = abs(partial_return)/bg48`;
- `V_t = std(previous 11 valid confirmed 5-minute returns + partial_return, ddof=0)/bg48`.

No maximum observation-age filter is added beyond the requirement that the selected observation belongs to the current native bar. Observation age is reported descriptively. Missing current-bar observations stay unavailable.

The target's confirmed-history baseline remains:

- symbol and 5-minute slot;
- previous confirmed state;
- recent confirmed shock-age bucket;
- confirmed-history `rms3/rms6/rms12/rms48`, `bg48`, and previous absolute return;
- target current E-15 I/V with the same fixed quadratic/cross expansion and previous-state interactions as D4-style C.

V19 itself is not changed and no new state is created.

## 4. Fixed other-index lag control

To distinguish **current cross-index refresh** from merely giving the model more cross-index numeric history, define a complexity-matched lag-only other-index control using only confirmed returns strictly before the target current bar:

- `I_other_lag = abs(other most recent confirmed valid 5m return) / other bg48`;
- `V_other_lag = std(other previous 12 confirmed valid 5m returns, ddof=0) / other bg48`.

This follows the logic of D4's lag-only complexity control. It never uses the other index's current partial price.

## 5. Data roles

Repository `DATA_USAGE_POLICY_V2` governs the study.

- 2020: warm-up only.
- Development: 2021–2023.
- Forward Development diagnostic: fit 2021–2022, score 2023.
- Reusable Validation: 2024–2025 only; not fresh/blind OOS.
- 2026: physically excluded from the workflow.
- BlackBox-V1: not queried.

Subjects are only `000688.SH` and `000852.SH`. Inputs are the repository-sealed 5-minute and 3-second index carriers already used by prior risk research.

## 6. Paired cohort

For a target E-15 row to enter, all of the following must hold:

- target own confirmed-history baseline available;
- target current E-15 I/V available;
- other index current E-15 I/V available at the identical decision timestamp;
- other index lag-only I/V available;
- target and other rows share the same trading day, native 5-minute bar end and decision time;
- target future endpoint is feasible without crossing half-session, lunch, overnight, day or symbol boundary.

No fallback to an older other-index current snapshot is allowed. Missing rows remain missing.

The scientific comparison uses exactly the same rows for all three models for each horizon/endpoint.

## 7. Future-risk endpoints

Exactly the D4 endpoint family is used for the **target** index at 15/30/60 minutes, excluding the current 5-minute bar:

1. `log_future_sigma = log(max(RMS(next H/5 complete target 5m close-to-close returns), 1e-12))`;
2. `future_tail = 1[max(abs(next H/5 target returns)) >= 3*target_bg48_at_decision]`.

A missing future window is unavailable, not a negative label.

## 8. Fixed information sets

All models use ridge lambda `0.01`, Development-column mean / population-standard-deviation scaling, unpenalized intercept, squared loss, and `[0,1]` clipping only for the binary endpoint. No hyperparameter search.

### C — own-index D4-style baseline

C is the target own-index D4-style information set described in section 3.

### X — current other-index augmentation

X = C plus the following five transforms of the **other index current E-15** coordinates:

- `u = log1p(I_other_current)`;
- `v = log(max(V_other_current,1e-12))`;
- `u^2`;
- `v^2`;
- `u*v`.

Because transfer may differ by target index, each of those five terms is additionally interacted with the two frozen target-symbol indicators. Thus the cross-index block has exactly 15 columns: five pooled terms plus ten target-symbol interaction terms.

No outcome-driven interaction search is allowed.

### L — equal-complexity lag-only other-index control

L = C plus **the identical 15-column transform/interactions**, replacing current other-index I/V with `I_other_lag / V_other_lag` from confirmed other-index history only.

X and L must have identical feature names, counts, transforms, standardization and ridge penalty. `X vs L` is the critical refresh comparison.

## 9. Execution order

1. Verify source identities, governance and physical data boundary.
2. Build target and other-index E-15 coordinates without future labels.
3. Verify exact same-time pairing and that current final closes cannot enter current coordinates.
4. Run deterministic invariants: future-price perturbation cannot alter any current feature; swapping current other-index partial values changes X inputs but cannot change C/L inputs; X/L schemas are identical.
5. Fit C/X/L on 2021–2022 and score 2023. Record all twelve comparison signs without changing the protocol.
6. Fit final 18 probes (3 models × 2 endpoints × 3 horizons) on 2021–2023 and freeze exact model bytes before Validation.
7. Only after frozen-model identity is sealed, score unchanged models on 2024–2025 reusable Validation.

## 10. Fixed comparisons, uncertainty and practical gates

Family = 12 comparisons:

- `X vs C` and `X vs L`;
- 2 endpoints;
- 3 horizons.

Primary uncertainty follows D4:

- same-day observations from both target indices remain together;
- non-overlapping five-trading-day blocks within year;
- 5000 stratified bootstrap repetitions;
- seed `20260915`;
- Bonferroni two-sided quantile `0.05/(2*12)`;
- fixed 20-trading-day blocks are sensitivity only.

Each individual comparison passes only if all are true:

- Validation n >= 10,000;
- Development n >= 20,000;
- each Validation year and each target symbol n >= 1,000;
- tail endpoint has >=100 positive Validation events;
- relative squared-loss reduction >=1.0%;
- tail endpoint additionally has absolute Brier reduction >=0.0005;
- adjusted 5-day block interval lower bound >0;
- 2024, 2025, STAR50 and CSI1000 absolute-gain signs are all nonnegative;
- paired current/lag-other coverage among otherwise target-base+future-feasible rows >=95%;
- corresponding 2023 forward Development gain is nonnegative.

An endpoint/horizon is supported only when **both `X vs C` and `X vs L` pass**.

Formal outcome:

- at least one endpoint/horizon jointly passes: `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`;
- none jointly pass: `CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`.

A win over C alone is insufficient because it cannot rule out generic extra cross-index model capacity/history.

## 11. Required descriptive diagnostics — never rescue gates

Report:

- contemporaneous own/other I and V correlations;
- current-other vs lag-other correlations;
- observation-age distribution for both indices at paired E-15 rows;
- comparison gains by target symbol, year, previous target state and decision slot;
- target future RMS/tail by deciles of the frozen X-vs-C prediction increment;
- counts excluded by target history, current target snapshot, current other snapshot, lag-other availability and future-window boundary.

These may explain a result but cannot change the gates.

## 12. Interpretation boundaries

Even a supported result means only that the other index's contemporaneous causal degree is a useful additional **risk attribute** for specified endpoints under reusable Validation. It does not authorize a cross-index trade, relative-value rule, direction signal, new V19 state, D5 consumer field or production field.

A negative result closes this fixed cross-index current-degree transfer specification; do not rescue it by post-hoc lag choice, target direction, threshold, horizon, nonlinear family, state filter or sample deletion.

Always record:

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
