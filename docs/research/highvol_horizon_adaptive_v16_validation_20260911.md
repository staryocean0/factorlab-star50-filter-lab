# HighVol recovery V16 — reusable Validation authority (2026-09-11)

Status: **SUPPORTED**

The exact frozen V16 horizon-adaptive recovery surface was evaluated once on reusable Validation from 2024-01-01 through 2026-08-21. No probability was refit, no threshold or horizon was changed, no post-hoc rescue was used, and BlackBox was not queried.

## Frozen object

- `15m = current_state + time-since-most-recent-shock`
- `30m = current_state + time-since-most-recent-shock`
- `60m = time-since-most-recent-shock only`

Development authority:

- execution commit: `bcdc18d5886869865c6454fa323ebc6858090249`
- run: `34497737506`
- artifact: `10160511846`
- frozen surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`

Reusable Validation authority:

- execution commit: `198c3040182f500e7e8c576ee7fa5ade3b30c9fa`
- run: `34602527314`
- job: `103273044422`
- artifact: `10264689647`
- artifact SHA256: `e28a877d40c3bd2464b4f09b1078cdfae83a7ecebcc8bbd34fdb7bad4e8d82f5`

## Data boundary

Symbols: `000688.SH`, `000852.SH`.

Common Validation cohort: **5,908** rows:

- 2024: 2,339
- 2025: 2,201
- 2026 through 2026-08-21: 1,368

2026 5m bars were deterministically synthesized from the sealed one-minute Validation inputs. Before synthesis, the historical 2023 equivalence guard passed exactly for both indices: 242 common days, 11,616 rows, max absolute close difference `0.0` each. Each 2026 source contains 154 complete days through 2026-08-21 and yields 7,392 synthesized 5m rows per symbol.

## Frozen pooled comparison

Positive improvement means V16 beats the frozen age-only comparator.

| Horizon | V16 Brier | Age-only Brier | Brier improvement | V16 LogLoss | Age-only LogLoss | LogLoss improvement |
|---|---:|---:|---:|---:|---:|---:|
| 15m | 0.08294514 | 0.08563351 | **+0.00268837** | 0.28725883 | 0.29616317 | **+0.00890434** |
| 30m | 0.10267887 | 0.10573547 | **+0.00305660** | 0.35256999 | 0.36237693 | **+0.00980693** |
| 60m | 0.08810163 | 0.08810163 | **0.00000000** | 0.30953459 | 0.30953459 | **0.00000000** |

Annual Brier improvement over age-only:

- 2024: 15m `+0.00261691`, 30m `+0.00309722`, 60m `0.0`;
- 2025: 15m `+0.00215756`, 30m `+0.00176125`, 60m `0.0`;
- 2026 through cutoff: 15m `+0.00366459`, 30m `+0.00507124`, 60m `0.0`.

Thus 15m and 30m win annual Brier in all three Validation years. At 60m V16 is exactly the frozen age-only anchor row-by-row (`max_abs_prediction_diff=0.0`), removing the V14 crossover by the preregistered model structure rather than by post-hoc score selection.

Every scored row satisfies `p15 <= p30 <= p60`.

## Decision

`full_validation_supported=true`.

V16 is the current validated 5m multi-horizon recovery surface. It supports the horizon-dependent information structure established in Development: instantaneous `UNSAFE/RECOVERING` state carries stable incremental recovery information at 15m and 30m, while at 60m the stable object is recent-shock age only.

This is a risk-state annotation object, not a directional payoff strategy.

`blackbox_queried=false`.
`production_authority=false`.
