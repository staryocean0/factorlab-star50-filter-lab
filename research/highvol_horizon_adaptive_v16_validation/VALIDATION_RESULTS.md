# HighVol recovery V16 — reusable Validation results

Status: **SUPPORTED**

The exact frozen V16 horizon-adaptive recovery surface was evaluated once on reusable Validation from 2024-01-01 through 2026-08-21. No probability was refit, no threshold or horizon was changed, no post-hoc rescue was used, and BlackBox was not queried.

## Frozen authority

- Development branch: `research/highvol-horizon-adaptive-surface-v16-20260910`
- Development execution commit: `bcdc18d5886869865c6454fa323ebc6858090249`
- Development run: `34497737506`
- Development artifact: `10160511846`
- frozen surface Git blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`
- Validation execution commit: `198c3040182f500e7e8c576ee7fa5ade3b30c9fa`
- Validation run: `34602527314`
- Validation job: `103273044422`
- Validation artifact: `10264689647`
- Validation artifact SHA256: `e28a877d40c3bd2464b4f09b1078cdfae83a7ecebcc8bbd34fdb7bad4e8d82f5`

## Data boundary and synthesis guard

Validation uses `000688.SH` and `000852.SH` only.

2026 native 5m was deterministically synthesized from the sealed one-minute Validation inputs only after the historical equivalence guard reproduced 2023 native 5m close exactly for both symbols:

- `000688.SH`: 242 common 2023 days, 11,616 rows, max absolute close difference `0.0`;
- `000852.SH`: 242 common 2023 days, 11,616 rows, max absolute close difference `0.0`.

The sealed 2026 sources are the authorized blobs:

- `000688.SH`: `4626fb307bbcae1c417ddcd69ac694cf322c8bbc`;
- `000852.SH`: `8de5cd3caab99dbacae229a2c87f15c4ff2f8558`.

For each symbol they cover 154 complete trading days from 2026-01-05 through 2026-08-21, with 36,960 one-minute rows and 7,392 synthesized 5m rows. No post-cutoff data entered the physical or measured cohort.

## Validation cohort

Common scored rows: **5,908**.

- 2024: 2,339
- 2025: 2,201
- 2026 through 2026-08-21: 1,368

Every scored row preserved the frozen cumulative ordering `p15 <= p30 <= p60`; the 60m V16 prediction was exactly the frozen age-only anchor row-by-row.

## Pooled frozen comparison

Positive improvement means V16 beats the frozen age-only comparator.

| Horizon | V16 Brier | Age-only Brier | Brier improvement | V16 LogLoss | Age-only LogLoss | LogLoss improvement |
|---|---:|---:|---:|---:|---:|---:|
| 15m | 0.08294514 | 0.08563351 | **+0.00268837** | 0.28725883 | 0.29616317 | **+0.00890434** |
| 30m | 0.10267887 | 0.10573547 | **+0.00305660** | 0.35256999 | 0.36237693 | **+0.00980693** |
| 60m | 0.08810163 | 0.08810163 | **0.00000000** | 0.30953459 | 0.30953459 | **0.00000000** |

The 60m row-level prediction difference versus age-only is exactly `0.0`, so the former V14 60m crossover is removed by the preregistered horizon-adaptive construction rather than hidden by a post-hoc score rule.

## Annual stability

Brier improvement over frozen age-only:

| Year | 15m | 30m | 60m |
|---|---:|---:|---:|
| 2024 | +0.00261691 | +0.00309722 | 0.00000000 |
| 2025 | +0.00215756 | +0.00176125 | 0.00000000 |
| 2026 through cutoff | +0.00366459 | +0.00507124 | 0.00000000 |

Annual Brier win counts are therefore `15m = 3/3`, `30m = 3/3`, while `60m = 0/3` by exact equality as designed.

## Decision

`full_validation_supported = true`.

V16 is now the validated 5m recovery surface:

- `15m = current_state + time-since-most-recent-shock`;
- `30m = current_state + time-since-most-recent-shock`;
- `60m = time-since-most-recent-shock only`.

All preregistered acceptance gates passed. This establishes reusable Validation support for the horizon-dependent information structure without granting production authority.

No PnL, payoff, routing, position sizing, trading rule, or BlackBox query was performed.

`production_authority=false`.
`blackbox_queried=false`.
