# Mechanism-to-execution diagnostic v1 — adjudication

Date: 2026-09-08  
Identity: `rmr_mechanism_to_execution_diagnostic_v1`  
Status: **COMPLETE / DIAGNOSTIC ONLY / NO BLACKBOX QUERY**  
Production authority: `false`

## Execution authority and reproducibility

The frozen diagnostic was executed by GitHub Actions run `34226850838` at commit `f35f64dcb567b681f583ae16881226c6ca738784`.

- job `102062955823`: `completed / success`;
- 6/6 boundary/governance tests passed;
- detailed receipt artifact ID: `10056093829`;
- artifact ZIP SHA256: `841e079c9b4a9835c3c323f7dff010258a38f54d7afecfb49d215fc6a81df67a`;
- historical source maximum date: `2025-12-31`;
- R1 frozen bundle SHA256: `41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb`;
- R2 frozen bundle SHA256: `08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1`;
- no refit, threshold selection, horizon selection, strategy optimization or BLACKBOX access occurred.

The reusable BLACKBOX ledger remains at **3 completed queries**. This diagnostic did **not** create query #4.

## Decisive VALIDATION evidence

Returns below are basis points. The fixed cost is 10bp round trip.

| Cell | Tradeable | Restoration rate | Frozen p | Mean break-even p | Binary structural EV net | Realized gross | Realized net | Target gross | Failure gross | Median reward/loss | Median reward consumed by next-bar entry | Censor | Median / p90 hold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R1_A | 92.52% | 70.15% | 70.83% | 77.37% | -23.42bp | -3.21bp | -13.21bp | +53.17bp | -171.42bp | 0.270 | 2.01% | 1.08% | 46 / 373 bars |
| R1_B | 94.86% | 71.95% | 73.62% | 74.64% | -18.06bp | +2.67bp | -7.33bp | +93.79bp | -288.15bp | 0.277 | 1.48% | 5.42% | 105 / 807 bars |
| R2_A | 84.21% | 23.50% | 25.53% | 42.63% | -11.79bp | -2.68bp | -12.68bp | +49.53bp | -19.39bp | 2.678 | 2.00% | 0.00% | 11 / 55 bars |
| R2_B | 82.89% | 17.00% | 19.00% | 27.94% | -12.32bp | -2.52bp | -12.52bp | +109.06bp | -28.49bp | 8.691 | 1.31% | 0.00% | 16 / 160 bars |

The common result is stronger than a simple statement that 10bp cost is too high. **All four cells have negative binary structural expected net before realized first-passage overshoot is used.** In R1_A, R2_A and R2_B, realized gross is already negative before the 10bp cost. R1_B is the only pooled VALIDATION cell with positive realized gross, but +2.67bp is far below 10bp.

The mean frozen probability versus mean break-even probability is descriptive, not an event-level expected-value identity. The decisive geometry statistic is the eventwise binary structural expected net, which remains negative in every cell. R1_B is especially important: its average probabilities look close (`73.62%` versus `74.64%`), yet heterogeneous reward/loss exposures still produce `-18.06bp` mean binary structural EV.

## Fixed markout term structure

All predeclared horizons are shown; none is selected.

| Cell | 1 | 5 | 15 | 30 | 60 | 120 | 240 bars |
|---|---:|---:|---:|---:|---:|---:|---:|
| R1_A | +0.27 | +1.23 | +3.49 | +5.77 | +5.65 | +4.02 | +2.37 |
| R1_B | +0.47 | -0.05 | +1.36 | +6.54 | +7.67 | +10.32 | +23.75 |
| R2_A | +0.06 | -0.75 | -2.33 | -3.91 | -5.66 | -9.69 | -15.93 |
| R2_B | +0.25 | -1.61 | -0.14 | -3.18 | -4.75 | -12.81 | -15.98 |

R2 has the wrong temporal translation for the current directional execution family: after the immediate bar, pooled markouts become progressively adverse. A mechanism that improves the probability of eventual structural re-entry does not imply profitable directional persistence from next-minute entry.

R1_A has positive pooled markouts after the immediate horizon but they remain below the fixed 10bp round-trip cost and are not stable enough across years to motivate a horizon rescue.

R1_B is different. Its predeclared term structure strengthens broadly across later horizons: +6.54bp at 30, +7.67bp at 60, +10.32bp at 120 and +23.75bp at 240. The 240-bar gross markout is positive in 4/5 VALIDATION years, but this observation **does not authorize selecting 240 bars**. It is only evidence that R1_B restoration information may manifest as a diffuse temporal path rather than through immediate structural first-passage execution.

## Why mechanism PASS and economics FAIL are compatible

### 1. `geometry_unfavorable` — primary

