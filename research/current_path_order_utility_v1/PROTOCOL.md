# Current E15 path-order incremental utility V1 — frozen protocol

Date: 2026-09-12  
Source main: `b9a6a47b2aca8ea9dddec1aab69c19ae0ae92311`

## Scientific question

At the E-15 decision checkpoint of the current native 5-minute bar, does the **time ordering of the already-observed intrabar path** add practically material causal information about future non-PnL risk after the established own-index current intensity / volatility-ratio information, current fine-activity amplitude, and current intrabar magnitude-shape are already known?

This is a direction-invariant risk-information study. It does not predict return sign and must not create a trading direction, position, payoff rule, first-shock predictor, state threshold, router, or production field.

This question is scientifically distinct from:

- D4 current E15 intensity / volatility-ratio utility;
- M3 activity-degree V1, which reduces the strict 15-second path to RMS activity amplitude and contains no path-order feature;
- signed-risk asymmetry V1, which used the previous 12 **completed 5-minute returns** and discarded their ordering;
- historical shock burden and one-step degree trajectory;
- old `wave_shape` / `cross_scale_root_cause` strategy-PnL analyses, whose path-shape evidence was posterior/full-cycle and not a causal E15 future-risk utility test.

Repository audit before freeze found no current-main causal future-risk utility study of intrabar path ordering, adjacent-return dependence, sign-change order, or range-to-total-variation at E15.

## Frozen source ancestry

The strict 15-second sampling, historical baseline, E15 current I/V construction, M3 standardization, future targets, and session rules inherit from:

`research/activity_degree_incremental_utility_v1/run_study.py`

Frozen parent Git blob at protocol freeze:

`b148d8ccf1d13651434b7b14b42a27dc4b31f5e6`

The parent itself freezes the V9 partial-state construction and M3 ancestry. This V1 does **not** reinterpret the old M3 promotion decision; current M3 is used here as a nuisance/amplitude control.

## Causal current-bar path

Decision time is exactly:

`bar_end - 15 seconds`.

Use the parent's strict 15-second source grid:

- each grid endpoint uses the latest source observation no more than 3 seconds old;
- no interpolation;
- no zero fill;
- no crossed source gap >3 seconds.

For the current native 5-minute bar, define the path from its bar start through E15. This gives exactly **19 consecutive 15-second returns** and 20 path prices.

Only observations at or before E15 are allowed. The final 15 seconds of the current 5-minute bar, the finalized current 5-minute close/return/state, and every future bar are forbidden inputs.

The immediately preceding E15 path-order block is the identically defined 19-return path at the previous 5-minute E15 checkpoint in the **same half-session**. It is used only as an equal-complexity lag control. No overnight or lunch carry is allowed for this lag.

## Frozen current magnitude-shape controls

Let the current 19 strict 15-second returns be `r_1 ... r_19`, in bp. Define two permutation-invariant, global-sign-invariant current magnitude-shape coordinates:

1. `L1L2_19 = sum(abs(r_i)) / (sqrt(19) * sqrt(sum(r_i^2)))`
2. `MAXL2_19 = max(abs(r_i)) / sqrt(sum(r_i^2))`

These are nuisance controls. They ensure that a path-order result cannot be explained merely by giving the model current intrabar concentration/dispersion information beyond M3 RMS amplitude.

If `sum(r_i^2) <= 0` or any required return is unavailable, the row is unavailable rather than imputed.

## Frozen order-sensitive coordinates

Using the same current 19 returns, define:

1. **range-to-total-variation**

   Start cumulative displacement at zero and let `c_k = sum_{i=1..k} r_i`.

   `RTV19 = (max(0,c_1,...,c_19) - min(0,c_1,...,c_19)) / sum(abs(r_i))`

   This lies in `[0,1]` when total variation is positive. It changes when the same returns are reordered, while remaining invariant to a global sign flip.

2. **adjacent-product persistence**

   `AP19 = sum_{i=2..19}(r_i * r_{i-1}) / sum_{i=1..19}(r_i^2)`

   This measures local continuation versus reversal ordering, is invariant to a global sign flip, and is bounded in `[-1,1]` up to floating tolerance.

No return-sign direction is exposed as a standalone model input. The study asks whether order/persistence of already-observed movement matters for future risk, not whether the market will rise or fall.

The lag-control coordinates `RTV19_lag` and `AP19_lag` are the identical pair from the previous E15 checkpoint in the same half-session.

## Frozen models

All models use ridge lambda `0.01`, Development-column mean/population-standard-deviation scaling, unpenalized intercept, squared loss, and `[0,1]` clipping only for binary predictions.

### B — strong current amplitude/magnitude baseline

B contains:

1. the parent D4-style C information set:
   - symbol and fixed 5m slot one-hot;
   - previous confirmed state;
   - recent confirmed shock-age bucket;
   - confirmed-history `log_rms3/6/12/48`, `log_bg48`, `log1p(last_abs/bg48)`;
   - current E15 I/V nonlinear block and previous-state interactions;
2. the parent **current M3** nonlinear/state-interaction block (`m`, `m^2`, and each interacted with previous confirmed state);
3. the current `L1L2_19` / `MAXL2_19` magnitude-shape block.

The two magnitude coordinates `(x,y)` expand identically to:

- `x`, `y`, `x^2`, `y^2`, `x*y`;
- each of those five terms interacted with `NORMAL`, `UNSAFE`, `RECOVERING` previous confirmed state.

