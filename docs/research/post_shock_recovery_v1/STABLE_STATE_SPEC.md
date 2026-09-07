# Post-shock stable state specification

Date: 2026-09-07. Research status after 2024-2025 development and the held-out 2026-01-05..2026-08-21 historical validation.

## Stable research object

The repository freezes the following supported market-state abstraction:

`observed first shock -> post-shock episode {Unsafe <-> Recovering}`

The episode starts in Unsafe. Thereafter it may move repeatedly between Unsafe and Recovering as the rolling state changes. The broad lifecycle still reads “first shock -> Unsafe -> recovery”, but it is not a one-way finite-state chain.

No causal online `Clean` transition is validated.

This is a market-risk state specification, not a trading rule, account action, production service, or fresh-OOS claim.

## Trigger

Use the already frozen operational first-shock definition. Do not retune the event threshold from later data.

When a qualifying first shock is observed at the close of its minute, start a post-shock episode. The episode is bounded to the same half-session; do not bridge lunch, close or overnight in this research version.

Do not add a static `mild/severe shock` tier. Event amplitude, pre-shock context and event-minute 3s path descriptors have not shown stable enough incremental severity information to justify such a state.

## Background anchor

Let `sigma_pre` be the frozen pre-shock background volatility used by the first-shock event definition. Keep it fixed for the episode so the recovery score has a stable denominator.

Do not replace it with future/session-wide volatility or silently re-anchor it after a few high-volatility minutes.

## State score

After enough post-shock observations exist, compute

`recovery_ratio(t) = RMS(last 5 completed 1-minute returns) / sigma_pre`.

Only completed minutes are used. Missing/repaired/quality-ineligible minute returns are Unknown; do not fill them as zero.

The five-minute window may be **updated every completed minute**. Window length and update cadence are different concepts: the supported implementation is a rolling five-minute score refreshed once per minute.

The ratio is the primary continuous Recovering score because:

- richer fixed models did not dominate it stably across 2025 and 2026;
- a two-minute window is materially noisier;
- a ten-minute window has not produced stable enough improvement to justify the extra lag;
- adding the other headline index's simultaneous five-minute volatility state did not show stable incremental benefit;
- adding elapsed time since the shock or time since the latest Unsafe reading did not improve the fixed 2025 evaluation and was also worse in the already-opened 2026 replay (`STATE_SUFFICIENCY_RESULTS.md`).

Do not add a separate hidden clock/dwell variable to the durable state representation from current evidence.

## State labels

- `Unsafe`: from the observed first shock until at least five post-shock completed minutes are available; afterwards whenever `recovery_ratio >= 1.5`.
- `Recovering`: `recovery_ratio < 1.5`, including values below 1.0, because no reliable online Clean-release rule has been validated.
- `Unknown`: required input is missing/quality-ineligible or the episode is truncated by the half-session boundary.
- `Clean`: disabled as an online state in this research version.

The 1.5 boundary is the previously registered risk-state threshold. Do not tune it on the 2026 validation outcomes.

For analysis/visualization only, Recovering may be split into:

- `Recovering-high`: `1.0 <= recovery_ratio < 1.5`;
- `Recovering-low`: `recovery_ratio < 1.0`.

These are **not release states**. Historical transition evidence shows Recovering-low still has a non-zero reactivation tail back to Unsafe. The high/low bands are not guaranteed to be strictly monotone on every longer horizon and therefore must not be promoted to separate causal states.

## Forward-state evidence

At +5/+10/+15/+20 checkpoints, the current state has forward information for the following five minutes.

Pooled 2024-2025 next-Unsafe probability:

- Recovering-low: about 8.8%;
- Recovering-high: about 15.7%;
- Unsafe: about 51.0%.

The fixed 2026 snapshot preserves the ordering, though with only 14 events:

- Recovering-low: 20.0%;
- Recovering-high: 44.4%;
- Unsafe: 68.2%.

This is why the ratio is retained as a state score and why a low current ratio is not promoted to Clean.

See `STATE_TRANSITION_EVIDENCE.md` for counts, event-cluster bootstrap and limitations.

Minute-by-minute historical paths also show that recovery is frequently interrupted: among 2024-2025 episodes that first reach Recovering, about 64% later return to Unsafe at least once within the observed path, and about 38% reactivate within ten minutes of the first Recovering reading. See `REACTIVATION_DIAGNOSTIC.md`.

The score also carries multi-step risk-burden information (`RISK_BURDEN_RESULTS.md`). In pooled 2025, current Unsafe checkpoints had at least one Unsafe block in the following 15 minutes about 69.6% of the time versus 11.1% for Recovering-low, and averaged about 1.43 versus 0.11 Unsafe five-minute blocks out of the next three. The already-opened 2026 replay was directionally similar but small. The 2024 15-minute high/low display-band ordering was not strictly monotone, reinforcing that the continuous ratio—not an expanded categorical state machine—should remain the primary output.

## What is explicitly NOT allowed

- no monotone one-way lock from Unsafe into Recovering;
- no fixed +10/+15/+20/+30 minute automatic release;
- no simple cooling rule promoted to Clean;
- no use of the frozen logistic/3s models as a hard release gate;
- no static shock-severity grade promoted from event amplitude/path shape;
- no cross-index headline-volatility term added without future independent evidence;
- no substitution of trailing2 or trailing10 for the frozen trailing5 score from consumed results;
- no elapsed-time/dwell-time hidden state added from consumed results;
- no hysteresis boundary tuned from the already-observed state flips;
- no threshold/feature search on the 2026 snapshot;
- no trading/backtest conclusion from this state alone;
- no rewriting of the sealed 2021-2025 or 2026 validation manifests.

## Engineering implementation

Research reference implementation:

- `code/post_shock_state.py`
- `tests/test_post_shock_state.py`

The implementation deliberately has no online Clean state, holds `sigma_pre` fixed, rejects same/prior-minute observations, treats invalid inputs as Unknown, allows Recovering -> Unsafe reactivation, and terminates rather than bridging a session boundary.

Nine boundary/causality tests passed in the cloud session before the files were written to GitHub.

Reusable diagnostics are also frozen for future replay:

- `code/state_transition_eval.py` / transition evaluator tests;
- `code/state_sufficiency.py` / `tests/test_state_sufficiency.py`;
- `code/risk_burden.py` / `tests/test_risk_burden.py`.

## Evidence boundary

The 2026 validation reproduced elevated post-shock risk, but online Clean-release rules remained unreliable. Therefore the durable result is state persistence and continuous recovery measurement, not safe-release timing.

The next independent time-extension validation is pre-registered in `NEXT_SNAPSHOT_PROTOCOL.md`. It must be applied before outcome summaries from same-semantics data after 2026-08-21 are opened for this task.

Future research may reopen Clean only when either:

1. genuinely new independent events after the current 2026-08-21 source snapshot are available; or
2. materially different information is added (for example cross-sectional constituent state, true tradable-market quote/order-flow information, or other pre-registered non-price-history inputs).

Any such work must start in a new protocol/version and must not modify this frozen specification retroactively.
