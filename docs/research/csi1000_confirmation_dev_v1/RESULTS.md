# CSI1000 one-minute confirmation Development study V1 — result

Status: **no confirmation candidate nominated**.

Actions run: `34218395159` (success). Development-only role guard passed. Validation and BlackBox were not queried.

## Pooled Development 2021-2023

| policy | trades | mean gross bp/trade | mean net after 1 bp/leg | one-way break-even bp |
|---|---:|---:|---:|---:|
| immediate benchmark | 104 | +2.7377 | +0.7377 | 1.3689 |
| wait1 + HighVol persists | 91 | +2.1647 | +0.1647 | 1.0824 |
| wait1 + HighVol persists + confirmation minute positive | 62 | +2.6538 | +0.6538 | 1.3269 |

## Annual Development failure

`wait1_persist`:
- 2021: 31 trades, net1 +0.0861 bp/trade.
- 2022: 28 trades, net1 +0.7291.
- 2023: 32 trades, net1 **-0.2530**.

`wait1_persist_positive`:
- 2021: 23 trades, net1 **-0.3813** bp/trade.
- 2022: 17 trades, net1 +2.6483.
- 2023: 22 trades, net1 +0.1946.

Both policies fail the frozen requirement that every Development year be positive after 1 bp per execution leg. Neither is eligible for reusable Validation.

## Conclusion

Do not add a one-minute confirmation requirement to the current research candidate. Waiting one minute does not create a stable improvement and can discard useful early-window opportunities. The immediate next-minute-open implementation remains the benchmark candidate.
