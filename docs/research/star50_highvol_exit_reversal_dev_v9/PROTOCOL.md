# STAR50 HighVol -> NormalVol exit-reversal mechanism V9

Role: **Development-only mechanism research**, 2021-2023. Validation and BlackBox are not queried.

V7 falsified the existing onset-path feature cube and V8 found no HighVol-age landmark with three-year cost-positive directional continuation. This round therefore studies a different state event: the causal exit from HighVol.

## Event

Within each half-session identify every completed-minute transition:

`previous minute = HighVol` -> `current minute = NormalVol`.

At the current completed minute, all state information is known. Let `run_length` be the number of consecutive HighVol minutes immediately preceding the exit. Let `net5` be the net return over the latest five completed one-minute returns ending at the current NormalVol minute.

If `net5 != 0`, define:

- continuation direction = sign(net5);
- reversal direction = -sign(net5).

Enter at the **next-minute open**, hold exactly 3 minutes, require same half-session and a complete valid path.

No tail2, path-efficiency, slow-trend, cross-index, or onset-vol-ratio filter is used.

## Fixed diagnostics

Report all exits pooled and by year. Also report predeclared prior-HighVol run-length bands only as mechanism diagnostics:

- 1 minute;
- 2-3 minutes;
- 4-6 minutes;
- >=7 minutes.

These bands reuse the coarse persistence landmarks from V8 and are not an optimization grid.

For each view report:

- event count;
- mean/median 3m continuation return;
- mean/median 3m reversal return;
- reversal hit rate;
- reversal mean net after 1bp/leg;
- reversal one-way break-even cost;
- mean absolute 3m displacement.

No candidate is nominated in this round. A view is only `mechanism_promising` if every 2021/2022/2023 slice has >=15 events and every year's **reversal** mean net after 1bp/leg is positive. A promising mechanism must be separately frozen and rerun on Development before any Validation evaluation.

## Governance

Workflow physically contains only STAR50 2020 warm-up and 2021-2023 Development data. Validation and BlackBox rows are absent. BlackBox remains untouched.
