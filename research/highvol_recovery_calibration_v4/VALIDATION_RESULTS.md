# HighVol recovery calibration v4 — reusable Validation result

Status: **SUPPORTED ON AVAILABLE NATIVE-5M VALIDATION COVERAGE / FULL-2026 COVERAGE OPEN**.

This is a risk-state probability calibration result, not a trading result.

## Frozen identity

Candidate: `shared_unsafe_recovering_age_recovery_probability_v4`.

The frozen Development table uses only current `UNSAFE/RECOVERING` state and fixed episode ages 5/15/30/45 minutes to estimate `P(NORMAL within next15m)`, with Beta(1,1)/Laplace smoothing. State thresholds and episode rules are unchanged from v3.

Development run `34414610302` fit 2,480 rows and passed all preregistered freeze gates. Artifact `10128564382`, ZIP SHA256 `0e67c583ed00d36b369bb9c2f1edcac3e5bce6e88caf54c5ad90f961bdc65ab2`.

Frozen probabilities (`UNSAFE` vs `RECOVERING`) are:

- 5m: 0.91% vs 6.47%;
- 15m: 1.55% vs 3.78%;
- 30m: 0.47% vs 5.51%;
- 45m: 27.80% vs 64.46%.

## Native-5m reusable Validation

Validation run `34414806977` used only native 5-minute rows for 2024 and 2025, with 2023 only as rolling warm-up. No refit or parameter change occurred.

Artifact `10128639805`, ZIP SHA256 `d36a2916beb75a44e8743503181db135222ce0bb89efcf6fd18e9388233473e0`.

Scored rows: 1,611.

| metric | frozen state×age table | frozen Development global baseline |
|---|---:|---:|
| Brier | 0.079211 | 0.135060 |
| LogLoss | 0.272333 | 0.441472 |

Annual Brier also improved in both available years:

- 2024: 0.077385 vs 0.131995;
- 2025: 0.081067 vs 0.138174.

By symbol:

- STAR50: Brier 0.077407 vs 0.131010 global baseline;
- CSI1000: Brier 0.080991 vs 0.139054.

Observed `P(Normal next15 | Recovering)` remained greater than `P(... | Unsafe)` at all 4/4 fixed age landmarks for each index.

All preregistered acceptance gates for the **available native-5m coverage** passed.

## Coverage limitation

The repository does not currently contain an authorized native cross-index 5-minute shard for 2026-01-01 through 2026-08-21. The available 2026 cross-index package is 1-minute (and separate 3-second observation data). This study intentionally did not resample those sources to manufacture a 5-minute Validation shard.

Therefore the correct authority is:

- calibration supported on 2024–2025 native-5m reusable Validation;
- **not yet a claim of complete Validation coverage through 2026-08-21**.

The missing 2026 native-5m coverage is a data-completion item, not a scientific failure.

## Interpretation

The state label alone is not the whole story: episode age materially changes recovery probability, especially near 45 minutes. But the small shared 2×4 table transfers well from 2021–2023 into 2024–2025 without refitting, supporting its use as a compact bottom-layer risk-process description.

This does not authorize a directional payoff, trade route, live risk reduction rule, or production deployment.

`production_authority=false`; `blackbox_queried=false`.
