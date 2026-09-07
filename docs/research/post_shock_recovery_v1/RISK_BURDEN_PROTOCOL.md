# Post-shock multi-horizon risk-burden protocol

Date: 2026-09-07. Consumed-history descriptive diagnostic; no state tuning and no Clean research.

Question: does the frozen current recovery state rank not only the next five-minute block, but the **cumulative risk burden over the following 15 minutes**?

For each frozen first-shock episode and checkpoints +5/+10/+15 minutes, compute the current frozen recovery ratio from the trailing five completed one-minute returns. Then compute three fixed, non-overlapping future five-minute RMS/sigma_pre ratios covering the next 15 minutes.

Frozen outputs:
- number/share of the three future blocks that are Unsafe (`ratio >=1.5`);
- whether any future block is Unsafe;
- mean future ratio and maximum future ratio.

Use existing display bands only: Recovering-low <1.0, Recovering-high 1.0..1.5, Unsafe >=1.5. No new cutoffs.

Report STAR50/CSI1000 and 2024/2025/2026 separately and pooled. Event-cluster bootstrap (10,000 repeats, seed 20260907) compares current Unsafe versus Recovering-low for (a) any Unsafe in next 15m and (b) mean unsafe-block share. Whole first-shock episodes are resampled.

Interpretation: this test may support the recovery ratio as a multi-horizon risk-burden score. It must not create a Clean release, modify the five-minute window, or tune thresholds. The already-opened 2026 snapshot is descriptive consistency only.
