# HighVol onset structure — development diagnostic V1

Date: 2026-09-08

Role under `docs/governance/DATA_USAGE_POLICY_V2.md`: **Development only**.

## Data use

- Subjects: `000688.SH`, `000852.SH`.
- Scored rows: 2021-01-01 through 2023-12-31 only.
- Pre-2021 rows may be loaded only as warm-up/source context where needed.
- 2024 through 2026-08-21 Validation is **not inspected by this diagnostic**.
- BlackBox-V1 is not queried.

## Frozen state definition

Reuse continuous volatility regime V1:

- `fast_rms = RMS(last 5 complete 1m close-to-close returns)`;
- `background_rms = RMS(the preceding non-overlapping 30 complete 1m returns)`;
- `vol_ratio = fast_rms / max(background_rms, 1 bp)`;
- `HighVol` iff `vol_ratio >= 1.5`;
- onset iff current minute is `HighVol` and immediately previous minute is `NormalVol` within the same half-session.

## Purpose

Do not select or promote a trading rule yet. Build a mechanism map of each HighVol onset using only information known at the onset close, then measure next-open-to-future-open returns.

Past-only onset features:

- `eff5`: abs(net 5m return) / 5m total variation;
- `net5_bp` and its sign;
- `sign_agreement5`: fraction of the five 1m returns agreeing with the 5m net direction;
- `tail1_share`: absolute final 1m return / 5m total variation;
- `tail2_share`: absolute movement in final 2m / 5m total variation;
- `accel_abs_2v3`: mean absolute return of final 2m / mean absolute return of first 3m;
- `prior5_net_bp`, `prior5_eff`, and whether prior 5m net direction agrees with current 5m direction;
- `vol_ratio` at onset.

Outcomes are descriptive development targets only:

- signed continuation return using the current 5m direction over 1/2/3/5/10 minutes;
- the corresponding reversal return is its negative;
- entry is next minute open; exit is the open after the fixed horizon;
- no invalid path and no half-session crossing.

## Output

Development event table plus fixed descriptive bin tables and correlations. These outputs may be inspected in detail because this is the Development pool.

No validation-period candidate result is produced by this study. A later study must freeze any derived taxonomy/rule before opening the Validation pool.
