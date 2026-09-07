# Post-shock multi-horizon risk-burden results

Date: 2026-09-07. Protocol: `RISK_BURDEN_PROTOCOL.md`. Actions run `34130759289` succeeded; three frozen tests passed.

**Conclusion: the current Unsafe state is associated with materially larger cumulative risk burden over the following 15 minutes, not only the next five-minute block. Recovering-low is safer but still not Clean. Recovering-high is not monotonically ordered at every year/horizon and remains display-only.**

## Pooled 2024

145 checkpoints from 52 first-shock episodes.

| Current band | Any Unsafe block in next 15m | Mean number of Unsafe 5m blocks (0..3) | Mean future ratio |
|---|---:|---:|---:|
| Recovering-low | 39.5% | 0.47 | 1.118 |
| Recovering-high | 31.4% | 0.47 | 1.106 |
| Unsafe | **58.9%** | **0.91** | **1.366** |

Event-cluster bootstrap, Unsafe minus Recovering-low:
- any-Unsafe probability: median +19.3 percentage points; 95% interval [-1.9, +40.6] points;
- future Unsafe-block share: median +14.2 percentage points; 95% interval **[+1.7, +27.7]** points.

The high/low display bands are not strictly monotone in 2024 on the 15-minute horizon, so no extra state boundary is inferred.

## Pooled 2025

52 checkpoints from 21 episodes.

| Current band | Any Unsafe block in next 15m | Mean number of Unsafe 5m blocks (0..3) | Mean future ratio |
|---|---:|---:|---:|
| Recovering-low | **11.1%** | **0.11** | 0.793 |
| Recovering-high | 55.0% | 0.80 | 1.217 |
| Unsafe | **69.6%** | **1.43** | **1.500** |

Unsafe minus Recovering-low event-cluster bootstrap:
- any-Unsafe probability: median +58.4 points; 95% interval **[+14.6, +85.2]**;
- Unsafe-block share: median +43.6 points; 95% interval **[+19.4, +65.2]**.

## 2026 descriptive replay

28 checkpoints from 10 episodes had a full following 15-minute horizon. This snapshot was already opened and is not an independent new confirmation.

| Current band | Any Unsafe block in next 15m | Mean number of Unsafe 5m blocks (0..3) |
|---|---:|---:|
| Recovering-low | 33.3% | 0.67 |
| Recovering-high | 60.0% | 1.20 |
| Unsafe | **88.2%** | **1.82** |

The ordering is directionally strong, but the event-cluster intervals are wide and include zero because only nine episodes contribute to the Unsafe-vs-low bootstrap comparison.

## Implication

The durable score should continue to be interpreted as a **risk-burden state**, not a binary one-step forecast. A current Unsafe reading means elevated risk can persist across several subsequent five-minute blocks.

Recovering-low is materially safer in the stronger 2025 evidence, yet even there and in 2026 it is not risk-free. This is consistent with keeping online Clean disabled.

Do not promote Recovering-high as a separate causal state: its 15-minute ordering is not stable enough in 2024. Continue to expose the continuous recovery ratio as the main output, with high/low bands only for visualization.

No threshold, event definition, window length, state transition or trading policy is changed by this result.
