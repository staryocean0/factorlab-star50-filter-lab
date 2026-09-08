# CSI1000 long HighVol acceleration — Validation component diagnostic V1

The frozen candidate already passed its registered reusable Validation acceptance. This diagnostic is allowed to inspect Validation details under repository data-use policy V2. It does not change or promote the candidate and does not query BlackBox-V1.

Fixed execution for every comparison: long only, `NormalVol -> HighVol`, next-minute-open entry, 3-minute hold, same-half-session valid path, non-overlapping selected trades, 1 bp/leg primary friction.

Compare four predeclared component variants:

1. `base_long_highvol`: no slow-trend filter and no late-acceleration filter.
2. `slow30_only`: preceding non-overlapping 30m net return > 0; no late-acceleration filter.
3. `accel_only`: `tail2_share >= 0.60` and `tail1_share < 0.60`; no slow-trend filter.
4. `full_candidate`: both `slow30 > 0` and the acceleration filter.

Report 2024, 2025, 2026-through-2026-08-21 and pooled metrics. Also report a fixed-sign counterfactual `reverse_full_candidate = -gross(full_candidate)` only as a falsification.

No alternative threshold, holding period, direction, or slow window is searched in this diagnostic.
