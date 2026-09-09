# HighVol / Unsafe recovery hazard v3 — retained Development evidence

Status: **STATE SEPARATION SUPPORTED / RISK-STATE ONLY**.

Frozen Development run `34414238847` (`2021–2023`, 2020 warm-up only) used the inherited HighVol/Unsafe thresholds unchanged and no PnL, trading rule, Validation or BlackBox data. Artifact `10128425758`, ZIP SHA256 `e54538e5f933a7a3e1f2f06398a9a35e5c9e49e6ebedaf48625f0cd7a035dab9`.

Episode counts were 459 for STAR50 and 417 for CSI1000, with 2,480 active fixed-landmark observations having complete next-15-minute support.

Across the frozen 5m/15m/30m/45m episode-age landmarks, all 16 pooled recovery/persistence comparisons (`2 indices × 4 landmarks × 2 metrics`) ordered as intended: `RECOVERING` had higher near-term Normalization probability and `UNSAFE` had higher probability of remaining non-Normal. Fourteen of 16 also had the expected sign in at least 2 of 3 Development years.

At 45 minutes the separation is large and three-year consistent: STAR50 `P(Normal next15)` is 26.92% in `UNSAFE` vs 62.30% in `RECOVERING`; CSI1000 is 28.57% vs 67.06%.

Re-shock probability is not monotone in the same state label: the expected Unsafe>Recovering recurrence ordering appears at some early landmarks but reverses by 30–45 minutes. Therefore `UNSAFE/RECOVERING` is supported as a recovery/persistence state, **not** as a complete re-shock model.

Next in-scope step: probability calibration of `P(Normal within next15m)` from causal state/episode-age information, developed on 2021–2023 and frozen before reusable Validation.

Full protocol/runner/result remain on branch `research/highvol-recovery-hazard-v3-20260910`; frozen execution commit `7c1568cbff9c8399abec2d5b3007fb1cc950d661` and result commit `e7be701aaf8217916631840f693bd51eea258c84`.

`production_authority=false`; BlackBox not queried.
