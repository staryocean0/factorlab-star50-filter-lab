# Post-shock recovery state V1 protocol

Date: 2026-09-07. Base branch: `research/first-shock-seconds-v2-20260907`.

Goal: after an already-observed first-shock event, estimate how long short-horizon market risk remains elevated and define descriptive `Unsafe -> Recovering -> Clean` labels. This is consumed-history market-state research, not trading, fresh OOS, or production validation.

## Frozen event universe

Use the sealed V2 operational first-event definition and 2024/2025 evaluation decision tables for both indices. Do not redefine first events after seeing recovery results. Do not cross lunch/close or half-session boundaries.

## Primary recovery state

For each first event with pre-event background `sigma_pre`, and each integer minute lag k after the event close for which five future minute returns remain in the same half-session:

- compute `R5(k) = RMS(return_{k+1..k+5}) / sigma_pre`;
- `Unsafe` when `R5(k) >= 1.5`;
- `Recovering` when `1.0 <= R5(k) < 1.5`;
- `Clean-candidate` when `R5(k) < 1.0`.

A descriptive **release time** is the earliest lag k at which two consecutive non-overlapping 5-minute blocks are both below background (`R5_block < 1.0`). If no such pair occurs before the half-session ends, release is right-censored. This release label uses future information and is an outcome for later causal prediction; it is not itself an online signal.

Sensitivity thresholds are fixed at Unsafe ratios 1.25 and 2.0; the primary 1.5 result must be reported first. No threshold selection by best performance.

## Outputs

1. Risk-decay curve by lag 0..45 minutes: fraction Unsafe and median `R5(k)`, with denominators and censoring.
2. Release-time distribution: median, quartiles, share released by 5/10/15/30 minutes, and right-censor rate.
3. Results separately for 000688.SH / 000852.SH and 2024 / 2025, plus pooled-by-index summaries.
4. Repeat on `quiet_first` events from the sealed event taxonomy, without changing the primary universe.
5. Candidate causal release features, measured only up to decision time after the shock: event amplitude, sigma_pre, event-minute 3s path descriptors, and trailing post-event 1/2/5-minute realized activity. These features are only screened after the descriptive duration results are frozen.

## Interpretation

- `Unsafe` means future five-minute realized volatility remains at least 1.5x the pre-shock background; it does not mean a second extreme event must occur.
- No result may be described as pre-first-shock prediction.
- If recovery is mostly complete within five minutes, state gating should be short; if a material tail persists, a release model is justified.
- Missing or session-truncated futures are Unknown/censored, never Clean.
