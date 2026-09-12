# Cross-index residual dislocation incremental utility V1 — frozen protocol

Date: 2026-09-12
Source main: `e30a0eb0e0884a569110c8819fb4b2696bb9dd29`

## 1. Scientific question

At the E15 decision time, after the target index's own D4-style current continuous risk coordinates **and** the other index's contemporaneous current I/V coordinates are already known, does a **dynamic cross-index relationship residual dislocation** add practically material information about the target index's future non-PnL risk?

This is not a relative-value, convergence, direction, trade, routing, position or PnL study.

## 2. Why this is a distinct preregisterable mechanism

The 2026-09-09 frozen `rmr_cross_index_relative_dislocation_v1` defined a trailing OLS relationship between STAR50 and CSI1000 and tested whether a signed residual displacement mean-reverted. That directional outcome is outside the current risk-attribute program.

The later `cross_index_degree_transfer_utility_v1` tested the other index's current E15 `I/V` degree after own-index `I/V`, and explicitly did **not** test relative-value residual geometry.

This V1 reuses only the pre-existing causal idea of **relationship residual dislocation**, removes its rich/cheap sign, moves it onto the current program's E15/5m information set, and asks only about future risk. The mechanism identity exists independently of the just-completed intrabar-order Validation and is not selected from that result.

Signed asymmetry, multiscale-volatility rescue, intrabar-order rescue, M3 refresh, shock-memory and trajectory specifications remain closed.

## 3. Causal current coordinates

Subjects:

- `000688.SH`
- `000852.SH`

For every native 5-minute bar ending at `T`:

- decision time = `T - 15 seconds`;
- target and other current partial prices are the latest 3-second observations at or before decision time that still lie inside the current 5-minute bar;
- current final 5-minute closes are forbidden;
- `partial_return = log(partial_price / previous_confirmed_5m_close)`.

The D4-style own-index baseline and the current other-index `I/V` block are inherited exactly from `cross_index_degree_transfer_utility_v1`.

## 4. Frozen dynamic residual severity — `RZ48`

For each target index separately, use the **48 most recent paired valid confirmed 5-minute close-to-close returns strictly before the current bar**:

- target history: `y_j`;
- other-index history: `x_j`.

Daily first bars have no artificial overnight return and therefore do not enter the 48 valid-return history.

Fit trailing OLS with intercept:

`y_j = alpha + beta * x_j + e_j`.

The relationship is unavailable if the other-index variance is <= `1e-12`, the residual sample SD (`ddof=1`) is <= `1e-12`, or fewer than 48 valid paired confirmed returns exist.

At E15:

`e_current = target_partial_return - (alpha + beta * other_partial_return)`

`RZ48 = abs(e_current) / sd(e_j)`.

Only the absolute residual severity enters the model. `alpha`, `beta`, residual sign, rich/cheap direction and signed relative-value information are diagnostics only and may not enter the predictive block.

## 5. Equal-complexity generic pairwise-dispersion control — `QZ48`

Using the **same 48 paired confirmed returns**, define the equal-weight spread:

`s_j = y_j - x_j`.

Let `mu_s` and `sd_s` be its sample mean and sample SD (`ddof=1`).

At E15:

`s_current = target_partial_return - other_partial_return`

`QZ48 = abs(s_current - mu_s) / sd_s`.

If `sd_s <= 1e-12`, the row is unavailable.

`QZ48` is a generic cross-index dispersion control: it uses the same current pair, same 48 historical pairs and same scalar complexity, but does not estimate a dynamic beta relationship.

`RZ48` and `QZ48` are invariant when all target/other returns and both current partial returns are multiplied by `-1`. Neither coordinate carries trade direction.

Rows must be simultaneously available for both `RZ48` and `QZ48`; no imputation or fallback window is allowed.

## 6. Frozen models

### B — cross-index nuisance baseline

`B` is the exact current-information model `X` from `cross_index_degree_transfer_utility_v1`:

- 84-column own-index D4-style current E15 baseline;
- plus the exact 15-column contemporaneous other-index I/V block.

Expected columns: `B = 99`.

The other-index I/V block is included as a nuisance control even though its earlier standalone incremental promotion failed; this makes the new claim stricter by requiring residual geometry to add information beyond generic other-index current degree.

### R — dynamic residual model

`R = B + RZ48 block`.

### Q — equal-weight spread control

