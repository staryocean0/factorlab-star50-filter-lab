# STAR50 conditioned quiet-first precursor gate v3.4 — result and route stop

Date: 2026-09-08  
Branch: `research/star50-conditioned-precursor-gate-v34-20260908`  
Preregistered protocol commit: `40667c7afadc82ff4a163030a5cedab276edeafb`  
Frozen scientific implementation/test ref: `731f565e8ef74f4679e85fea7a28cc612ce3be11`  
Successful Actions run: `34143862337`  
Workflow commit: `42676647089112cf5b70496589e80165a2197dad`  
Artifact: `10026994387`, digest `sha256:784e88a441ab9684c251d7a8989973cfdd8f93b1cf1796e137a61d623d997e5e`  
Tests: **6 passed**. No 2026 read, no classifier fit, no new morphology feature, no returns/P&L/trading/production evaluation.

## Question

V3.3 showed that the raw frozen V3.2 scale score translated positively to the full quiet-time universe in 2024 but reversed in 2025. V3.4 tested the post-V3.3 hypothesis that the V3.2 signal, if real, might only be meaningful **conditional on the common volatility state** rather than as an absolute score level.

The morphology score was unchanged:

`0.5 * [(logE30-logE240) + (logE60-logE240)]`

For every 2024/2025 eligible quiet decision row, V3.4 used only the 2022–2023 historical quiet library at the exact same half-session/minute, selected the fixed **100** nearest rows in `(log_sigma_pre, log_rv480)`, and converted the current scale score to a midrank historical conditional percentile. The gate was frozen at conditional percentile `>= 0.80`. No labels entered the library, distance, standardization, support limit or threshold construction.

A second preregistered gate checked state transportability: for each historical exact-clock group, the 99th percentile of leave-one-out 100th-neighbor distance was frozen as the support limit. Evaluation rows outside that limit were **retained and flagged**, never deleted. A future-validation candidate required extrapolated rows `<=5%` separately in both years.

## Results

| year | eligible rows | conditioned risk coverage | risk label rate | Clean label rate | risk-Clean diff | RR | conditional AUC | event recall | permutation median recall | state extrapolated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 20,110 | 17.91% | 1.0272% | 0.4059% | **+0.6213 pp** | 2.531 | **0.6317** | 6/13 = 46.15% | 30.77% | **5.74%** |
| 2025 | 21,559 | 19.42% | 0.0239% | 0.0806% | **-0.0567 pp** | 0.296 | **0.4622** | 1/2 = 50.00% | 50.00% | **12.57%** |

The common-volatility baseline is retained only as a comparator. It remains negative in 2024 and positive in 2025, consistent with substantial year-to-year state composition change; it does not rescue the conditioned scale gate.

## Preregistered adjudication

The candidate rule required **all four conditions in both 2024 and 2025**:

1. risk-Clean future-label difference > 0;
2. continuous conditioned-score AUC > 0.5;
3. event recall not below the session-permutation median;
4. evaluation-state extrapolated fraction <= 5%.

Independent post-run recomputation gives:

- 2024: conditions 1–3 pass; condition 4 fails (`5.7434% > 5%`).
- 2025: conditions 1 and 2 fail (`-0.0567 pp`, `AUC 0.4622`); condition 3 is exactly at the reference median; condition 4 fails (`12.5748% > 5%`).

Therefore:

**`candidate_for_future_locked_validation = false`**

and the V3.2 scale-score route is **stopped by protocol**.

## Interpretation

Conditioning on `(log_sigma_pre, log_rv480)` slightly strengthens the positive 2024 ranking relative to the raw V3.3 score, but it does **not** repair the 2025 reversal. In addition, the historical 2022–2023 state library fails its own transportability gate in both evaluation years, especially 2025.

This does not prove that all cross-scale precursors are impossible. It does establish a narrower and important negative result: the already-consumed V3.2 score, both raw and under its pre-existing two-dimensional volatility matching idea, has not produced a stable full-universe quiet-first risk gate across 2024–2025 under fixed results-blind rules.

The two 2025 quiet-first events are too sparse for a strong mechanistic negative claim, but sparsity cannot be used to override the frozen candidate rule.

## Route decision

Effective immediately for consumed 2022–2025 history:

- **do not** scan alternative neighbor counts;
- **do not** scan conditional percentile thresholds;
- **do not** add matching dimensions or morphology variables to rescue the route;
- **do not** fit a classifier to the sparse quiet-first events;
- **do not** reinterpret V3.2 event-vs-control existence evidence as a deployable gate;
- retain V3.2, V3.3 and V3.4 as sequential positive-existence / negative-translation / negative-conditioned-translation evidence.

A legitimate next task is a **label-blind state and measurement support audit** to determine whether the growing 2024–2025 historical-support mismatch is primarily a common-volatility regime transport issue, a clock/session concentration issue, or a data-measurement support issue. That audit cannot promote or retune the stopped V3.2 score route.

All evidence remains consumed historical development (`fresh_oos=false`) and grants no trading or production authority.
