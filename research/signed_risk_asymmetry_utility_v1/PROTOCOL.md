# Signed-risk asymmetry incremental utility V1 — frozen protocol

Date: 2026-09-12
Source main: `291d04861e85492337a2f86f1fade0419254972d`

## Scientific question

Does the **sign structure of recent completed returns** add practical causal information about future non-PnL risk after the already-supported own-index current E15 continuous risk coordinates and the established absolute-volatility history are known?

This is a bottom-layer risk-information study. Historical return sign is used only to describe the shape of already-observed risk. It must not produce trade direction, sign-flip logic, position, sizing, payoff, PnL, routing, or production authority.

This question is distinct from:

- D3 state utility;
- D4 current E15 intensity / volatility-ratio utility;
- M3 fine-activity amplitude;
- cross-index transfer;
- historical shock-count / excess burden;
- one-step degree trajectory / delta;
- the old HighVol trading/PnL regime studies.

Repository audit before freezing found no formal semivariance/downside/upside/signed-return/skew/return-sign incremental-utility study on current main. The frozen risk-coordinate study uses RMS/activity surprise and relative volatility, not return sign.

## Causal observation rule

For a decision row at current E15, the asymmetry window is the **previous 12 valid completed 5-minute returns of the same index**.

The current unfinished 5-minute bar is excluded. Implementation must construct the window from final 5-minute returns only after shifting by one valid return bar. Missing/invalid rows do not become zero and do not create sign observations.

The 12-bar window is a valid-trading-bar window, not a natural-clock 60-minute promise; it uses the same completed-history convention as the inherited historical features. No future bar, future state, episode end, or future label may enter the feature block.

## Frozen signed coordinates

For previous completed returns `r_1 ... r_12` in bp, define:

1. **signed energy imbalance**

   `SEI12 = sum(r_i * abs(r_i)) / sum(r_i^2)`

   This is signed squared-return energy normalized by total squared-return energy and lies in [-1, 1] when the denominator is positive.

2. **signed absolute-return imbalance**

   `SAI12 = sum(r_i) / sum(abs(r_i))`

   This is net signed movement normalized by total absolute movement and lies in [-1, 1] when the denominator is positive.

If a denominator is not strictly positive, the corresponding row is unavailable rather than imputed.

No alternative lookback, exponential decay, downside-only threshold, skewness definition, state-filtered window, or symbol-specific form may be introduced after Validation is seen.

## Equal-complexity magnitude-only control

To separate sign-specific information from the generic benefit of adding two recent-history summaries, construct two scale-free coordinates from the **same previous 12 completed returns** while discarding sign:

1. `L1L2_12 = sum(abs(r_i)) / (sqrt(12) * sqrt(sum(r_i^2)))`
2. `MAXL2_12 = max(abs(r_i)) / sqrt(sum(r_i^2))`

These describe magnitude shape/concentration only. They use the same rows, same availability rule, same number of raw coordinates, same nonlinear expansion, same state interactions, same ridge penalty, and same fitting samples as the signed block.

## Frozen models

All models inherit the D4-style own-index current E15 baseline `C` exactly as exposed by the frozen degree-trajectory parent runner. It includes the established current own-index intensity / volatility-ratio information and historical controls; it does not receive unfinished-bar final sign.

- `C`: inherited own-index baseline only.
- `A`: `C` + the two signed asymmetry coordinates `SEI12`, `SAI12`.
- `M`: `C` + the two magnitude-only control coordinates `L1L2_12`, `MAXL2_12`.

For both `A` and `M`, the two raw coordinates `(x, y)` expand identically to:

- `x`
- `y`
- `x^2`
- `y^2`
- `x*y`

Each of the five terms also receives an interaction with each previous confirmed state `NORMAL`, `UNSAFE`, `RECOVERING`.

Therefore each added block has exactly 20 columns. `A` and `M` must have identical design dimensions and regularization. The inherited `C` feature count is expected to be 84, and `A/M` are expected to be 104.

Ridge lambda is frozen at `0.01`.

## Population and split

Subjects:

- `000688.SH`
- `000852.SH`

Historical/fitting boundary:

- pre-2021: warm-up only;
- Development: 2021-01-01 through 2023-12-31;
- forward Development diagnostic: fit 2021-2022, score 2023;
- final frozen fit: 2021-2023 only;
- reusable Validation: 2024 and 2025 only for this realtime-3s-compatible study;
- 2026 must not be read;
- BlackBox-V1 must not be queried.

The exact model bytes must be frozen before Validation scoring. Validation is reusable/adaptive evidence, not fresh OOS.

## Frozen endpoints

For horizons 15, 30, and 60 minutes, use the inherited non-PnL targets:

- `log_future_sigma`;
- `future_tail`.

Current bar is excluded from the future target exactly as in the parent utility framework. Lunch/overnight crossing behavior is inherited and must not be loosened.

## Frozen comparisons

For every horizon × endpoint, `A` must pass both:

- `A vs C` — sign block versus the established baseline;
- `A vs M` — sign block versus the equal-complexity magnitude-only history block.

An endpoint/horizon is supported only if **both** comparisons pass every gate below.

## Frozen gates

For each comparison:

1. Validation `n >= 10,000`, Development fit `n >= 20,000`, and every annual/symbol slice `n >= 1,000`.
2. Tail endpoint has at least 100 positive events.
3. Relative MSE improvement is at least **1.00%**.
4. For tail, absolute Brier improvement is also at least **0.0005**.
5. Family-adjusted 5-trading-day block-bootstrap interval for absolute gain has lower bound > 0.
6. Every annual and symbol slice has nonnegative absolute gain.
7. Availability coverage versus otherwise-feasible inherited baseline rows is at least 95%.
8. The corresponding 2023 Development-forward absolute gain is nonnegative.

Bootstrap repetitions: 5000.
Family size for multiplicity adjustment: 12 comparisons.
A 20-trading-day block interval is sensitivity output only and is not a promotion gate.

## Frozen decision

If at least one horizon × endpoint passes jointly against both `C` and `M`:

`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`

Otherwise:

`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`

A statistical hint below the practical gates must be reported as such and must not be promoted.

## Post-result discipline

After Validation is opened, this V1 specification may not be rescued by:

- trying 6/24/48-bar windows;
- changing to exponential decay;
- replacing the signed coordinates with skewness or thresholded downside counts;
- changing state/symbol/horizon filters;
- lowering the 1% or 0.0005 practical gates;
- changing ridge lambda;
- selecting only favorable years/symbols.

Any later study would require a scientifically distinct preregistered question, not a rescue of this result.

## Governance outputs

Always record:

- `validation_reused=true`;
- `fresh_oos=false`;
- `read_2026=false`;
- `blackbox_queried=false`;
- `pnl_computed=false`;
- `candidate_nominated=false` unless a later authority process explicitly changes it;
- `production_authority=false`;
- `v20_started=false`;
- `d6_started=false`.

No supported result in this study automatically changes V19 or D5 consumer fields. Consumer promotion requires a separate explicit authority decision.