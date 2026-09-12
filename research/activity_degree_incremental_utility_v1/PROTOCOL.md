# Activity-degree incremental utility V1 — frozen protocol

Date: 2026-09-12  
Source main: `a26f4a302d5f73486b3b0cd04da50e382020d28f`  
Status at freeze: **results-blind for this V1 incremental comparison**. Earlier M3 Development/structural Validation findings and D4 I/V utility results are already known and must be disclosed; therefore the coming 2024–2025 evaluation is reusable/adaptive Validation, never fresh OOS.

Pre-outcome source-audit corrections: (1) the original V9 E15 selector uses the latest same-bar 3s observation at or before the checkpoint and does not itself impose a <=3 second staleness gate; the <=3 second endpoint rule belongs to the inherited strict M3 grid. Because the scientific cohort below requires a complete strict M3 path including the decision-time endpoint, included rows still have a <=3 second decision endpoint. (2) the explicitly listed M3 augmentation block contains 8 columns, not 6: `m`, `m^2`, plus each term interacted with the 3 previous-state indicators. No model term, gate, threshold, horizon, target or cohort rule changed in these corrections.

## 1. Question

On the already-defined low-amplitude surface, does a strictly causal 15-second activity-surprise coordinate add practically material future-risk information **after** the D4-style current E15 shock-intensity / volatility-ratio information set is already available?

This is a non-PnL risk-information study. It does not create a state threshold, first-shock predictor, direction signal, trading rule, position, payoff router or production model.

## 2. Frozen ancestry and definitions

M3 ancestry is frozen to `docs/research/fine_activity_future_risk_v1/run_study.py` Git blob `2a5f607db1451a2e4576a9bc0940b67ac02f0d2e` and its protocol blob `d43f5b4a2c0395d1d022a3fb5e10c58dce08de0c`:

- strict 15-second grid;
- each endpoint must use the latest source observation no more than 3 seconds old;
- no interpolation or zero fill;
- no crossed source gap >3 seconds;
- `A5 = sqrt(mean(r_15s^2))` over the previous five physical minutes;
- clock-matched expanding `median(log A5)` / `1.4826*MAD`, floor `1e-8`, minimum 60 strictly earlier observations;
- `M3 = (log(A5)-center)/scale`.

The clock is adapted only from one-minute decision slots to the actual E15 5m checkpoint: index × half-session × exact 5m bar slot. Formula, strictness and prior-only standardization do not change.

D4-style current continuous coordinates are frozen to the V9 partial-state construction (`run_v9.py` Git blob `ae2a7e095df58692ef9df0dfee5856cac727ca44`) and D4 design semantics:

- decision time = `bar_end - 15 seconds`;
- V9 selects the latest 3s price at or before decision time inside the current native 5m bar, without a separate V9 staleness cutoff;
- this V1 cohort additionally requires the inherited strict M3 path, so its decision-time grid endpoint is necessarily no more than 3 seconds old;
- `partial_return = log(partial_price / previous_confirmed_5m_close)`;
- `bg48` uses the previous 48 valid confirmed 5m returns, excluding current partial return;
- `I_t = abs(partial_return)/bg48`;
- `V_t = std(previous 11 valid confirmed 5m returns + partial_return, ddof=0)/bg48`.

The finalized 5m state machine remains the frozen 3σ / 1.50 / 1.10 mechanism. The model receives the **previous confirmed** state and recent confirmed shock age only; current/final future state is never a design input.

## 3. Data roles

Repository `DATA_USAGE_POLICY_V2` governs this study.

- 2020: warm-up only for 5m history.
- Development: 2021–2023. M3 becomes usable only after its own 60-observation clock-matched causal reference exists; no imputation.
- Forward Development diagnostic: fit on admissible 2021–2022 rows, score 2023 only.
- Reusable Validation: 2024–2025 only. It has already been reused by prior studies; it is not fresh/blind OOS.
- 2026: physically excluded from the workflow.
- BlackBox-V1: not queried.

Subjects are only `000688.SH` and `000852.SH`. Inputs are the repository-sealed 5m and 3s index carriers. No options/futures or other instruments.

## 4. Frozen analysis surface and cohort

The M3 ancestry is not generalized. A row enters the scientific cohort only when all are true:

- current E15 partial I/V is available;
- current M3 and previous same-half-session E15 M3 are both available;
- the strict five-minute M3 price path is complete;
- path range `pre5m_range_bp < 30`;
- all D4-style historical baseline fields are available;
- the future endpoint is feasible within the same trading half-session/day under the 5m grid;
- no current finalized 5m return or future field enters design.

There is no stale-row deletion beyond the inherited <=3-second grid-endpoint requirement needed to define the strict M3 path. Missing rows remain missing; no fallback to older available samples for M3.

## 5. Fixed future-risk endpoints

Exactly the D4 endpoint family is used at horizons 15/30/60 minutes, current 5m bar excluded:

1. `log_future_sigma = log(max(RMS(next H/5 complete 5m close-to-close returns), 1e-12))`.
2. `future_tail = 1[max(abs(next H/5 returns)) >= 3*bg48_at_decision]`.