This adds exactly 20 columns beyond the parent current-M3 model.

### O — current path-order candidate

O = B + current `RTV19` / `AP19`, expanded by the same 20-column transform/state-interaction schema.

### L — equal-complexity lagged-order control

L = B + `RTV19_lag` / `AP19_lag`, expanded by exactly the same 20-column schema.

O and L must have identical column counts, transforms, ridge penalty, and fitting rows. O is promotable only if it beats both B and L; beating B alone is insufficient because it could reflect added model capacity or persistent morphology rather than current path-order refresh.

Expected inherited parent counts are 84 columns for D4-style C and 92 for parent current-M3 A. Therefore B is expected to have 112 columns and O/L 132 columns. Any count drift is an execution failure, not a reason to edit the protocol.

## Population and cohort

Subjects:

- `000688.SH`
- `000852.SH`

A row enters the scientific cohort only when:

- D4-style current E15 I/V and confirmed-history baseline fields are available;
- current M3 is available from its strictly prior clock-matched reference;
- the current 19-return E15 path is strict and complete;
- current magnitude and order coordinates are finite;
- the previous E15 checkpoint in the same half-session has strict complete order coordinates for L;
- the future endpoint is feasible within the same half-session/day.

Unlike the old M3 V1 scientific cohort, **there is no `<30bp` low-amplitude surface restriction**. That restriction belonged to the earlier M3 question. Here current M3 and current magnitude shape are controls, and current path ordering is tested across all strictly observed E15 paths. No amplitude threshold or subgroup may be added after Validation is opened.

Coverage is measured against otherwise-feasible B rows before requiring the lag-order control. Missing/strict-path failures remain unavailable; no fallback or zero fill.

## Data roles and isolation

- pre-2021: warm-up only;
- Development: 2021-01-01 through 2023-12-31;
- forward Development diagnostic: fit 2021-2022, score 2023;
- final frozen fit: 2021-2023 only;
- reusable Validation: 2024-2025 only;
- 2026 detail must not be read;
- BlackBox-V1 must not be queried.

The exact final model bytes must be frozen before Validation scoring. Validation is reusable/adaptive evidence, not fresh OOS.

## Frozen endpoints

Exactly the inherited non-PnL endpoints at 15/30/60 minutes, excluding the current 5-minute bar:

- `log_future_sigma`;
- `future_tail`.

Future windows must not cross lunch, overnight, symbol, or trading day.

## Frozen comparisons

For each horizon × endpoint, O must pass both:

- `O vs B` — current path order versus the strong current amplitude/magnitude baseline;
- `O vs L` — current path order versus the equal-complexity lagged-order control.

An endpoint/horizon is supported only when both comparisons pass every frozen gate.

## Frozen gates

For each of the 12 comparisons:

1. Validation `n >= 10,000`, Development fit `n >= 20,000`, every annual/symbol slice `n >= 1,000`.
2. Tail endpoint has at least 100 positive events.
3. Relative squared-loss improvement >= **1.00%**.
4. Tail additionally has absolute Brier improvement >= **0.0005**.
5. Family-adjusted 5-trading-day block-bootstrap interval for absolute gain has lower bound >0.
6. 2024, 2025, STAR50, and CSI1000 absolute-gain signs are all nonnegative.
7. Final cohort coverage versus otherwise-feasible B rows >=95%.
8. Corresponding 2023 Development-forward absolute gain is nonnegative.

Bootstrap repetitions: 5000.  
Family size: 12 comparisons.  
A fixed 20-trading-day block interval is sensitivity only and cannot promote a result.

## Frozen decision

If at least one horizon × endpoint jointly passes O vs B and O vs L:

`CURRENT_E15_PATH_ORDER_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`

Otherwise:

`CURRENT_E15_PATH_ORDER_INCREMENTAL_UTILITY_NOT_SUPPORTED`

A statistical hint that fails a practical or robustness gate remains unsupported.

## Mandatory causal / identity checks before outcomes

At minimum verify:

- current path uses exactly 19 strict 15-second returns ending at E15;
- perturbing the final 15 seconds / finalized current close cannot change current features;
- future appends cannot change historical feature prefixes;
- global sign flip leaves magnitude and order coordinates unchanged;
- permutation of the same current 19 returns leaves magnitude controls, endpoint net move, and RMS amplitude unchanged while changing at least one order coordinate on a nondegenerate fixture;
- O/L schemas and column counts are exactly complexity matched;
- B/O/L expected counts are 112/132/132.

## Post-result discipline

After Validation is opened, this V1 may not be rescued by:

- switching from 15-second to 3-second order features;
- changing 19-return current-bar path length;
- replacing `RTV19/AP19` with sign-change counts, entropy, Hurst, path efficiency, skewness, alternative autocorrelation, drawdown shape, or other morphology summaries;
- adding amplitude/range/state/slot/year/symbol filters;
- selecting only one index;
- changing ridge lambda, horizons, bootstrap family, practical gates, or magnitude/lag controls;
- turning morphology into a direction/trading/PnL rule.

Any future path study must pose a genuinely distinct preregistered mechanism, not search around this result.

## Governance outputs

Always record:

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.

No supported result automatically changes V19, D4, D5, M3, or signed-asymmetry decisions. Consumer promotion requires a separate explicit authority decision.
