# Intrabar temporal reversal incremental utility V1 — frozen protocol

Date: 2026-09-12
Source main: `b9a6a47b2aca8ea9dddec1aab69c19ae0ae92311`

## Scientific question

Does the **time ordering of price changes inside the current 5-minute bar**, observed causally up to E15 (15 seconds before the native bar end), add practical information about future non-PnL risk after the established own-index D4 current continuous risk coordinates are known?

The mechanism is specifically whether two current bars with similar net displacement and fine-scale activity can differ because one path is locally persistent while another repeatedly reverses between adjacent observations.

This is a bottom-layer risk-information study. It must not produce trade direction, position, sizing, payoff, PnL, routing, or production authority.

## Duplicate audit boundary

This question is distinct from all formally closed axes:

- D3 state utility;
- D4 current E15 intensity / volatility-ratio utility;
- current M3 fine-activity amplitude;
- cross-index current degree;
- historical shock burden;
- one-step degree trajectory / delta;
- signed-return asymmetry over the previous 12 completed 5-minute returns;
- the old `rmr-activity-pressure-reversal-v1-20260909` branch.

The old RMR branch compresses the latest five 1-minute returns to one net `R5`, compresses activity to a mean ratio, and asks whether the **future** 5/15-minute move reverses relative to `R5`. It does not encode the ordering of returns inside the current bar. Therefore it is not a prior test of the mechanism frozen here.

The signed-risk-asymmetry V1 is also not reopened: it uses the previous 12 completed 5-minute returns and asks about historical sign imbalance. This study uses only the ordering of observations inside the current unfinished bar.

## Causal intrabar observation rule

For each native 5-minute bar, define:

- `bar_start = bar_end - 5 minutes`;
- `decision_time = bar_end - 15 seconds`.

Use the existing 3-second-compatible source only through observations available at or before `decision_time`.

Within each half-session, apply the already-audited strict 15-second sampling rule:

- every grid value is the latest source observation at or before the grid time;
- endpoint observation age must be <= 3 seconds;
- a 15-second return is valid only when both adjacent grid prices are finite and there is no raw source gap > 3 seconds between them.

For the current bar, use exactly the 20 grid prices

`bar_start, bar_start+15s, ..., decision_time`

and therefore exactly 19 adjacent 15-second log returns in basis points:

`r_1 ... r_19`.

No observation after `decision_time`, no final current-bar close, no future state, and no future label may enter the intrabar feature block.

If the full 20-price / 19-return path is not valid, the row is unavailable for **both** the temporal block and its order-invariant control. Missing returns are never imputed to zero.

## Frozen order-sensitive coordinates

Let `s_i = sign(r_i)`.

### 1. Adjacent reversal fraction — `ARF19`

Among adjacent pairs for which both returns are nonzero,

`ARF19 = count(r_i * r_{i+1} < 0) / count(r_i != 0 and r_{i+1} != 0)`,

for `i = 1 ... 18`.

If there is no adjacent nonzero pair, the row is unavailable.

`ARF19` lies in `[0,1]`; larger values mean more frequent adjacent directional reversals.

### 2. Lag-1 amplitude alignment — `LAC19`

`LAC19 = sum(r_i * r_{i+1}) / sqrt(sum(r_i^2) * sum(r_{i+1}^2))`,

with the two sums in the denominator taken over `i=1...18` and `i=2...19` respectively.

If either denominator term is not strictly positive, the row is unavailable.

`LAC19` lies in `[-1,1]`; negative values represent amplitude-weighted local reversal and positive values represent local persistence.

Both coordinates are invariant to multiplying the entire current path by `-1`. They therefore describe local ordering rather than trade direction.

No alternative sampling grid, return count, run-length statistic, entropy statistic, dynamic-time-warping statistic, thresholded reversal definition, or symbol-specific form may be introduced after Validation is seen.

## Equal-complexity order-invariant control

To separate genuine ordering information from the generic benefit of adding fine current-bar summaries, construct two coordinates from the **same 19 returns** while discarding their ordering.

### 1. Fine RMS relative to inherited background — `FRMS19`

`FRMS19 = sqrt(mean(r_i^2)) / (10000 * bg48)`

where `bg48` is the inherited standard deviation of the previous 48 completed 5-minute returns in decimal-return units.

### 2. Net-to-path efficiency — `NPE19`

`NPE19 = abs(sum(r_i)) / sum(abs(r_i))`.

If a denominator is not strictly positive, the row is unavailable.

