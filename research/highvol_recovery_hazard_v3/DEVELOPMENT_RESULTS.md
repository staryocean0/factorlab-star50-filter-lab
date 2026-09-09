# HighVol / Unsafe recovery hazard v3 — Development result

Status: **STATE SEPARATION SUPPORTED / RISK-STATE ONLY**.

This is not a trading result. No PnL, directional payoff, carrier mapping, Validation, or BlackBox data was used.

## Frozen execution

- Branch: `research/highvol-recovery-hazard-v3-20260910`
- Frozen execution commit: `7c1568cbff9c8399abec2d5b3007fb1cc950d661`
- Development Action run: `34414238847`
- Job: `102675383371`
- Artifact: `10128425758`
- Artifact ZIP SHA256: `e54538e5f933a7a3e1f2f06398a9a35e5c9e49e6ebedaf48625f0cd7a035dab9`
- Data boundary: 2020 warm-up; reported episodes only 2021–2023; both indices on common trading days; physical workflow excluded 2024+.
- Frozen landmarks: 5m, 15m, 30m, 45m after shock episode start.
- Frozen future window: next 15m.
- State thresholds unchanged from the retained HighVol/Unsafe engine.

Episode counts: STAR50 459; CSI1000 417. There were 2,480 active landmark observations with complete future-hazard support.

## Main result

For the two primary process-ordering metrics—near-term Normal recovery and continued non-Normal persistence—**all 16 pooled comparisons** (`2 symbols × 4 landmarks × 2 metrics`) ordered in the expected direction:

- `RECOVERING` had higher probability of reaching `NORMAL` in the next 15m than `UNSAFE`;
- `UNSAFE` had higher probability of still being non-Normal 15m later than `RECOVERING`.

Fourteen of these 16 pooled comparisons also had the expected direction in at least 2 of the 3 Development years.

### STAR50

| episode age | Unsafe: P(Normal next15) | Recovering: P(Normal next15) | recovery gap |
|---|---:|---:|---:|
| 5m | 0.00% | 4.59% | +4.59pp |
| 15m | 0.00% | 1.54% | +1.54pp |
| 30m | 0.00% | 3.08% | +3.08pp |
| 45m | 26.92% | 62.30% | +35.38pp |

The 5m, 15m and 45m recovery/persistence ordering was positive in all three years. At 30m the pooled ordering remained positive but two annual rows were tied at zero recovery for both relevant groups.

### CSI1000

| episode age | Unsafe: P(Normal next15) | Recovering: P(Normal next15) | recovery gap |
|---|---:|---:|---:|
| 5m | 0.00% | 8.12% | +8.12pp |
| 15m | 1.89% | 5.79% | +3.90pp |
| 30m | 0.00% | 7.43% | +7.43pp |
| 45m | 28.57% | 67.06% | +38.49pp |

The recovery/persistence ordering was positive in all three Development years at every frozen landmark.

## Recurrence is a different process dimension

The current state label does **not** provide a stable monotone ordering for re-shock probability.

Early in the episode the expected relation is often visible—for example at 15m, shock-before-Normal within the next 15m is 8.11% vs 4.25% for STAR50 Unsafe vs Recovering, and 18.87% vs 4.55% for CSI1000. But by 30m/45m the pooled recurrence ordering reverses: recurrent shock is low and sometimes more frequent in `RECOVERING` than `UNSAFE`.

Therefore `UNSAFE/RECOVERING` should be retained as a **recovery/persistence state**, not interpreted as a complete model of re-shock hazard.

## Process interpretation

The v2 descriptive result said shock-level Unsafe often ends quickly while complete Normalization commonly takes around an hour. V3 makes that more operational: conditional on an episode still being active, the distinction between `UNSAFE` and `RECOVERING` contains reproducible information about near-term Normalization, especially around the 45-minute stage.

This supports the next risk-only step: freeze a probability-calibration object for `P(Normal within next 15m)` using Development data, then evaluate calibration on reusable Validation without changing the underlying state thresholds.

It does **not** support converting the labels into a directional strategy or using the recurrence result as a trade trigger.

`production_authority=false`; `validation_queried=false`; `blackbox_queried=false`.
