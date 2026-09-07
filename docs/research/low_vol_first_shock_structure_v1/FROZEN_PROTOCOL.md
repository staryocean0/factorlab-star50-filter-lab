# Low-Volatility First-Shock Conditional Structure v1 — FROZEN PROTOCOL

Date: 2026-09-07
Branch: `research/low-vol-first-shock-structure-v1-20260907`
Parent evidence: `research/measurement-support-audit-20260907` @ `ac15a6ed5cc257c0ed0c64b0646438f2653e46e7`
Status at freeze: **RESULTS NOT READ / NO NEW MODEL EFFECT CLAIM**

## 1. Research question

Test whether **cross-scale abnormal activity observable before an event** contains incremental information about the next 15-minute **first-shock risk** specifically when the immediately preceding 5-minute price path still looks low-amplitude.

This is not a trading study and not another morphology-algorithm version. It does not unfreeze direction, third-wave, returns/P&L, OOS, trading, sizing, or production.

The target failure mode is the ordinary-session first jump that is missed by a broad volatility-state predictor.

## 2. Data and admissible support

Only already-authorized two-index historical data through 2025 may be used:

- `000688.SH` STAR50 index;
- `000852.SH` CSI1000 index;
- minute inputs used by the existing first-shock study;
- existing index 3-second source observations and their frozen quality/eligibility rules.

No 2026 data. No ETF/option/futures/order-book substitution.

Fine-scale analysis is restricted to decision windows satisfying the already-audited support rules. The audited source gap means no fine-scale scientific decision point before `2022-05-16` may be admitted merely by interpolation, zero-filling, endpoint invention, or relaxed continuity rules.

Source rows with repeated seconds retain their stable source ordering/key; timestamps alone must not be silently deduplicated.

## 3. Frozen event definition

Reuse the minute first-shock definition without modification:

- shock minute absolute log return > 30 bp;
- shock minute absolute log return > 4 × trailing 30-minute pre-event RMS;
- RMS floor = 1 bp;
- a first event requires the preceding 30 known minutes to contain no event of the same definition;
- ordinary decision points are session minute 31 through 105;
- a valid alarm must be strictly available at least one minute before the shock minute's earliest possible start;
- future horizon = next 15 minutes within the same admissible session support.

The event definition, horizon, and lead-time convention may not be changed after seeing this study's results.

## 4. Frozen low-amplitude conditioning set

Primary conditioning set:

`pre5m_range_bp < 30`

where `pre5m_range_bp` is computed only from information fully known at the decision time over the previous five minutes under the frozen fine-support rules.

This conditioning set is deliberately narrower than “low volatility” in general. It means the observed five-minute price range has not yet reached the 30 bp shock-scale threshold. It must not be described as a safe or calm state.

The previously audited event ledger is descriptive evidence only; it is not used to tune the 30 bp threshold in this study.

## 5. Frozen candidate measurements

All measurements are causal and computed using only data available at or before the decision point. No supervised classifier is fit.

### M1. Fine/coarse realized-variation ratio

Over the previous five physical minutes:

- `RV_fine`: sum of squared log returns on the admissible 15-second observation grid;
- `RV_1m`: sum of squared one-minute log returns over the same physical interval;
- `M1 = log((RV_fine + eps) / (RV_1m + eps))`.

`eps` is a fixed numerical stabilizer only: `1e-16` in log-return-squared units.

Purpose: detect hidden within-minute movement that is muted by minute endpoints.

### M2. Five-minute displacement concentration

Using the admissible 15-second path over the previous five physical minutes, let `a_i = |Δ log P_i|` and `n` be the number of observed path steps required by the frozen support grid.

`M2 = n * Σ(a_i / Σa_i)^2` when total motion > 0; otherwise missing.

Purpose: distinguish diffuse small motion from a few locally concentrated pre-shock moves without using direction.

### M3. Short-horizon activity surprise

`A5 = sqrt(mean(r_15s^2))` over the previous five physical minutes.

Build a causal clock-matched reference using only earlier admissible observations of the same index and same session-minute bucket. Reference statistic is the expanding median of `log(A5)` with a minimum of 60 prior admissible decision points. Scale is `1.4826 × expanding MAD`, with floor `1e-8`.

`M3 = (log(A5) - expanding_median) / max(1.4826*MAD, 1e-8)`.

No future year may enter an earlier year's reference.

### M4. Cross-scale discordance

`M4 = M3 + M1`.

This is fixed before results and is the only composite measurement. No fitted weights, feature search, or post-result recombination is allowed.