`FRMS19` and `NPE19` are unchanged by any permutation of the 19 returns. `NPE19` is also invariant to a global sign flip. Together they control for fine-scale activity/amplitude and net displacement relative to total traveled path without encoding which return occurred first.

The temporal and order-invariant blocks must use exactly the same rows.

## Frozen models

All models inherit the existing D4-style own-index current E15 baseline `C` exactly as exposed by the frozen degree-trajectory parent runner.

- `C`: inherited own-index D4-style baseline only.
- `T`: `C` + `ARF19` / `LAC19`.
- `O`: `C` + `FRMS19` / `NPE19`.

For both `T` and `O`, raw coordinates `(x, y)` expand identically to:

- `x`
- `y`
- `x^2`
- `y^2`
- `x*y`

Each of the five terms receives one interaction with each previous confirmed state:

- `NORMAL`
- `UNSAFE`
- `RECOVERING`

Thus each added block has exactly 20 columns.

Expected design dimensions:

- `C = 84`;
- `T = 104`;
- `O = 104`.

Ridge lambda is frozen at `0.01`. Fitting rows, target rows, standardization, regularization and evaluation logic must be identical between `T` and `O`.

## Population and split

Subjects:

- `000688.SH`
- `000852.SH`

Historical/fitting boundary:

- 2020: warm-up only where needed;
- Development: 2021-01-01 through 2023-12-31;
- forward Development diagnostic: fit 2021-2022, score 2023;
- final frozen fit: 2021-2023 only;
- reusable Validation: 2024 and 2025 only;
- protected 2026 row data must not be read;
- synthetic 2026 data must not be used;
- BlackBox-V1 must not be queried.

The exact model bytes must be frozen before Validation scoring. Validation is reusable/adaptive evidence, not fresh OOS.

## Frozen endpoints

For horizons 15, 30 and 60 minutes, use the inherited non-PnL targets:

- `log_future_sigma`;
- `future_tail`.

Current bar is excluded from the future target exactly as in the parent utility framework. Lunch/overnight crossing behavior is inherited and must not be loosened.

## Frozen comparisons

For every horizon × endpoint, `T` must pass both:

- `T vs C` — temporal ordering block versus the established D4-style baseline;
- `T vs O` — temporal ordering block versus the equal-complexity order-invariant current-bar block.

An endpoint/horizon is supported only if both comparisons pass every gate below.

## Frozen gates

For each comparison:

1. Validation `n >= 10,000`, Development fit `n >= 20,000`, and every annual/symbol slice `n >= 1,000`.
2. Tail endpoint has at least 100 positive events.
3. Relative MSE improvement is at least **1.00%**.
4. For tail, absolute Brier improvement is also at least **0.0005**.
5. Family-adjusted 5-trading-day block-bootstrap interval for absolute gain has lower bound > 0.
6. Every annual and symbol slice has nonnegative absolute gain.
7. Common intrabar-path availability coverage versus otherwise-feasible inherited baseline rows is at least 95%.
8. The corresponding 2023 Development-forward absolute gain is nonnegative.

Bootstrap repetitions: 5000.

Family size for multiplicity adjustment: 12 comparisons.

A 20-trading-day block interval is sensitivity output only and is not a promotion gate.

## Frozen decision

If at least one horizon × endpoint passes jointly against both `C` and `O`:

`INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`

Otherwise:

`INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_NOT_SUPPORTED`

A statistical hint below the practical gates must be reported as such and must not be promoted.

## Post-result discipline

After Validation is opened, this V1 specification may not be rescued by:

- changing the 15-second grid;
- using 3-second raw returns directly;
- moving E15 closer to the bar close;
- adding run length, entropy, crossing counts, DTW, motif or shape-search features;
- changing zero-return treatment;
- changing state, slot, year, horizon or symbol filters;
- selecting only one index;
- changing ridge lambda;
- lowering the 1% or 0.0005 practical gates;
- dropping the order-invariant `O` control;
- reopening multiscale-volatility or signed-asymmetry variants.

Any later study requires a scientifically distinct preregistered mechanism, not a rescue of this result.

## Governance outputs

Always record:

- `validation_reused=true`;
- `fresh_oos=false`;
- `read_2026=false`;
- `synthetic_2026_used=false`;
- `blackbox_queried=false`;
- `pnl_computed=false`;
- `candidate_nominated=false`;
- `production_authority=false`;
- `v20_started=false`;
- `d6_started=false`.

No result in this study automatically changes V19, D4 or D5 consumer authority.