R1's certified parent-integrity variable improves the probability of recovery, but the fixed structural target is small relative to the failure boundary. The median reward/loss ratios are only `0.270` and `0.277`, so recovery probabilities near 70–74% are not enough after the fixed execution geometry and 10bp cost.

R2 has favorable raw target/loss ratios (`2.68` and `8.69` median), but restoration itself is much less frequent: frozen mean probabilities are only `25.53%` and `19.00%`, below mean break-even levels `42.63%` and `27.94%`. Thus R2's probability improvement is statistically real yet economically too small for this payoff map.

### 2. `entry_slippage_or_confirmation_delay` — secondary, not the main cause

Next-minute tradeability is high in every cell (`82.89%` to `94.86%`). Median target reward consumed between confirmation and fixed next-bar entry is only `1.31%` to `2.01%` in VALIDATION. This does not support an entry-delay tuning rescue.

### 3. `boundary_overshoot_tail` — secondary aggravator

Mean failure-side overshoot in VALIDATION is approximately `-7.43bp`, `-7.01bp`, `-5.72bp`, `-5.65bp` for R1_A, R1_B, R2_A and R2_B. Target-side overshoot is positive as well, approximately `+8.64bp`, `+13.14bp`, `+6.36bp`, `+10.58bp`.

Overshoot changes realized magnitude but is not the primary failure: binary expected net is already negative before overshoot.

### 4. `slow_resolution_cost_exposure` — timing concern for R1, not proven cost cause

R1_B is slow: median `105` bars, p90 `807` bars, censor `5.42%`; R1_A median is `46` and p90 `373` bars. R2 resolves much faster and essentially without censoring.

The diagnostic charges only a fixed 10bp round trip, not a time-varying carrying cost. Therefore slow resolution cannot be claimed as a measured cost cause. It is evidence of a timing/capital-exposure mismatch, especially for R1_B.

### 5. `short_horizon_wrong_way_markout` — strong for R2; delayed realization signal for R1_B

R2's fixed term structure deteriorates with horizon. This argues against reopening R2 via simple execution timing changes.

R1_B instead shows a broad delayed positive term structure. This is the only diagnostic evidence strong enough to justify a new theory review, but not a strategy or horizon selection.

### 6. `probability_not_monotonic_with_realized_return` — supported in all pooled cells

Pooled VALIDATION Pearson correlations between frozen probability and realized net are:

- R1_A: `+0.0358`;
- R1_B: `-0.0075`;
- R2_A: `-0.0482`;
- R2_B: `-0.0285`.

The fixed probability-bin mean realized nets are non-monotonic in all four pooled cells. In bp, from low to high non-empty bins:

- R1_A: `-43.87, -8.97, -33.80, -4.43, -13.97`;
- R1_B: `+46.50 (n=3), +1.76, -10.73, -9.28, -6.49`;
- R2_A: `-10.01, -13.23, -23.07`;
- R2_B: `-10.63, -15.10, -9.83`.

Therefore the certified probability is a restoration-likelihood signal, not a monotonic realized-return score. Probability filtering / threshold search is not supported as a rescue.

## Program adjudication

### Chosen next direction: `execution_timing_theory`

Authorize only a **results-blind theory review** for a materially new R1_B temporal execution mechanism. This is not `R1 economic v4`, not a strategy promotion, and not permission to optimize `[1,5,15,30,60,120,240]`.

The theory review must explain causally why higher-scale parent-trend restoration should realize over a distributed time path and how an execution object should represent that path **before** any new outcome-dependent parameter is opened. It may not choose a horizon from this receipt, tune entry delay, target, stop, cost, probability threshold, scale, year, regime or time of day.

### Closed under current evidence

- R1_A: stop current index-level economic translation family. Positive pooled markouts remain too small versus fixed cost and annual timing is not robust.
- R2_A / R2_B: stop current index-level economic translation family. Probability is below payoff break-even and the pooled markout term structure becomes increasingly adverse.
- probability-filter rescue: closed by non-monotonic realized-return mapping.

### Instrument mapping

Do **not** select ETF/futures/options mapping from this diagnostic. The study contains index-level price-path evidence, not instrument-specific spread, basis, carry, convexity, liquidity or execution evidence. Instrument mapping remains eligible only if a separate independent instrument theory is later proposed.

## Governance consequence

- BLACKBOX query count remains exactly `3`.
- No BLACKBOX query #4 is authorized or scheduled.
- No automatic R1 economic v4, R2 economic v2 or router v2 is opened.
- Broad R8/R9 indicator search remains paused.
- Production authority remains `false`.

Detailed decisive evidence is retained in `docs/research/rmr_mechanism_to_execution_diagnostic_v1_decisive_receipt_20260908.json`; the full workflow receipt is anchored by the successful run/artifact above.
