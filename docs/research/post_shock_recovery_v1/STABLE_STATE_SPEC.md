# Post-shock stable state specification

Date: 2026-09-07. Research status after 2024-2025 development and the held-out 2026-01-05..2026-08-21 historical validation.

## Stable research object

The repository now freezes the following as the supported market-state abstraction:

`observed first shock -> Unsafe -> Recovering score`

No causal online `Clean` transition is validated.

This is a market-risk state specification, not a trading rule, account action, production service, or fresh-OOS claim.

## Trigger

Use the already frozen operational first-shock definition. Do not retune the event threshold from later data.

When a qualifying first shock is observed at the close of its minute, start a post-shock episode. The episode is bounded to the same half-session; do not bridge lunch, close or overnight in this research version.

## Background anchor

Let `sigma_pre` be the frozen pre-shock background volatility used by the first-shock event definition. Keep it fixed for the episode so the recovery score has a stable denominator.

Do not replace it with future/session-wide volatility.

## State score

After enough post-shock observations exist, compute

`recovery_ratio(t) = RMS(last 5 completed 1-minute returns) / sigma_pre`.

Only completed minutes are used. Missing/repaired/quality-ineligible minute returns are Unknown; do not fill them as zero.

The ratio is the primary continuous Recovering score because it remained transparent and useful across the prior periods; richer fixed models did not dominate it stably across 2025 and 2026.

## State labels

- `Unsafe`: from the observed first shock until at least five post-shock completed minutes are available; afterwards whenever `recovery_ratio >= 1.5`.
- `Recovering`: `recovery_ratio < 1.5`, including values below 1.0, because no reliable online Clean-release rule has been validated.
- `Unknown`: required input is missing/quality-ineligible or the episode is truncated by the half-session boundary.
- `Clean`: disabled as an online state in this research version.

The 1.5 boundary is the previously registered risk-state threshold. Do not tune it on the 2026 validation outcomes.

## What is explicitly NOT allowed

- no fixed +10/+15/+20/+30 minute automatic release;
- no simple cooling rule promoted to Clean;
- no use of the frozen logistic/3s models as a hard release gate;
- no threshold/feature search on the 2026 snapshot;
- no trading/backtest conclusion from this state alone;
- no rewriting of the sealed 2021-2025 or 2026 validation manifests.

## Evidence boundary

The 2026 validation reproduced elevated post-shock risk, but online Clean-release rules remained unreliable. Therefore the durable result is state persistence and continuous recovery measurement, not safe-release timing.

Future research may reopen Clean only when either:

1. genuinely new independent events after the current 2026-08-21 source snapshot are available; or
2. materially different information is added (for example cross-sectional constituent state, true tradable-market quote/order-flow information, or other pre-registered non-price-history inputs).

Any such work must start in a new protocol/version and must not modify this frozen specification retroactively.
