# HighVol recovery calibration v4 — retained risk-state evidence

Status: **SUPPORTED ON 2024–2025 NATIVE-5M REUSABLE VALIDATION; 2026 NATIVE-5M COVERAGE OPEN**.

This is a bottom-layer risk-state probability result, not a trading strategy.

Frozen Development object: one shared 8-cell table for STAR50 and CSI1000, using only current `UNSAFE/RECOVERING` state and shock-episode age 5/15/30/45 minutes to estimate `P(NORMAL within next 15m)`. State thresholds are unchanged; probabilities use `(successes+1)/(n+2)` Laplace smoothing.

Development run `34414610302` used 2,480 2021–2023 rows and passed all freeze gates. Frozen probabilities (`UNSAFE` vs `RECOVERING`) were 0.91% vs 6.47% at 5m, 1.55% vs 3.78% at 15m, 0.47% vs 5.51% at 30m, and 27.80% vs 64.46% at 45m. Artifact `10128564382`, SHA256 `0e67c583ed00d36b369bb9c2f1edcac3e5bce6e88caf54c5ad90f961bdc65ab2`.

Frozen reusable Validation run `34414806977` used native 5m data for 2024–2025 only, with no refit. On 1,611 rows, Brier was 0.079211 vs 0.135060 for the frozen Development global-probability baseline; LogLoss was 0.272333 vs 0.441472. Brier improved separately in both 2024 and 2025 and for both indices. Observed `Recovering > Unsafe` recovery ordering held at all 4/4 fixed landmarks for STAR50 and all 4/4 for CSI1000. Artifact `10128639805`, SHA256 `d36a2916beb75a44e8743503181db135222ce0bb89efcf6fd18e9388233473e0`.

Coverage limitation: current authorized cross-index 2026 package does not contain native 5m rows through 2026-08-21. No 1m-to-5m resampling was performed. Therefore this result cannot be described as complete Validation through the policy endpoint until native 5m 2026 coverage is supplied.

Scientific interpretation: `UNSAFE/RECOVERING + episode age` is supported as a compact, transferable recovery-process description. It does not fully model re-shock recurrence risk; that remains a separate research dimension.

Full executable evidence remains on branches `research/highvol-recovery-calibration-v4-20260910` and `research/highvol-recovery-calibration-v4-validation-20260910`.

`production_authority=false`; BlackBox not queried.
