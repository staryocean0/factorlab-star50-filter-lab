# CSI1000 HighVol candidate failure context diagnostic V1

Purpose: explain why the frozen `tail2>=0.8, tail1<0.6, momentum, hold10m` candidate was positive in Development 2021-2023 but failed Validation 2024-2026-08-21.

Data roles follow repository V2 governance:

- Development details may be reused freely.
- Validation details may be inspected because the frozen candidate has already been evaluated and failed.
- BlackBox-V1 is not queried.

This diagnostic does not rescue the failed candidate and does not alter its thresholds.

## Hypothesis to inspect

The 2-minute acceleration may behave differently depending on the slower trend that existed before the five-minute trigger window.

For each already-defined candidate trigger, compute from information known at trigger close:

- background 30m net return using the same non-overlapping 30m block underlying the HighVol denominator;
- background 30m path efficiency;
- whether the current 5m direction agrees with that prior 30m net direction;
- prior 10m and prior 15m net direction/efficiency as secondary diagnostics.

Then report the already-frozen 10m continuation outcome by:

- Development vs Validation role;
- calendar slice;
- trigger direction;
- slow-trend alignment.

No new strategy is selected in this diagnostic. Any follow-up candidate must be rebuilt and selected in the Development pool before another Validation pass.
