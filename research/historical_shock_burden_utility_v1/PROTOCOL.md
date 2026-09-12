# Historical shock-burden incremental utility V1 — frozen protocol

Date: 2026-09-12  
Source main: `f182176c18818c8dd370b5490e411a78f563919f`  
Status at freeze: **results-blind for this V1 comparison**. D4 own-current I/V, V5 recurrent-shock clock reset, historical state-sufficiency / future-risk-burden diagnostics, M3 current-refresh results and cross-index current-degree results are already known. Therefore 2024–2025 remains adaptive reusable Validation, not fresh OOS.

## 1. Question

At E-15, after the target index's own causal confirmed history, previous V19-style state, recent confirmed shock-age bucket, and current D4-style shock-intensity / volatility-ratio coordinates are already known, does **accumulated prior shock burden** still add practically material information about future risk?

The mechanism under test is historical memory, not current activity refresh and not another first-shock detector. Specifically: do repeated / unusually large confirmed shocks in the recent completed trading-bar history contain information not summarized by current I/V, state, recent-shock age and ordinary rolling volatility?

This is risk-information research only. It does not create a trade, direction signal, router, position rule, V20 state or production field.

## 2. Why this is distinct from earlier work

- V5 `highvol_reshock_cluster_v5` established that a recurrent shock resets the recovery clock, but did not test cumulative prior shock burden after current degree and recent-shock age are controlled.
- The 2026-09-07 state-sufficiency diagnostic compared current recovery ratio against elapsed / recovery-age variables only.
- The old `RISK_BURDEN_PROTOCOL` used “burden” to mean **future** 15-minute unsafe burden conditional on current state; it did not construct a backward-looking shock-count or shock-excess feature.
- Trigger-severity diagnostics tested static properties of the first shock, not repeated confirmed shock history.
- D4 tested current E-15 I/V against historical controls but did not include thresholded cumulative shock memory.

So V1 asks a previously unresolved incremental question.

## 3. Frozen causal ancestry

Use the accepted D4-style own-index E-15 reconstruction implemented by the current cross-index utility parent runner. Parent identity at freeze:

- `research/cross_index_degree_transfer_utility_v1/run_study.py` Git blob `b4d3c72e58706b2eb9ae8425f7e7f5439ba002c5`;
- inherited activity/D4-style parent blob `b148d8ccf1d13651434b7b14b42a27dc4b31f5e6`.

For current target bar end `T`, decision time is `T-15s`. Current I/V are computed from the latest current-bar 3-second observation available at or before that decision, previous confirmed 5m close, and confirmed-history `bg48` / previous 11 returns exactly as in the parent. Current final close and current final 5m return are forbidden from current features.

The baseline C contains:

- target symbol and 5-minute slot;
- previous confirmed state;
- confirmed recent-shock age bucket;
- confirmed-history `rms3/rms6/rms12/rms48`, `bg48`, previous absolute return;
- current E-15 I/V with the inherited five-term nonlinear expansion and previous-state interactions.

No D4/V19 threshold or state definition changes.

## 4. Frozen backward-looking memory clocks

Memory is measured over the **latest 12 valid completed intraday return bars** for that symbol, strictly before the current E-15 bar. This is a 12-trading-bar memory, not 60 wall-clock minutes.

Rules:

- only completed 5-minute close-to-close intraday returns enter;
- the first bar of a trading day has no intraday return and is skipped as a memory observation;
- lunch / overnight gaps do not create synthetic returns;
- valid completed bars before a gap remain legitimate past information, exactly as rolling confirmed-history volatility can span trading sessions;
- 2020 may supply warm-up history but is never fitted or evaluated;
- for row `t`, memory is computed **before** row `t` final values are appended to the historical queue;
- therefore changing row `t` final close / final shock label cannot alter row `t` memory.

A row is memory-available only when twelve prior valid completed bars with finite required coordinates exist.

## 5. Shock-specific memory S

For each of the 12 prior completed bars `j`, use its already-confirmed coordinates:

- `I_final_j = abs(r_j) / bg48_j`;
- shock flag `1[I_final_j >= 3.0]`.

Freeze two summary coordinates:

- `shock_count12 = sum 1[I_final_j >= 3.0]`;
- `shock_excess12 = sum max(I_final_j - 3.0, 0)`.

These are historical attributes only; no current partial or future information enters.

S = C plus the following fixed transform block:

- `u = log1p(shock_count12)`;
- `v = log1p(shock_excess12)`;
- `u^2`, `v^2`, `u*v`;
- each of these five terms interacted with the three frozen previous-state indicators.

This adds exactly 20 columns.

## 6. Equal-complexity high-volatility memory control H

To distinguish shock-specific memory from a generic benefit of adding a thresholded historical burden summary, construct H from the same twelve prior bars using their confirmed final volatility ratios:

- `V_final_j = final_rv12_j / bg48_j`;
- high-vol flag `1[V_final_j >= 1.5]`;
- `highvol_count12 = sum 1[V_final_j >= 1.5]`;
- `highvol_excess12 = sum max(V_final_j - 1.5, 0)`.

