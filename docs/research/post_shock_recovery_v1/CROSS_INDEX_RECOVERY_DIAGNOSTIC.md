# Cross-index recovery increment diagnostic

Date: 2026-09-07. Exploratory consumed-history analysis. No 2026 tuning and no state-rule change.

## Question

After one index has already experienced a first shock, does the simultaneous short-horizon volatility state of the *other* index materially improve prediction of this index's next-five-minute recovery risk beyond the shocked index's own current recovery ratio?

This tests whether a common cross-index stress state should be added to the current `Unsafe -> Recovering` state machine.

## Construction

Use common 2024-2025 half-session/minute support for STAR50 and CSI1000.

At +5/+10/+15/+20 minute checkpoints after each frozen first shock:

- target current state: target trailing-5m RMS divided by the target's event-time `sigma_pre`;
- other-index state: other index trailing-5m RMS divided by the other index's own event-time preceding-30m sigma;
- outcome: target next-five-minute RMS divided by target `sigma_pre`.

All quantities are causal at the checkpoint. The existing 1.0/1.5 state boundaries are reused; no new threshold is selected.

## Conditional transition check

Across 286 2024-2025 checkpoints:

| Target current state | Other index not Unsafe: target next Unsafe | Other index Unsafe: target next Unsafe |
|---|---:|---:|
| Recovering-low | 8.1% (74) | 16.7% (6) |
| Recovering-high | 14.3% (84) | 22.2% (18) |
| Unsafe | 51.4% (37) | 50.7% (67) |

The recovering rows hint that common stress can matter, but the co-Unsafe cells are small. When the target is already Unsafe, the other index being Unsafe adds essentially no discrimination.

## Sequential 2024-fit / 2025 historical evaluation

A deliberately simple log-risk regression was fit on pooled 2024 checkpoints and evaluated on pooled 2025 checkpoints:

- raw target persistence (`next ~= current target ratio`): log-RMSE 0.471;
- linear calibration using target current ratio only: 0.445;
- same linear calibration plus other-index current ratio: **0.448**.

The other-index coefficient in the pooled 2024 fit is approximately -0.02 in log space, effectively zero.

By target index the sign is not stable:

- STAR50: adding CSI1000 produces a small 2025 RMSE improvement (about 0.470 -> 0.465);
- CSI1000: adding STAR50 worsens it (about 0.362 -> 0.394), with only a small 2025 event sample.

## Decision

Do **not** add a cross-index common-volatility term to the stable post-shock state score at this stage.

The useful common-market interpretation remains scientific context, but the current durable state variable should stay local and transparent:

`recovery_ratio = target trailing-5m RMS / target fixed pre-shock sigma_pre`

This negative result is valuable because it prevents the state machine from accumulating complexity without stable incremental evidence.

Future independent data can re-test cross-index increment under a pre-registered protocol, especially if a broader constituent cross-section becomes available. The current result does not imply cross-index stress is economically irrelevant; it only says the other headline index's own five-minute volatility state does not show a stable incremental forecasting benefit here.
