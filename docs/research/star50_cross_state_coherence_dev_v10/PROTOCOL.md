# STAR50 cross-index state coherence Development V10

Role: **Development-only mechanism research**, 2021-2023. Validation and BlackBox are not queried.

V7 closed the existing STAR50 onset-path feature cube, V8 found no stable HighVol-age continuation landmark, and V9 found no stable HighVol-exit reversal. This round moves to the project-level routing question: whether a STAR50 volatility event is **systemic** or **STAR50-specific**.

## Event

At every causal STAR50 `NormalVol -> HighVol` onset, align CSI1000 `000852.SH` at the same completed minute and classify two fixed binary dimensions:

1. CSI1000 state: `HighVol` or `NormalVol` (Unknown rows excluded).
2. Recent 5-minute direction agreement: STAR50 and CSI1000 latest completed 5-minute net returns have the same sign or opposite signs (zero/missing excluded).

This creates exactly four cells. There is no threshold sweep.

For STAR50, define direction from its own latest completed 5-minute net return. Enter next-minute open and hold exactly 3 minutes. Report both:

- continuation return = trade in STAR50's own latest-5m direction;
- reversal return = trade opposite that direction.

Require same half-session and a complete valid path. For primary trade-like economics, remove overlapping events globally within each STAR50 half-session using the fixed 3-minute holding horizon before cell aggregation. Also retain all eligible onsets as a descriptive mechanism file.

No tail2, efficiency, slow trend, state age, penetration, shock-z, or continuous cross-index threshold is used.

## Fixed views

Exactly these four primary cells:

- CSI1000 NormalVol + direction agree;
- CSI1000 NormalVol + direction disagree;
- CSI1000 HighVol + direction agree;
- CSI1000 HighVol + direction disagree.

Also report pooled `CSI1000 NormalVol` and pooled `CSI1000 HighVol` views as state-level diagnostics; they cannot nominate a mechanism by themselves.

A primary cell is `continuation_promising` only if each of 2021/2022/2023 has >=15 non-overlapping events and each year's continuation mean after 1bp/leg is positive. It is `reversal_promising` under the symmetric rule for reversal. This is a mechanism label only, not a frozen candidate; any promising cell must be separately specified and rerun on Development before Validation.

## Governance

The workflow physically contains only 2020 warm-up plus 2021-2023 1-minute data for both STAR50 and CSI1000. Validation and BlackBox rows must be absent. BlackBox remains untouched.
