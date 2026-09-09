# R1_B temporal execution theory program review — 2026-09-08

Identity under review: `rmr_R1B_temporal_impulse_completion_v1`

Status: **APPROVED FOR ONE DEV-ONLY IMPLEMENTATION TEST**

Production authority: `false`

## Authority and motivation

The completed mechanism-to-execution diagnostic established that the certified R1_B mechanism is statistically real but the closed next-minute / original structural-boundary / 10bp execution mapping is not viable. The same diagnostic showed a broad delayed positive fixed-markout term structure and slow structural resolution for R1_B. Those observations motivate a temporal-path theory, but they do **not** authorize selecting 120 or 240 bars.

This review therefore starts from mechanism structure, not from a chosen markout horizon.

## Causal mechanism statement

R1_B is the certified `S2-inside-S3` trend-parent pullback mechanism.

A qualifying R1_B event is observed only after an S2 wave opposite the intact S3 parent direction has been causally confirmed. Under the existing directional-change engine, confirmation of that counter-parent S2 wave is also the moment at which the detector switches into a new S2 wave running in the parent direction.

The new theory is:

> If the S3 parent remains intact, the temporal economic manifestation of R1_B is not necessarily the first touch of the old pullback start. It is one complete post-pullback S2 restoration impulse in the parent direction. A causal observer only knows that this impulse has completed when the next parent-aligned S2 wave is itself confirmed by the existing S2 directional-change rule.

This is a state-transition timing hypothesis. It uses the already-certified scale hierarchy and does not introduce a new indicator family.

## Single approved candidate

Candidate ID: `R1B_S2_PARENT_IMPULSE_CONFIRM_EXIT`

For every certified R1_B event:

1. Population: exactly the existing R1_B `S2-inside-S3` event engine and non-overlap convention.
2. Direction: frozen R1_B parent direction.
3. Entry: next observed 1m close after the certified R1_B confirmation bar, unchanged from the completed diagnostic.
4. Entry validity: the original recovery/failure interval must still contain the next-bar entry; otherwise the event is `entry_invalid` and creates no return path.
5. Temporal completion: locate the first subsequent **S2 wave in the parent direction** whose `confirm_idx` is after the R1_B confirmation. Candidate success exit is the observed close at that S2 wave's `confirm_idx`. The unobservable wave extreme/end price may never be used as an exit.
6. Parent failure: before temporal completion, if price crosses the original frozen R1_B S3 structural failure boundary, exit at the first observed crossing close and classify `parent_failure`.
7. Safety censor: if neither completion nor parent failure occurs within the inherited 1200 observed bars / available role boundary, exit at the horizon close and classify `censored`.
8. Cost: fixed 10bp round trip, unchanged.
9. No probability threshold or probability-based sizing is allowed.
10. Returns are evaluated event-by-event. Overlapping hypothetical event returns do not imply portfolio concurrency or production position sizing.

## Why this is materially different from the closed R1 economic family

The closed family treated restoration as a binary first-passage payoff between the pullback-start target and a parent structural failure boundary. The candidate above changes the economic object itself: restoration is represented as completion of the next causal lower-scale impulse aligned with the intact higher-scale parent.

It does **not** change:

- event definition;
- S2/S3 thresholds;
- parent features or frozen R1 mechanism;
- next-bar entry convention;
- 10bp cost;
- parent structural failure boundary;
- 1200-bar safety cap.

There is no horizon search and no target optimization.

## Explicitly forbidden

- selecting 120 or 240 bars, or any other hold horizon, from prior markouts;
- probability cutoffs, probability sizing or expected-return filters;
- entry-delay search;
- stop/target search;
- changing the 10bp cost assumption;
- changing S2/S3 scales;
- year, regime or time-of-day selection;
- using the S2 wave extreme/end price as a noncausal exit;
- refitting R1;
- opening VALIDATION before the DEV decision is recorded;
- any BLACKBOX access or query #4;
- portfolio optimization;
- production declaration.

## DEV-only decision contract

The first empirical step reads only DEV `2015-01-05 .. 2020-12-31`.

Report the candidate and the closed structural-resolution baseline on the same next-bar-tradeable R1_B events:

- event and tradeable counts;
- mean/median gross and net return;
- win rate;
- exit-class counts and rates;
- mean/median/p90 holding bars;
- annual 2015–2020 mean net return;
- annual candidate-minus-baseline mean net return.

The candidate is `DEV_READY_FOR_VALIDATION_FREEZE` only if all four predeclared conditions hold:

1. pooled candidate mean net return > 0 after 10bp;
2. pooled candidate mean net return > pooled baseline mean net return;
3. pooled candidate median net return > 0;
4. candidate annual mean net return > 0 in at least 4 of the 6 DEV calendar years.

Otherwise the identity closes on DEV and VALIDATION remains unopened for this candidate.

These are viability gates, not tunable parameters.

## If DEV passes

Only after a recorded DEV pass may a separate VALIDATION execution freeze be written. That freeze must preserve the candidate exactly as defined here and may not use DEV to search alternative wave scales, horizons, exits or thresholds.

The intended VALIDATION gate, if reached, is stricter and will require pooled positive net, improvement over the same baseline, positive median net, and positive annual mean net in at least 4 of 5 years. It will be frozen before any candidate VALIDATION output is inspected.

## BLACKBOX

BLACKBOX is outside this review. Query count remains 3. Query #4 is neither authorized nor scheduled.
