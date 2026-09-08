# STAR50 break-penetration Development study V3

Role: **Development only**. No Validation rows are used in this study and BlackBox is not queried.

## Motivation

STAR50 downside regime-break V2 failed reusable Validation because 2024 was strongly positive while 2025/2026 were negative. Post-failure Validation diagnostics rejected two simple repairs: signed last-2-minute acceleration and contemporaneous CSI1000 confirmation.

The next hypothesis is deliberately more structural and must be redeveloped on 2021-2023:

> A five-minute efficient selloff is a genuine regime break only when it erases a material fraction of the preceding thirty-minute rise. A shallow pullback inside an intact slow rise is economically different from a selloff that destroys the slow trend itself.

Define at each `NormalVol -> HighVol` onset satisfying:

- STAR50 `000688.SH`;
- prior non-overlapping 30-minute net return > 0;
- recent 5-minute net return < 0;
- 5-minute path efficiency >= 0.60;

`break_penetration = - net5_bp / slow30_net_bp`.

Natural interpretation bands are frozen before results:

- `<0.25`: shallow pullback;
- `0.25-0.50`: moderate pullback;
- `0.50-1.00`: major retracement but prior rise not fully erased;
- `1.00-2.00`: full trend erasure / first-order overshoot;
- `>=2.00`: large overshoot.

No percentile-derived bins are allowed.

## Outcomes

Primary economic outcome is short return from next-minute open to the open three minutes later, same half-session and complete valid path. Positive bp means the short made money.

Report both:

1. all eligible HighVol onset events for mechanism shape;
2. non-overlapping 3-minute trade-like events for economic viability.

For trade-like nested natural thresholds, inspect only `break_penetration >= 0.50`, `>=1.00`, and `>=2.00`. These are interpretation thresholds, not a fine grid.

A threshold may nominate a V3 candidate only if, on Development 2021/2022/2023:

- pooled trades >= 60;
- every year trades >= 15;
- every year mean net return after 1bp/leg > 0;
- pooled mean net return after 1bp/leg > 0;
- pooled one-way break-even cost > 1bp.

If none pass, no candidate is nominated. Do not relax these gates after seeing results.

The old V2 `tail2_share >= 0.50` is shown only as a secondary cross-tab; it is not required in the new base mechanism and is not automatically carried into V3.

## Data governance

Development: 2021-01-01 through 2023-12-31. 2020 may be checked out only as warm-up. Validation 2024-01-01 through 2026-08-21 must be physically absent from the Development workflow. BlackBox remains untouched.
