# CSI1000 long HighVol acceleration — Development V1

This is a Development-pool search under repository data-use policy V2.

## Data roles

- Development only for candidate selection: 2021-01-01 through 2023-12-31.
- Validation is not read by this search.
- BlackBox-V1 is not queried.

The search is motivated by the prior failed two-minute acceleration candidate and its allowed Validation diagnosis: upward accelerations aligned with the prior slow trend behaved more consistently than downward accelerations. That observation is a hypothesis generator only; all new thresholds below are selected anew from Development.

## Fixed base event

- Subject: `000852.SH`.
- Continuous HighVol onset: `NormalVol -> HighVol` where recent 5m RMS / preceding non-overlapping 30m RMS >= 1.5, background floor 1 bp.
- Current five-minute net direction must be positive. No short candidate is considered in this study.
- Entry is next minute open.
- Same half-session, complete valid path only.
- Selected trades may not overlap.

## Development menu

Slow-direction context window: `10m`, `15m`, `30m` immediately preceding the current five-minute trigger window. Require slow net return > 0 (same direction as the long trigger).

Late acceleration filter:

- minimum `tail2_share`: `0.40`, `0.60`, `0.80`;
- final-one-minute cap: `none` or `tail1_share < 0.60`.

Hold: `3m`, `5m`, `10m`.

Total fixed menu: 3 × 3 × 2 × 3 = 54 identities.

## Cost and eligibility

Primary abstract friction: 1 bp per execution leg, exactly two legs per completed trade.

A Development identity is eligible only if:

1. at least 15 completed trades in each of 2021, 2022 and 2023;
2. at least 60 completed trades pooled;
3. mean net return after 1 bp/leg is positive in every Development year;
4. pooled one-way break-even cost is > 1 bp.

Among eligible identities rank by:

1. highest worst-year mean net return after 1 bp/leg;
2. then highest pooled mean net return after 1 bp/leg;
3. then more pooled trades;
4. then shorter hold;
5. then longer slow context;
6. then less restrictive late-acceleration filter.

If no identity is eligible, nominate NONE. Validation must not be opened to rescue this Development search.