`Q = B + QZ48 block`.

For either scalar severity `z`, use `u = log1p(z)` and add exactly:

- `u`
- `u^2`
- `u` interacted with previous confirmed `NORMAL / UNSAFE / RECOVERING`
- `u^2` interacted with previous confirmed `NORMAL / UNSAFE / RECOVERING`

Thus each added block has exactly 8 columns.

Expected dimensions:

- `B = 99`
- `R = 107`
- `Q = 107`

`R` and `Q` must have identical feature names/counts, identical rows, identical scaling and ridge lambda `0.01`.

## 7. Population and data roles

- 2020: warm-up only;
- Development: 2021–2023;
- forward Development diagnostic: fit 2021–2022, score 2023;
- final frozen fit: 2021–2023 only;
- reusable Validation: 2024–2025 only;
- protected 2026 rows must not be read;
- synthetic 2026 data must not be used;
- BlackBox-V1 must not be queried.

Validation is reusable/adaptive evidence, not fresh OOS.

Inputs are only the already sealed 5m and 3s index carriers. No options/futures or external instruments are introduced.

## 8. Frozen future-risk endpoints

For 15, 30 and 60 minutes, use the inherited D4 endpoints on the **target index**, excluding the current 5-minute bar:

1. `log_future_sigma`
2. `future_tail`

Future windows cannot cross lunch, overnight, symbol or trading-day boundaries. Missing future windows are unavailable, not negative labels.

## 9. Frozen comparisons

For every horizon × endpoint, `R` must pass both:

- `R vs B` — dynamic residual severity versus the already-known own+other current information set;
- `R vs Q` — dynamic residual severity versus equal-complexity generic pairwise dispersion.

An endpoint/horizon is supported only if both comparisons pass every gate.

## 10. Frozen gates

For each of the 12 formal comparisons:

1. Validation `n >= 10,000`, Development `n >= 20,000`, every Validation annual/symbol slice `n >= 1,000`.
2. Tail endpoint has at least 100 positive Validation events.
3. Relative squared-loss reduction >= **1.00%**.
4. Tail absolute Brier reduction >= **0.0005**.
5. Family-adjusted 5-trading-day block-bootstrap absolute-gain interval lower bound > 0.
6. Every 2024/2025 and target-symbol slice has nonnegative absolute gain.
7. Common residual/control availability among otherwise feasible `B` rows >=95%.
8. Corresponding 2023 Development-forward absolute gain is nonnegative.

Bootstrap repetitions: 5000.
Family size: 12.
A fixed 20-trading-day block interval is sensitivity only.

Formal outcome:

- any horizon × endpoint jointly passes `R vs B` and `R vs Q`:
  `CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`
- otherwise:
  `CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_NOT_SUPPORTED`

## 11. Required invariants

Before Validation:

- protocol, runner and parent-runner Git blobs are fixed;
- Development workspace physically excludes 2024–2026;
- final model bytes are frozen before Validation is opened;
- `R/Q` are `107/107` and schema-identical after the first 99 baseline columns;
- current finalized 5m returns cannot enter current partial coordinates;
- each relationship history uses only confirmed returns strictly before the current row;
- a global sign flip leaves `RZ48/QZ48` unchanged;
- future-label perturbations cannot alter current features.

## 12. Post-result discipline

After Validation is opened, this V1 may not be rescued by:

- changing 48 to another relationship window;
- changing OLS to robust/ridge/rolling-correlation/cointegration methods;
- changing the equal-weight `QZ48` control;
- adding residual sign, rich/cheap direction, beta sign or directional interactions;
- selecting only one index, year, state, slot or horizon;
- changing E15 or using the final current-bar close;
- changing ridge, bootstrap family, 1% or 0.0005 gates;
- dropping current other-index I/V from `B`;
- reopening old RMR mean-reversion, intrabar-order, signed-asymmetry or multiscale-volatility rescue paths.

Any later study must pose a genuinely different preregistered mechanism.

## 13. Governance

Always record:

- `validation_reused=true`
- `fresh_oos=false`
- `read_2026=false`
- `synthetic_2026_used=false`
- `blackbox_queried=false`
- `pnl_computed=false`
- `candidate_nominated=false`
- `production_authority=false`
- `v20_started=false`
- `d6_started=false`

No result automatically changes D4, D5 or V19 authority.