Future windows cannot cross lunch, overnight, symbol, or trading day. A missing future window is unavailable, not a negative label.

## 6. Fixed information sets

All models use ridge lambda `0.01`, Development-column mean / population-standard-deviation scaling, unpenalized intercept, squared loss, and `[0,1]` clipping only for binary predictions. No hyperparameter search.

### C — D4-style current I/V baseline

C uses the D3/D4 information schema reconstructed from sealed 5m/3s carriers:

- symbol and 5m decision slot one-hot;
- previous confirmed state one-hot;
- recent confirmed shock-age bucket `{NONE, LT15, M15_25, M30_40, GE45}`;
- `log_rms3`, `log_rms6`, `log_rms12`, `log_rms48`, `log_bg48`, `log1p(last_abs/bg48)` from confirmed history only;
- `a=log1p(I_t)`, `b=log(max(V_t,1e-12))`, `a^2`, `b^2`, `a*b`;
- each of those five current numeric terms interacted with previous confirmed state.

This study refits C on its M3-admissible cohort; it does not claim byte-identical reuse of the unavailable chat-only D4 prediction vectors. The scientific claim is incremental information beyond the **D4-style information set**, not a retroactive modification of D4.

### A — current activity-surprise augmentation

A = C plus the frozen 8-column M3 block:

- `m = M3_current`;
- `m^2`;
- `m` interacted with each previous confirmed state;
- `m^2` interacted with each previous confirmed state.

No M3 bands are model inputs. No clipping, threshold search or interaction search is allowed.

### N — equal-complexity lagged-M3 control

N = C plus exactly the same 8-column M3 block, replacing `M3_current` with `M3_lag`, where `M3_lag` is the immediately preceding E15 M3 in the same half-session and is therefore known before the current native bar.

A and N have identical column counts, transforms, ridge rule and base information. `A vs N` asks whether the **current fine-scale refresh** contributes beyond merely giving the model more nonlinear fine-activity capacity.

## 7. Execution order

1. Verify frozen source identities, physical data boundary and governance.
2. Build causal 5m historical state/background features and strict E15 I/V/M3 rows without labels.
3. Run deterministic prefix/causality checks: future-price perturbations must not change any current feature; current-final close must not enter E15 I/V/M3.
4. Fit C/A/N on 2021–2022 and score 2023. Record all 12 `A vs C/N × endpoint × horizon` signs. Do not change the specification from those signs.
5. Fit the final 18 probes (3 models × 2 endpoints × 3 horizons) on 2021–2023, write model identity/feature schemas/normalization parameters, and freeze them before reading 2024–2025 labels.
6. Only after the model freeze commit/run phase, evaluate 2024–2025 reusable Validation with unchanged models.

The workflow may implement fit and validation as separate Action jobs/runs. Validation must verify exact frozen model bytes before scoring.

## 8. Fixed uncertainty and gates

Family = 12 comparisons: `A vs C` and `A vs N` × 2 endpoints × 3 horizons.

Primary uncertainty is the D4 scheme: same-day two-index observations grouped into non-overlapping five-trading-day blocks within year; 5000 stratified bootstrap repetitions; seed `20260914`; Bonferroni two-sided quantile `0.05/(2*12)`. A fixed 20-trading-day block is sensitivity only.

Each individual comparison passes only if all are true:

- Validation n >= 10,000;
- Development n >= 20,000;
- each Validation year and each symbol n >= 1,000;
- tail endpoint has >=100 positive Validation events;
- relative squared-loss reduction >=1.0%;
- tail endpoint additionally has absolute Brier reduction >=0.0005;
- adjusted 5-day block interval lower bound >0;
- 2024, 2025, STAR50 and CSI1000 absolute-gain signs all nonnegative;
- feasible-row coverage after base historical availability >=95%;
- corresponding 2023 forward Development gain is nonnegative.

An endpoint/horizon is supported only when **both A vs C and A vs N pass**. A win over C alone cannot rule out added model-capacity/fine-history explanations.

Formal outcome:

- at least one endpoint/horizon jointly passes: `CURRENT_M3_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`;
- none jointly pass: `CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`.

Partial passes are listed exactly and never generalized. Failing the 1% practical gate is failure even if confidence intervals are positive.

## 9. Required descriptive checks, never rescue gates

Report:

- current/lag M3 correlation and availability;
- M3 deciles versus future RMS/tail within C-prediction deciles;
- result slices by current previous-confirmed state, year, symbol and E15 slot;
- current M3 versus raw I/V correlations;
- counts excluded by strict 3s path, <30bp surface, missing causal reference, lag requirement and future-window boundary.

These descriptions cannot rescue a failed primary gate or create thresholds.

## 10. Interpretation boundaries

This study is adaptive: M3 Development and risk-coordinate 2024/2025 structure are already known, and D4 2024/2025 I/V utility is already known. Therefore even a strong result is reusable Validation evidence, not fresh independent confirmation.

It does not change V19, D3, D4 or D5 decisions. It does not authorize M3 as a state, trading gate or production field. No 2026/BlackBox rows, PnL, direction, position sizing, router, options/futures, external consumer acceptance or production authority are permitted.

Always record:

`validation_reused=true`; `fresh_oos=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
