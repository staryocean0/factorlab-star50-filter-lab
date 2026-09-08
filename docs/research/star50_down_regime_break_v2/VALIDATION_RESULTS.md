# STAR50 downside accelerated regime-break V2 — Validation result

Status: **FAIL** under the frozen primary Validation acceptance rule.

Candidate: `star50_downside_accelerated_regime_break_v2`

Candidate SHA256: `6ed7e13804d27d375e5efe388bf0c6414e7a08cf01eeec65cfe7e4079da7a1fd`

Evidence run: GitHub Actions run `34226567654`, job `102062026620`, head commit `0a151b6401470243c07d88c715694937c69de60e`.

Data role: reusable Validation/tuning evidence, `2024-01-01` through `2026-08-21`. Candidate fitting on Validation: false. BlackBox queried: false.

The workflow physically checked out only STAR50 `2024.parquet`, `2025.parquet`, and the bounded `2026.parquet`. The 2026 manifest reports `actual_last_day=2026-08-21` and `post_snapshot_rows=0`.

## Frozen rule was unchanged

- `NormalVol -> HighVol`;
- preceding non-overlapping 30-minute net return > 0;
- recent 5-minute net return < 0;
- 5-minute efficiency >= 0.60;
- `tail2_share >= 0.50`;
- no tail1 condition;
- short next minute open;
- fixed 3-minute hold;
- same half-day/session, valid complete path, non-overlapping;
- 1 bp per leg primary cost.

## Results

| period | trades | gross bp/trade | net bp/trade @1bp/leg | one-way break-even bp |
|---|---:|---:|---:|---:|
| 2024 | 11 | 19.5501 | 17.5501 | 9.7750 |
| 2025 | 20 | -1.1636 | -3.1636 | -0.5818 |
| 2026 | 9 | -10.5433 | -12.5433 | -5.2716 |
| pooled | 40 | 2.4222 | 0.4222 | 1.2111 |

Pooled gross median: `-1.6495 bp/trade`; gross hit rate: `45.0%`.

Trading-day block bootstrap of net return at 1 bp per leg, 10,000 draws, 39 trading-day blocks: mean `+0.4222 bp/trade`, 95% interval `[-6.6666, +8.8411] bp/trade`. This was pre-registered as report-only, not an acceptance gate.

## Primary acceptance

- total trades >= 30: PASS (`40`);
- pooled net @1bp/leg > 0: PASS (`+0.4222`);
- at least two of 2024/2025/2026 year slices net-positive: **FAIL** (`1/3`);
- pooled one-way break-even > 1bp: PASS (`1.2111`).

Overall primary result: **FAIL**.

The failure is specifically cross-period instability: a very strong 2024 is not reproduced in 2025 or 2026. This candidate is rejected as a validated module even though the pooled average remains slightly positive.

## Anti-rescue decision

Do not change `tail2>=0.50`, `efficiency>=0.60`, or the fixed 3-minute hold to rescue V2 inside Validation. Do not add a tail1/confirmation filter and call the same candidate validated. Detailed Validation diagnosis may only generate a new hypothesis, which must return to Development for development and freeze before any later Validation test.

Validation artifact ZIP SHA256 reported by Actions: `7c183d416f2dbcdc66de11357cd1eb13c53eb415208b3eb10d4ad9e8db125dda`; artifact ID `10055960559`.
