# CSI1000 frozen candidate within-event delay-decay V1

Frozen before reading delay-decay market results.

## Purpose

Test whether the validated CSI1000 long acceleration candidate is specifically concentrated near the `NormalVol -> HighVol` transition, without cross-event matching.

## Frozen candidate set

Reconstruct exactly the previously frozen candidate:

- `000852.SH`;
- `NormalVol -> HighVol`;
- recent 5m net > 0;
- preceding non-overlapping 30m net > 0;
- `tail2_share >= 0.60`;
- `tail1_share < 0.60`;
- original hold = 3 minutes;
- non-overlapping candidate selection.

Candidate counts must reproduce 104 Development events and 129 Validation events.

## Delay menu

For every frozen candidate event, compare fixed entry delays `d = 0,1,2,3,5` minutes.

- `d=0`: enter at the next minute open, identical to the frozen candidate.
- `d=k`: wait k additional full minutes, then enter at the following minute open.
- Every entry holds exactly 3 minutes and exits at the corresponding open.
- Same half-session and complete valid execution path only.
- Candidate identity is never changed because a delayed path is unavailable; that delay is simply missing for that event.

No delayed state is used to decide whether to trade. State immediately before each delayed entry is reported descriptively only.

## Outputs

For Development (2021-2023) and reusable Validation (2024 through 2026-08-21), report by delay and year/pooled:

- eligible events;
- mean/median gross bp per trade;
- hit rate;
- mean net after 1 bp per leg;
- fraction whose state immediately before entry is still `HighVol`.

For each `d>0`, on events where both d=0 and d are executable, report paired difference:

`delay_minus_immediate_bp = gross(d) - gross(0)`.

Use 10,000 trading-day block bootstrap draws separately by role for each delay difference.

## Interpretation

- Materially negative delay-minus-immediate differences that become more negative with delay support transition-localized opportunity.
- Similar delayed and immediate returns support a broader persistent acceleration regime rather than onset-specific timing.
- Better delayed returns would argue that waiting for confirmation may be preferable to entering immediately.

This is a Validation diagnostic, not candidate retuning or promotion. Development and Validation are reusable under the three-pool policy. BlackBox-V1 is not queried.
