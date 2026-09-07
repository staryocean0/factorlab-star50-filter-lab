# Continuous post-shock recovery score results

Date: 2026-09-07. Protocol: `RECOVERY_SCORE_PROTOCOL.md`.

**Result: the richer fixed recovery model does not beat simple short-horizon volatility persistence on 2025. Use current trailing activity as the primary Recovering score; do not add complexity yet.**

Fit pooled 2024, evaluate pooled 2025 at +5/+10/+15/+20 minute checkpoints. Test set: 70 rows from 20 events.

| Predictor | 2025 log-risk RMSE | Pearson | Spearman |
|---|---:|---:|---:|
| Fixed ridge recovery model | 0.461 | 0.404 | 0.449 |
| **Current trailing-5m risk persistence** | **0.440** | **0.623** | **0.659** |
| 2024 unconditional mean | 0.504 | n/a | n/a |

The same ordering holds descriptively in both indices; CSI1000-2025 has only 5 events and should not be overinterpreted.

The ridge model's high predicted-risk tercile does contain more realized danger (52.2% of rows have next-5m RMS >=1.5x background, versus 26.1% in its low tercile), so there is some ranking structure. However persistence is materially stronger and simpler.

## State implication

For the current research version:

- `Unsafe`: current trailing post-shock 5-minute RMS / pre-shock sigma >=1.5;
- `Recovering`: current ratio between 1.0 and 1.5, or below 1.0 but without a validated stable-release confirmation;
- `Clean`: no causal online promotion from the current evidence.

The recovery score should therefore remain the **current trailing-5m volatility ratio**, not a newly fitted multivariate model. This is a state score, not a safe-release guarantee.

No new data are required to maintain this score. A stronger online Clean transition would require genuinely more independent event samples or materially different information, rather than more tuning on the same 2024-2025 events.
