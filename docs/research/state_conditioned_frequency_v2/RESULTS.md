# State-conditioned physical-scale strategy results

Date: 2026-09-08

Status: consumed-history exploratory research. No production/trading promotion.

## Evidence receipt

Canonical successful optimized replay:

- branch: `research/state-conditioned-physical-scale-fast-20260908`
- code commit: `ae52563b9f5349922fb986c8082e02a87ed70d81`
- GitHub Actions run: `34186970072`
- artifact: `state-conditioned-physical-scale-fast-34186970072`
- artifact id: `10040864829`
- artifact SHA256: `9e479bcfc2b49d39a8521ab6fcb9a5a13cb56cdaba7959aba353a5506c866095`

All frozen boundary/equivalence tests passed before the market surface was accepted. Output-manifest byte counts/SHA256 were independently checked after download. The 5m scaled-clock and fixed-physical families are exactly identical for both indices, including signal, lowpass and sigma hashes; the full annual 5m metric rows are numerically identical as well.

Data roles remain:

- 2021-2025: consumed exploratory history;
- 2026-01-05..2026-08-21: already-opened consistency replay, not fresh OOS for this new routing hypothesis.

## Question tested

Does post-shock `Unsafe` mean the original Butterworth+hysteresis strategy should become physically faster, or does the state merely support finer sampling/execution while retaining the old physical information horizon?

Two frozen families were compared at 1/2/3/5/10/15 minute bars:

- `scaled_clock`: keep 12-bar filter + 48-bar sigma, so the physical strategy clock contracts with the bar size;
- `fixed_physical`: keep approximately 60-minute filter + 240-minute sigma memory while sampling more finely.

The 5-minute member is the exact common anchor.

## Main conclusion

**The study does not support a generic `Unsafe -> shorten the whole strategy clock` rule.**

At the most relevant 1/2/3 minute scales, fixed-physical is better than scaled-clock in Unsafe for both indices at 1m and 2m, and for CSI1000 also at 3m. STAR50 scaled-clock is better at 3m, but this does not survive the already-opened 2026 replay. Therefore the Phase-1 result—Unsafe contains more short-horizon movement—does not imply that the original strategy's information horizon should be mechanically compressed.

A more precise interpretation is:

> high volatility can justify a faster observation/execution cadence, but the slower structural signal may still need to be retained.

This distinction matters: `faster bars` and `faster underlying strategy` are not the same intervention.

## STAR50

No stable Unsafe routing candidate is promoted.

2021-2025 pooled Unsafe break-even one-way friction, in bp:

| scale | scaled-clock | fixed-physical |
|---:|---:|---:|
| 1m | 0.570 | 1.647 |
| 2m | -1.026 | 1.150 |
| 3m | 0.987 | -0.344 |
| 5m | 0.394 | 0.394 |

The apparently better fixed-physical 1m/2m cells are not stable. For example, fixed-physical 1m Unsafe break-even is negative in 2022 and the already-opened 2026 replay; fixed-physical 2m is negative in 2024 and strongly negative in 2026. The 2026 Unsafe gross-return quality is negative for all 1/2/3/5m STAR50 candidates.

Therefore the current STAR50 implication for this strategy family is conservative:

- do not route Unsafe into a mechanically faster version of the same strategy;
- treat Unsafe primarily as a risk/admission state until a different strategy family earns its own evidence;
- do not infer `Unsafe = no trading` for all possible strategies, only that this specific accelerated family is not established.

## CSI1000

The full surface reveals one exploratory exception worth preserving:

**3-minute sampling/execution with the fixed physical ~60m filter / ~240m volatility memory, gated by Unsafe.**

This is a sampling/execution refinement candidate, not physical-clock contraction.

Unsafe results for this fixed-physical 3m candidate:

| year | gross bp / exposure minute | break-even one-way friction bp | net bp at 1bp one-way cost | exposure minutes |
|---:|---:|---:|---:|---:|
| 2022 | 2.286 | 4.573 | +21.436 total | 12 |
| 2023 | 0.555 | 2.499 | +8.996 total | 27 |
| 2024 | 0.482 | 1.590 | +35.413 total | 198 |
| 2025 | 0.404 | 1.258 | +6.700 total | 81 |
| 2026 replay | 0.810 | 1.546 | +12.012 total | 42 |

2021 has no eligible CSI1000 Unsafe exposure under the frozen support.

The 2021-2025 pooled break-even one-way friction is 1.740bp. Leave-one-active-year-out pooled break-even remains above roughly 1.55bp in every exclusion. The candidate's Unsafe gross bp per exposure minute is also above its NoEpisode value in every active calendar year 2022-2026.

However this candidate was identified after inspecting the complete registered Phase-2 surface. It is therefore **post-selection exploratory evidence**, not a confirmatory strategy. Do not optimize around 3m on the consumed data.

## Execution-cost implication

The CSI1000 candidate has a narrow cost margin. Its weakest active historical year in the current panel is 2025, with about 1.258bp break-even per one-way turnover; the already-opened 2026 replay is about 1.546bp.

This means a real tradable carrier must be evaluated before any economic promotion. The current outputs are index-open log-return abstractions and contain no futures basis, bid/ask spread, queueing, slippage, broker surcharge or asymmetric same-day close fee.

For an intraday carrier, the next study should use actual all-in execution semantics. If all-in one-way-equivalent friction is near or above ~1.25bp, the attractive CSI1000 cell is already at risk of disappearing in its weakest observed year.

## What Phase 2 changes in the research architecture

The working state router is now index-specific:

- STAR50: `Unsafe` is a risk/admission warning for this strategy family; no faster route is validated.
- CSI1000: preserve one **exploratory** candidate: `Unsafe -> 3m observation/execution cadence + fixed 60m/240m structural clock`.
- `Recovering` does not automatically restore or release a position; Clean remains disabled in the state model.

The general statement is no longer “high volatility means use a higher-frequency strategy.” It is:

> high volatility enlarges the short-horizon movement budget; whether that should be harvested by finer execution, a different strategy family, or not traded depends on the index and real transaction costs.

## Next frozen direction

Do not search more frequencies on 2021-2026. The next work should be:

1. freeze the CSI1000 fixed-physical 3m Unsafe candidate as a single post-selection candidate for the next independent snapshot after 2026-08-21;
2. run a fee-aware routing study that tries to reduce turnover without changing the 3m/60m/240m structural choice;
3. obtain actual CSI1000 tradable-carrier execution data (preferably IM futures bid/ask/trade data plus as-of fees) before claiming economic viability;
4. keep STAR50 in risk-control mode for this strategy family unless a separately preregistered alternative family is tested.