## 6. Threshold freeze and evaluation roles

Because fine support begins during 2022, use roles:

- 2022-05-16 through 2022-12-31: reference warm-up / descriptive support only;
- 2023: calibration only;
- 2024: evaluation year 1;
- 2025: evaluation year 2.

For each index and each measurement M1–M4 separately, freeze a **high-anomaly threshold at the 80th percentile** of admissible 2023 low-amplitude decision points. No 2024/2025 information enters these thresholds.

No threshold is retuned to maintain 20% coverage in evaluation years. Actual coverage drift must be reported.

A secondary continuous analysis may report monotonic risk across fixed 2023 quintile cut points, but these same cut points must be carried unchanged into 2024 and 2025.

## 7. Primary estimands

For each index × year × measurement:

1. `risk_high = P(first shock in next 15m | low-amplitude, M >= frozen threshold)`;
2. `risk_low = P(first shock in next 15m | low-amplitude, M < frozen threshold)`;
3. absolute risk difference `risk_high - risk_low`;
4. risk ratio with explicit undefined handling when denominator is zero;
5. high-anomaly time coverage;
6. unique first-event recall under strict lead-time;
7. number of alarm segments after merging consecutive high-anomaly decision points;
8. median and distribution of earliest valid lead minutes among hit unique events.

Decision-point risk and unique-event recall are distinct quantities and must never be conflated.

## 8. Required controls

### C1. Activity-level control

Report the same estimands for a simple trailing-5m one-minute RMS threshold frozen at its 2023 80th percentile. This tests whether a cross-scale measurement adds anything beyond ordinary recent activity.

### C2. Clock-only control

Report unconditional low-amplitude first-shock risk by fixed session-minute decile/bucket so opening/closing seasonality is visible.

### C3. Same-coverage diagnostic

For interpretation only, evaluation-year top-20% ranking may be shown beside frozen-threshold results. It is explicitly non-deployable and may not replace the frozen-threshold primary result.

## 9. Statistical protocol

Primary uncertainty for risk differences uses a **five-trading-day moving-block bootstrap**, 2,000 resamples when computationally feasible, preserving within-day overlap and clustering.

For the 4 measurements × 2 indices × 2 evaluation years primary risk-difference tests, control family-wise error using Holm adjustment over the 16 preregistered comparisons.

Report raw point estimates and confidence intervals even if none survive correction. Do not select only positive years or only one index after seeing results.

Because event counts are small, effect-size intervals and event counts take priority over asymptotic p-values.

## 10. Mandatory sensitivity views

Without changing the primary definition, report:

- 2024 and 2025 separately;
- STAR50 and CSI1000 separately;
- pooled descriptive view only after the four separate cells;
- support-quality / repair-eligible versus any allowed repaired-minute sensitivity already exposed by the source metadata;
- `pre5m_range_bp < 20`, `<30` primary, and `<40` as sensitivity only; 20/40 must not replace the primary threshold;
- event-level results with repeated overlapping prediction windows collapsed to unique first events.

## 11. Hard fail-closed rules

Stop the scientific run for an affected cell if any of the following occurs:

- future/2026 rows enter a feature or calibration reference;
- fine-support continuity required by the frozen measurement is absent;
- source rows are silently interpolated, deduplicated, or zero-filled;
- the event definition differs from the frozen first-shock definition;
- the 2023 threshold is recomputed using 2024/2025 values;
- results are used to add a new candidate measurement inside this v1 family;
- any return/P&L/trading label is read.

## 12. Decision rule

This study can support **conditional-structure evidence**, not automatic deployment.

A measurement is called `replicated_positive_structure` only if:

- risk difference is positive in both 2024 and 2025 for the same index;
- the pooled effect is not driven solely by one event cluster;
- at least one of the two annual intervals excludes zero before multiplicity adjustment and the direction survives Holm-family review without a sign contradiction;
- alarm coverage and segment inflation are reported and are not hidden;
- the effect is not explained away by the simple trailing-activity control in the same qualitative direction.

Anything weaker is recorded as descriptive / unstable / not established. Negative results close this exact candidate family; they do not prove all cross-scale information is useless.

## 13. Frozen status after preregistration

- `results_read_after_freeze = false`
- `complex_supervised_model_allowed = false`
- `morphology_replication_status = morphology_replication_not_yet_accepted`
- `direction = frozen`
- `third_wave = frozen`
- `returns_or_pnl = frozen`
- `fresh_oos = false`
- `trading = frozen`
- `production = false`
