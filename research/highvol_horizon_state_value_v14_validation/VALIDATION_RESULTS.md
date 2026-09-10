# HighVol horizon-specific state value V14 — full Validation results

Status: **REJECTED AS A JOINT 15/30/60M HORIZON SURFACE**

This is a frozen reusable Validation of the Development-nominated `state + recent-shock age` recovery surface against the frozen `age-only` comparator. No probability was refit and no horizon was selected after inspection.

## Authority

- Development execution commit: `a9223748933fc842a68865a3837e24f49f014691`
- Development run: `34454169246`
- Development artifact: `10142758729`
- frozen surface blob: `be06a4988fb4a602e2b72d115268c926421aa1f5`
- Validation execution commit: `b93f9eb6129e12c49987a75f7af122f8d161c111`
- Validation run: `34493954221`
- Validation artifact: `10158985790`
- Validation artifact SHA256: `513821db8709a128f2d3bcb30d368ecd951b8e3d8511eb7d4a20b2c63d0e2271`

## Data boundary

Validation covers 2024-01-01 through 2026-08-21 for `000688.SH` and `000852.SH`.

2026 native 5m was deterministically synthesized from the sealed one-minute Validation inputs only after the already-authorized 2023 equivalence guard passed exactly for both indices:

- `000688.SH`: 242 common 2023 days, 11,616 rows, max absolute close difference `0.0`;
- `000852.SH`: 242 common 2023 days, 11,616 rows, max absolute close difference `0.0`.

The sealed 2026 inputs end at 2026-08-21 and produced 154 complete trading days / 7,392 synthesized 5m rows per symbol. BlackBox was not queried.

## Frozen-cohort results

Common Validation cohort: **5,908** rows.

Year counts:

- 2024: 2,339
- 2025: 2,201
- 2026 through 2026-08-21: 1,368

Pooled comparison, positive values mean the frozen `state + age` surface improved over frozen `age-only`:

| Horizon | State+age Brier | Age-only Brier | Brier improvement | State+age LogLoss | Age-only LogLoss | LogLoss improvement |
|---|---:|---:|---:|---:|---:|---:|
| 15m | 0.082945 | 0.085634 | **+0.002688** | 0.287259 | 0.296163 | **+0.008904** |
| 30m | 0.102679 | 0.105735 | **+0.003057** | 0.352570 | 0.362377 | **+0.009807** |
| 60m | 0.089035 | 0.088102 | **-0.000934** | 0.314358 | 0.309535 | **-0.004823** |

Annual Brier win count for `state + age` over `age-only`:

- 15m: **3 / 3**
- 30m: **3 / 3**
- 60m: **0 / 3**

The 60m reversal is not confined to one Validation year: state+age Brier is worse than age-only in 2024, 2025 and 2026 through the cutoff.

## Decision

`full_validation_supported = false`.

The preregistered V14 object was a joint 15/30/60m horizon surface. It therefore fails because the 60m horizon does not preserve incremental state value. The 15m and 30m results remain valid evidence that current `UNSAFE/RECOVERING` state contains near-horizon information beyond recent-shock age, but they **must not** be post-hoc promoted as a rescued V14 candidate.

Scientific implication for new Development work: test the hypothesis that instantaneous state is a **near-term recovery modifier**, whereas at longer horizons recent-shock age dominates. Any next model must be formulated and evaluated in Development before Validation is reused.

No PnL, payoff, routing, position sizing or trading rule was evaluated. `production_authority=false`; `blackbox_queried=false`.
