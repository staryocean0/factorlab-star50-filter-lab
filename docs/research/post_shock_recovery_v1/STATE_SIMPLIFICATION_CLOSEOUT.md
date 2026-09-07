# Post-shock state simplification closeout

Date: 2026-09-07.

**Current conclusion: within the index-price information already examined, the durable post-shock state can remain one-dimensional.**

Primary state variable:

`recovery_ratio = RMS(last 5 completed 1m returns) / fixed pre-shock sigma_pre`

State machine:

`first shock -> episode {Unsafe <-> Recovering}`

with `Unsafe` at ratio >=1.5 after the initial five-minute warm-up, `Recovering` below 1.5, Unknown on missing/invalid support, and no online Clean.

## Tested modifiers that did not justify expanding the state

- elapsed time since the first shock;
- time since the latest Unsafe reading;
- pre-shock background sigma as a separate regime variable;
- background-sigma interaction with current recovery ratio;
- shock direction (up/down) and direction interaction;
- contemporaneous recovery state of the other headline index;
- static event amplitude / event-minute 3s path severity descriptors;
- replacing the five-minute window with two-minute or ten-minute alternatives.

None showed stable enough incremental value across the fixed evaluation structure to justify a new causal state dimension. Some individual metrics move slightly, but proper-score/event-cluster comparisons do not establish a stable gain.

Supporting notes:
- `STATE_SUFFICIENCY_RESULTS.md`
- `NORMALIZATION_STABILITY_RESULTS.md`
- `DIRECTION_STABILITY_RESULTS.md`
- `STATE_TRANSITION_EVIDENCE.md`
- `RISK_BURDEN_RESULTS.md`
- `STABLE_STATE_SPEC.md`

## What remains supported

1. Current recovery ratio ranks the following five-minute risk.
2. Current Unsafe also implies materially larger cumulative risk burden over the following fifteen minutes.
3. Recovering can reactivate to Unsafe; it is not a one-way decay process.
4. Recovering-low is safer but not Clean.
5. Boundary termination at lunch/close is censoring, not evidence of safety.

## Research discipline after closeout

Do not mine additional index-price modifiers on the already-consumed 2024-2025 data or the opened 2026-01-05..2026-08-21 snapshot. Further complexity should be considered only when:

- genuinely new same-semantics events after 2026-08-21 are available under the frozen next-snapshot protocol; or
- materially different information arrives under a new preregistered protocol.

The next useful task before new data arrive is validation-readiness planning: define event-count / support requirements and fixed acceptance outputs for the next independent snapshot, without changing the state itself.
