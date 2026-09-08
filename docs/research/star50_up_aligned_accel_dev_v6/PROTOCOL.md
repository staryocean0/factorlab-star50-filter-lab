# STAR50 aligned upside acceleration Development V6

Role: **Development-only redevelopment of a Validation-informed mechanism hypothesis**.

The prior STAR50 downside-break V2 failed reusable Validation, and V3-V5 Development studies did not repair it. An already-existing coarse HighVol mechanism cube (direction / slow alignment / tail2 acceleration / 5m efficiency) showed a distinct cell with positive 3-minute continuation in both the historical Development aggregate and reusable Validation aggregate:

> slow trend aligned up + recent 5m up + tail2 acceleration + efficient path.

Because reusable Validation evidence informed this hypothesis, any later 2024-2026 result is explicitly `validation/tuning evidence`, not fresh OOS. The candidate must first be rebuilt and pass Development 2021-2023.

## Frozen Development candidate family

STAR50 `000688.SH`, at a `NormalVol -> HighVol` onset:

- prior non-overlapping 30-minute net return > 0;
- recent 5-minute net return > 0;
- recent 5-minute path efficiency >= 0.60;
- `tail2_share >= 0.60`;
- no tail1/single-spike condition;
- long at next-minute open;
- fixed hold 3 minutes;
- same half-session and complete valid path;
- non-overlapping trades;
- 1bp/leg primary cost.

The 0.60 values are the pre-existing binary mechanism-cube definitions, not a new threshold sweep. No alternate thresholds or holding periods are allowed in this round.

## Development acceptance

All must pass on 2021/2022/2023:

- pooled trades >= 60;
- each year trades >= 15;
- each year mean net return after 1bp/leg > 0;
- pooled mean net after 1bp/leg > 0;
- pooled one-way break-even > 1bp.

If any gate fails, no candidate is frozen and Validation is not rerun.

## Governance

Development workflow physically contains only STAR50 2020 warm-up plus 2021-2023 rows. Validation rows and BlackBox rows are absent. BlackBox is not queried.
