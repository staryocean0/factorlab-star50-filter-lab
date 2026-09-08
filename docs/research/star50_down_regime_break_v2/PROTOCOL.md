# STAR50 downside accelerated regime-break V2

## Scientific status

This is a new candidate generated from prior Validation mechanism diagnosis. The hypothesis was returned to the Development pool before formal candidate testing. It is not a rescue of the failed V1 candidate.

Data roles follow `docs/governance/DATA_USAGE_POLICY_V2.md`:

- Development: 2021-01-01 through 2023-12-31.
- Validation: 2024-01-01 through 2026-08-21, unopened for this candidate until Development passes.
- BlackBox-V1: not queried.

## Frozen candidate

Symbol: `000688.SH`.

At a causal `NormalVol -> HighVol` onset, require all of:

1. preceding non-overlapping 30-minute net return is positive;
2. most recent 5-minute net return is negative;
3. 5-minute path efficiency is at least `0.60`;
4. `tail2_share`, the absolute movement in the last two minutes divided by total absolute 5-minute movement, is at least `0.50`.

No `tail1_share` filter is used.

Execution is frozen as:

- short at the next minute open;
- hold exactly 3 minutes;
- exit at the corresponding minute open;
- stay within the same half-day/session;
- require a complete valid path;
- accept non-overlapping trades only;
- no confirmation wait;
- no mechanical stop.

Primary economics use 1 bp per leg.

## Development acceptance

All must pass before Validation may be opened:

- pooled trades >= 60;
- every year 2021/2022/2023 has at least 15 trades;
- every year has positive mean net return after 1 bp per leg;
- pooled mean net return after 1 bp per leg is positive;
- pooled one-way break-even cost is greater than 1 bp.

Development may be inspected freely. The thresholds above are frozen for this formal rerun.

## Validation preregistration

If and only if Development passes, evaluate the same frozen identity on 2024-01-01 through 2026-08-21.

Validation passes when all hold:

- total trades >= 30;
- pooled mean net after 1 bp per leg > 0;
- at least two of the 2024/2025/2026 slices have positive mean net after 1 bp per leg;
- pooled one-way break-even cost > 1 bp.

Validation is reusable validation/tuning evidence, not fresh OOS. If it fails, do not rescue `tail2>=0.50`, `efficiency>=0.60`, or the 3-minute hold inside Validation. Detailed failure diagnosis is allowed only to formulate the next hypothesis, which must return to Development.

BlackBox-V1 remains untouched.
