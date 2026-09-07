# Post-shock stable state specification

Date: 2026-09-07. Research status after 2024-2025 development and the held-out 2026-01-05..2026-08-21 historical validation.

## Stable research object

The repository freezes the following supported market-state abstraction:

`observed first shock -> Unsafe -> Recovering score`

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
- adding the other headline index's simultaneous five-minute volatility state did not show stable incremental benefit.

## State labels

- `Unsafe`: from the observed first shock until at least five post-shock completed minutes are available; afterwards whenever `recovery_ratio >= 1.5`.
- `Recovering`: `recovery_ratio < 1.5`, including values below 1.0, because no reliable online Clean-release rule has been validated.
- `Unknown`: required input is missing/quality-ineligible or the episode is truncated by the half-session boundary.
- `Clean`: disabled as an online state in this research version.

The 1.5 boundary is the previously registered risk-state threshold. Do not tune it on the 2026 validation outcomes.

For analysis/visualization only, Recovering may be split into:

- `Recovering-high`: `1.0 <= recovery_ratio < 1.5`;
- `Recovering-low`: `recovery_ratio < 1.0`.

These are **not release states**. Historical transition evidence shows Recovering-low still has a non-zero reactivation tail back to Unsafe.

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

## What is explicitly NOT allowed

- no fixed +10/+15/+20/+30 minute automatic release;
- no simple cooling rule promoted to Clean;
- no use of the frozen logistic/3s models as a hard release gate;
- no static shock-severity grade promoted from event amplitude/path shape;
- no cross-index headline-volatility term added without future independent evidence;
- no substitution of trailing2 or trailing10 for the frozen trailing5 score from consumed results;
- no threshold/feature search on the 2026 snapshot;
- no trading/backtest conclusion from this state alone;
- no rewriting of the sealed 2021-2025 or 2026 validation manifests.

## Engineering implementation

Research reference implementation:

- `code/post_shock_state.py`
- `tests/test_post_shock_state.py`

The implementation deliberately has no online Clean state, holds `sigma_pre` fixed, rejects same/prior-minute observations, treats invalid inputs as Unknown, allows Recovering -> Unsafe reactivation, and terminates rather than bridging a session boundary.

## Evidence boundary

The 2026 validation reproduced elevated post-shock risk, but online Clean-release rules remained unreliable. Therefore the durable result is state persistence and continuous recovery measurement, not safe-release timing.

The next independent time-extension validation is pre-registered in `NEXT_SNAPSHOT_PROTOCOL.md`. It must be applied before outcome summaries from same-semantics data after 2026-08-21 are opened for this task.

Future research may reopen Clean only when either:

1. genuinely new independent events after the current 2026-08-21 source snapshot are available; or
2. materially different information is added (for example cross-sectional constituent state, true tradable-market quote/order-flow information, or other pre-registered non-price-history inputs).

Any such work must start in a new protocol/version and must not modify this frozen specification retroactively.
