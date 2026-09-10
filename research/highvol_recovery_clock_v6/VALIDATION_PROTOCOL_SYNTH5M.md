# V6 recent-shock recovery clock — full reusable Validation protocol

User authorization on 2026-09-10 explicitly permits constructing 5m bars from the repository's 1m index bars; the user's existing 5m data are themselves constructed from 1m data.

## Candidate freeze

Candidate identity is frozen in `FROZEN_RECENT_SHOCK_TABLE.json`. No state threshold, shock rule, age bucket, probability, target, or symbol rule may change in Validation.

## 1m -> 5m construction contract

For each symbol and trading day independently:

1. order 1m rows by displayed Shanghai session time;
2. require complete morning and afternoon sessions of 120 rows each;
3. partition each half-session into 24 consecutive non-overlapping groups of 5 rows;
4. for the risk-state engine, set the synthesized 5m `close` equal to the fifth 1m row's `close` in each group;
5. carry the fifth source timestamp only as the ordering timestamp; do not interpolate, forward-fill, or use future rows;
6. produce exactly 48 synthesized 5m rows per complete trading day.

Before any 2026 Validation score is computed, this construction must be verified on 2023 against the existing repository 5m bars for both `000688.SH` and `000852.SH`. The guard requires identical trading-day support, identical row counts per day, and max absolute close difference <= 1e-9 after chronological alignment. Failure stops the workflow before 2026 scoring.

## Validation coverage

- 2024 and 2025: existing repository 5m bars.
- 2026: synthesize from the sealed cross-index 1m validation pack, restricted to its complete support through 2026-08-21.
- 2023 may be read only for the aggregation-equivalence guard, never for Validation scoring.
- No data after 2026-08-21 and no BlackBox material may be read.

## Frozen evaluation

Build the unchanged V3/V6 risk process and score every supported active non-shock episode row using the frozen recent-shock 8-cell probability table. Report pooled and annual Brier/LogLoss for 2024, 2025, and 2026 through 2026-08-21, plus observed `RECOVERING > UNSAFE` ordering by age bucket and symbol.

Compare the frozen V6 table against the frozen Development global event rate `0.24425812345034582` as a simple probability baseline. No refit is permitted.

## Acceptance

Full-coverage Validation support requires all of:

- synthesis equivalence guard passes on both symbols in 2023;
- at least 2,000 scored Validation rows across 2024-2026;
- pooled Brier below the frozen global-rate baseline;
- pooled LogLoss below the frozen global-rate baseline;
- Brier below the global-rate baseline in each of 2024, 2025, and 2026;
- for each symbol, observed recovery probability is higher in `RECOVERING` than `UNSAFE` in at least 3 of 4 age buckets across pooled 2024-2026;
- no refit/parameter change/PnL/trading rule/BlackBox access.

Passing supports the recent-shock recovery clock as a risk-state probability object only. `production_authority=false`.