H = C plus the **identical 20-column transform/state-interaction schema** used by S, replacing the shock pair with the high-vol pair. S and H must have identical feature names, counts, scaling and ridge penalty. `S vs H` is the critical mechanism comparison.

This control is not claimed to be information-equivalent to S. It controls function complexity and asks whether thresholded shock recurrence carries value beyond a similarly summarized historical high-vol burden.

## 7. Data roles

`DATA_USAGE_POLICY_V2` is binding.

- 2020: warm-up only;
- Development fit/search-free construction: 2021–2023;
- forward Development diagnostic: fit 2021–2022, score 2023;
- reusable Validation: 2024–2025 only, not fresh/blind OOS;
- 2026: physically excluded from all workflow checkouts;
- BlackBox-V1: not queried.

Subjects remain only `000688.SH` and `000852.SH`. Inputs are the repository-sealed 5m and 3s carriers already admitted for prior causal-risk research.

## 8. Future-risk endpoints

Use exactly the inherited D4 endpoint family on the target index, excluding the current 5-minute bar and never crossing half-session / lunch / overnight boundaries:

1. 15/30/60m `log_future_sigma = log(max(RMS(next H/5 complete 5m returns),1e-12))`;
2. 15/30/60m `future_tail = 1[max(abs(next H/5 returns)) >= 3*bg48_at_decision]`.

Missing future windows are unavailable, never negatives.

## 9. Fixed model family

Models are `C`, `S`, `H`.

All use:

- ridge lambda `0.01`;
- Development-column mean / population-standard-deviation scaling;
- unpenalized intercept;
- squared loss;
- `[0,1]` clipping only for the tail endpoint;
- no hyperparameter, threshold, window, interaction or horizon search.

The scientific cohort for each horizon is the exact same set of rows for C/S/H: own baseline available, current E-15 I/V available, twelve-bar S/H memory available, and future endpoint feasible.

## 10. Execution order

1. Verify parent blobs, input hashes, V2 governance and physical absence of 2026 data in the workspace.
2. Build confirmed history and twelve-bar memory before attaching current E-15 snapshots.
3. Verify causal invariants: current-row final-value perturbation cannot change current memory; future perturbation cannot change any current feature; S/H schemas are identical and C is their exact subset.
4. Fit C/S/H on 2021–2022 and score 2023; record all twelve forward comparison signs without changing this protocol.
5. Fit final 18 probes on 2021–2023 and freeze exact model bytes.
6. Only after freeze identity exists may unchanged probes be scored on 2024–2025 reusable Validation.

## 11. Fixed comparisons and practical gates

Family = 12 comparisons:

- `S vs C` and `S vs H`;
- 2 endpoints;
- 3 horizons.

Primary uncertainty follows D4/cross-index V1:

- both indices on the same trading day stay together;
- non-overlapping five-trading-day blocks within year;
- 5000 stratified bootstrap repetitions;
- seed `20260916`;
- Bonferroni two-sided family-12 interval;
- fixed 20-trading-day blocks are sensitivity only.

Each individual comparison passes only if all are true:

- Validation n >= 10,000;
- Development n >= 20,000;
- each Validation year and each symbol n >= 1,000;
- tail endpoint has >=100 positive Validation events;
- relative squared-loss reduction >=1.0%;
- tail endpoint additionally has absolute Brier reduction >=0.0005;
- adjusted 5-day block interval lower bound >0;
- 2024, 2025, STAR50 and CSI1000 absolute-gain signs are all nonnegative;
- twelve-bar memory coverage among otherwise own-base+future-feasible rows >=95%;
- corresponding 2023 forward Development gain is nonnegative.

An endpoint/horizon is supported only if **both `S vs C` and `S vs H` pass**.

Formal outcome:

- at least one joint pass: `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS`;
- no joint pass: `HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`.

A win over C alone is insufficient because it cannot distinguish shock-specific recurrence memory from generic extra historical burden representation.

## 12. Required diagnostics — never rescue gates

Report:

- shock/high-vol memory distributions and correlations;
- memory availability / coverage;
- comparison gains by symbol, year, previous state and decision slot;
- future RMS/tail by deciles of the frozen S-vs-C prediction increment;
- frequency of zero / one / multiple prior shocks in the twelve-bar window;
- observation-age distribution of the current E-15 snapshot.

These diagnostics may explain a result but cannot change the frozen gates.

## 13. Interpretation boundaries

A supported result would mean only that shock-specific completed-history burden is a useful additional **research risk attribute** for specified endpoints under reusable Validation. It does not automatically authorize a D5 field, V19 transition, new state or production use; a separate consumer-admission decision would still be required.

A negative result closes this fixed twelve-trading-bar shock-memory specification. Do not rescue it post hoc by changing 12 to 6/24 bars, using decays, moving 3σ/1.5 thresholds, filtering one index/state/time slice, changing horizons, dropping H, or adding direction/PnL.

Always record:

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
