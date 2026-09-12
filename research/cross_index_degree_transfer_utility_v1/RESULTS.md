# Cross-index current-degree transfer utility V1 — reusable Validation result

Date: 2026-09-12  
Decision: **`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

This result closes the frozen specification in `PROTOCOL.md`. It does not change V19, D3, D4, D5, the M3 decision, the reception work, or the data-governance boundary.

## Question

At the same E-15 decision time, after the target index's own confirmed history and own current shock-intensity / volatility-ratio (`I_t`,`V_t`) are already known, does the *other* index's current E-15 risk degree add practically material information about the target index's future risk?

The fixed models were:

- **C** — target own D4-style history + current own I/V;
- **X** — C + other-index **current** E-15 I/V in a frozen 15-column nonlinear/target-interaction block;
- **L** — C + the same 15-column block using only other-index **lagged confirmed-history** I/V.

An endpoint/horizon could be supported only if both `X vs C` and `X vs L` passed every preregistered gate.

## Frozen identity and execution

Frozen protocol Git blob:

`9d925368f01163b51421d5221d9a3ba4f5adaaaf`

Frozen parent D4-style reconstruction runner Git blob:

`b148d8ccf1d13651434b7b14b42a27dc4b31f5e6`

Original Development fit run: `34676891139`.

Original pre-Validation frozen model artifact:

- artifact id `10292497993`;
- artifact ZIP digest `sha256:d46ead8563dda8e51be572044e981d49e3ff6a03f9fcebdac5d5e3f546b41df4`;
- exact `FROZEN_MODELS.json` SHA256 `7eae7142323b38c5ae54618745e9ad9891c00afb09d02e8eb8def4490675f6b6`.

Feature identity at freeze:

- C: 84 columns;
- X: 99 columns;
- L: 99 columns;
- X/L schema identical;
- current/lag cross-index block: 15 columns.

Development paired coverage was 100% at all three horizons.

The decisive reusable Validation run is `34677297901`, job `103509323551`. It downloaded the **original pre-Validation model bytes**, verified the exact SHA above, reran 7/7 causal/complexity invariants, then scored unchanged models on 2024–2025.

Final Validation artifact:

- artifact id `10292433776`;
- bytes `65330`;
- artifact ZIP digest `sha256:1ab8a12d77beb15c7aba5880a588c3475dc7d6270ca121eb95056ef9aa56ba92`;
- `VALIDATION_RESULTS.json` SHA256 `01780af3bcee5d087eb3af4ea02739a210a28b1cd211e08892a5be1de2b4664f`.

## Cohort

Paired other-current and other-lag coverage among otherwise target-base + future-feasible rows was exactly 100%.

| horizon | Development n | Validation n | paired coverage |
|---|---:|---:|---:|
| 15m | 59,614 | 39,770 | 100% |
| 30m | 50,890 | 33,950 | 100% |
| 60m | 33,442 | 22,310 | 100% |

The Validation target-base universe contained 45,590 available E-15 rows out of 46,560 target rows before horizon feasibility.

## Formal comparison results

No comparison met the frozen 1% practical relative-loss gate. No five-day Bonferroni-adjusted interval had a positive lower bound. Consequently all six endpoint × horizon joint promotions are false.

| horizon | endpoint | comparison | relative gain | absolute gain | 5d adjusted CI low | supported |
|---|---|---|---:|---:|---:|---|
| 15m | log future RMS | X vs C | +0.021981% | 0.00006665 | -0.00026423 | no |
| 15m | log future RMS | X vs L | +0.000276% | 0.00000084 | -0.00020659 | no |
| 15m | future tail | X vs C | +0.000943% | 0.00000028 | -0.00003799 | no |
| 15m | future tail | X vs L | -0.031588% | -0.00000941 | -0.00003718 | no |
| 30m | log future RMS | X vs C | +0.055856% | 0.00009500 | -0.00019531 | no |
| 30m | log future RMS | X vs L | +0.062989% | 0.00010713 | -0.00002207 | no |
| 30m | future tail | X vs C | +0.077012% | 0.00003774 | -0.00004003 | no |
| 30m | future tail | X vs L | +0.015409% | 0.00000755 | -0.00004194 | no |
| 60m | log future RMS | X vs C | +0.101470% | 0.00012086 | -0.00021706 | no |
| 60m | log future RMS | X vs L | +0.030288% | 0.00003605 | -0.00012750 | no |
| 60m | future tail | X vs C | +0.141975% | 0.00011937 | -0.00007778 | no |
| 60m | future tail | X vs L | +0.002945% | 0.00000247 | -0.00010626 | no |

The largest pooled point estimate is only +0.142% (`60m future_tail`, X vs C), roughly one seventh of the frozen 1% practical gate, and its tail absolute gain is also far below the required `0.0005`.

## Stability and direction of the evidence

This is not merely a narrowly missed practical threshold:

- 15m log-RMS X vs C is negative for STAR50 and positive for CSI1000;
- 30m and 60m log-RMS X vs C show the same STAR50-negative / CSI1000-positive split;
- 15m tail X vs L is negative pooled;
- several tail comparisons are negative in 2025 or in one target index;
- 30m and 60m tail X vs C had negative 2023 forward-Development gain.

Therefore the protocol's year/symbol sign and forward-development gates also reject several comparisons independently of the 1% practical gate.

Do **not** convert the visible CSI1000-positive / STAR50-negative asymmetry into a post-hoc one-direction experiment. The frozen study required bidirectional robustness and explicitly prohibited rescuing the result by selecting target direction, lag, state, horizon or threshold after seeing outcomes.

## Descriptive dependence

The two indices' contemporaneous degrees are substantially redundant:

- at the 15m cohort, own/other current shock-intensity correlation ≈ `0.6356`;
- own/other current volatility-ratio correlation ≈ `0.7354`;
- other current vs other lag volatility-ratio correlation ≈ `0.9148`.

That high redundancy is consistent with the tiny conditional gains once target own current I/V is already present. It is interpretation only, not a promotion gate.

Historical observation-age diagnostics had median and 95th percentile 0 seconds, with maxima 42 seconds for the 15/30m cohorts and 39 seconds for 60m. These are observation-time semantics from historical data, **not measured local feed reception latency** and must not be described as such.

## Engineering incidents during execution

Three execution incidents occurred, none of which changed the frozen science:

1. Initial run `34676891139`: Development fit/freeze succeeded. Validation execution stopped in a descriptive decile writer because pandas interpreted `g.tail` as the DataFrame method rather than the column named `tail`. No comparison result was produced by that failed Validation step.
2. Retry run `34677092352`: a fresh refit was deliberately rejected because its JSON model bytes did not exactly match the original frozen SHA. Development forward statistics matched the first fit to floating numerical precision, but the refit was **not** accepted as a new freeze.
3. Frozen-validation run `34677231960`: original frozen bytes were downloaded and verified, but the execution-only compatibility wrapper initially lacked repo root on `sys.path`; scoring did not start. The import path was fixed without changing the scientific runner.

The decisive run `34677297901` then used the original `7eae...` frozen model bytes and completed successfully.

## Decision boundary

Formal decision:

**`CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

Interpretation: the other index's contemporaneous E-15 causal risk degree is correlated with the target's own degree, but after target own I/V is already known, the marginal future-risk predictive value is tiny, unstable by target/year in several views, and does not clear the preregistered practical or uncertainty gates.

Therefore:

- do not add other-index current I/V to the D5 consumer;
- do not add a cross-index state to V19;
- do not reopen cross-index relative-value/direction/router work;
- do not rescue this specification with one-way direction selection, lag search, state filters, threshold changes, horizon selection or sample deletion.

Historical decisions remain unchanged: M3 refresh is not promoted; D4 own-index I/V support remains endpoint-limited; V19 remains frozen; D3/D5/D5R/reception conclusions remain as previously recorded.

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `d6_started=false`; `v20_started=false`; `production_authority=false`.
