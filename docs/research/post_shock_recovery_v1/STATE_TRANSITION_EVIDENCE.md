# Post-shock state transition evidence

Date: 2026-09-07. This note summarizes the already-frozen recovery thresholds; it does not tune them.

## Question

Does the current post-shock recovery ratio contain forward information about the next five minutes, or is it only a backward-looking description?

The frozen score is:

`recovery_ratio = RMS(last 5 completed 1m returns) / sigma_pre`

The already-registered display/state boundaries are:

- `Unsafe`: ratio >= 1.5
- `Recovering-high`: 1.0 <= ratio < 1.5
- `Recovering-low`: ratio < 1.0

`Recovering-high/low` are analytical sub-bands inside the single causal `Recovering` state. Neither band is an online `Clean` release.

For each first-shock episode, checkpoints at +5/+10/+15/+20 minutes compare the current trailing-five-minute ratio with the following five-minute realized ratio. Repeated checkpoints from the same event are therefore dependent; event-cluster bootstrap is used for the main contrast.

## 2024-2025 consumed-history transition matrix

286 evaluable checkpoints.

| Current band | Next Recovering-low | Next Recovering-high | Next Unsafe | Checkpoints |
|---|---:|---:|---:|---:|
| Recovering-low | 61.2% | 30.0% | **8.8%** | 80 |
| Recovering-high | 46.1% | 38.2% | **15.7%** | 102 |
| Unsafe | 11.5% | 37.5% | **51.0%** | 104 |

Thus an `Unsafe` checkpoint is about 5.8 times as likely to be followed by another Unsafe five-minute block as a `Recovering-low` checkpoint on this historical sample.

Event-cluster bootstrap, resampling whole first-shock episodes rather than individual checkpoints:

- Unsafe minus Recovering-low next-Unsafe probability: median +41.9 percentage points;
- 95% interval: **[+30.6, +52.6] percentage points**;
- relative-risk bootstrap median about 5.8; 95% interval approximately [3.1, 15.6].

The continuous ratio also ranks the next-five-minute realized ratio positively: Spearman correlation is about 0.40 in 2024, 0.64 in 2025, and 0.48 pooled.

## 2026 held-out historical validation snapshot

The thresholds above were frozen before the 2026 validation. The 2026-01-05..2026-08-21 pack supplies 41 evaluable +5/+10/+15/+20 checkpoints from 14 first-shock events.

| Current band | Next Recovering-low | Next Recovering-high | Next Unsafe | Checkpoints |
|---|---:|---:|---:|---:|
| Recovering-low | 60.0% | 20.0% | **20.0%** | 10 |
| Recovering-high | 33.3% | 22.2% | **44.4%** | 9 |
| Unsafe | 13.6% | 18.2% | **68.2%** | 22 |

The sample is small, but the ordering is preserved: higher current post-shock activity corresponds to materially higher forward risk.

Event-cluster bootstrap for Unsafe minus Recovering-low gives a median difference of about +46.7 percentage points with a very wide 95% interval of roughly [+13.4, +77.4] points, reflecting the small 2026 event count.

The continuous ratio's 2026 Spearman correlation with the following five-minute realized ratio is about 0.43, consistent in sign with both prior years.

## Interpretation

1. `recovery_ratio` is supported as more than a contemporaneous label: it carries short-horizon forward state information across 2024, 2025 and the fixed 2026 snapshot.
2. `Unsafe` is genuinely persistent. A current Unsafe reading does not merely describe the past five minutes; approximately half or more of observed checkpoints remain Unsafe in the next five minutes.
3. `Recovering-low` is materially safer than Unsafe, but is **not Clean**. Reactivation to Unsafe remains about 9% in pooled 2024-2025 and 20% in the small 2026 snapshot.
4. `Recovering-high` is an intermediate analytical band and may be shown in diagnostics, but it is not promoted to a separate release state.
5. These transition probabilities are empirical calibration summaries, not production probabilities. They must be refreshed only on genuinely new snapshots without retuning the frozen boundaries.

## State-machine implication

Keep the durable state abstraction:

`first shock -> Unsafe -> Recovering`

Within `Recovering`, the continuous ratio remains the primary output. For visualization only, ratio <1.0 may be called `Recovering-low` and 1.0..1.5 `Recovering-high`.

Do not enable `Clean`. The observed reactivation tail is exactly why a low current ratio is not sufficient for safe release.
