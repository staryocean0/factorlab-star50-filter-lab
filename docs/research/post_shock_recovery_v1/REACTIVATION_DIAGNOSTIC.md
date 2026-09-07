# Post-shock reactivation diagnostic

Date: 2026-09-07. Consumed 2024-2025 history; no threshold tuning.

## Question

Once a post-shock episode first drops below the frozen Unsafe threshold, does it usually continue recovering monotonically, or does risk frequently reactivate?

Use the frozen rolling-five-minute ratio, updated every completed minute:

`recovery_ratio = RMS(last 5 completed 1m returns) / fixed sigma_pre`

- Unsafe: ratio >=1.5
- Recovering: ratio <1.5

Analyze up to the first 45 minutes after each first shock, within the same half-session only.

## Result

The state is **not monotone**.

Across the 2024-2025 event set:

- median first observed Recovering reading occurs about **6 minutes** after the shock among episodes that reach Recovering within the observable horizon;
- median number of Unsafe/Recovering threshold flips over the observed post-shock path is **2**;
- mean number of flips is about **2.7**;
- about **64%** of episodes that reach Recovering later return to Unsafe at least once within the observed path;
- about **38%** reactivate to Unsafe within ten minutes after their first Recovering reading.

The pattern is not confined to one index/year. The share with at least one threshold flip is high in every cell (roughly 71%-100% in the small annual samples).

Typical Recovering runs are longer than Unsafe bursts, but short unsafe reactivations remain common. This is consistent with the transition evidence showing a non-zero next-five-minute Unsafe probability even from Recovering-low.

## Interpretation

`first shock -> Unsafe -> Recovering` describes the episode's broad lifecycle, **not a one-way finite-state transition**.

The causal state machine must allow:

`Unsafe <-> Recovering`

until the half-session ends or a future independent protocol validates a true terminal Clean state.

This is also why the continuous ratio is more informative than presenting only the discrete label.

## Hysteresis decision

Do not add hysteresis from this consumed sample.

A hysteresis band might reduce display flicker, but it would also delay real Unsafe reactivation. Choosing entry/exit boundaries from the already-observed flip distribution would be another tuning step and has no independent validation.

Current implementation therefore keeps the exact frozen 1.5 threshold and allows immediate causal re-entry to Unsafe when the rolling five-minute ratio rises back above it.

For UI/research plots, show the continuous `recovery_ratio` together with the discrete state so threshold crossings are interpretable rather than hidden.
