# STAR50 downside accelerated regime-break V2 — Development result

Status: **PASS** under the frozen Development acceptance rule.

Candidate: `star50_downside_accelerated_regime_break_v2`

Candidate SHA256: `6ed7e13804d27d375e5efe388bf0c6414e7a08cf01eeec65cfe7e4079da7a1fd`

Evidence run: GitHub Actions run `34225994735`, job `102060139283`, head commit `0711c1cdbad20eda5ce489f3c4de2871e19cde80`.

Data role: Development only, `2021-01-01` through `2023-12-31`. The workflow physically checked out only 2020 warm-up plus 2021/2022/2023 STAR50 minute files. Validation was not queried. BlackBox was not queried.

## Frozen rule

At causal `NormalVol -> HighVol` onset:

- preceding non-overlapping 30-minute net return > 0;
- recent 5-minute net return < 0;
- 5-minute efficiency >= 0.60;
- `tail2_share >= 0.50`;
- no `tail1_share` condition;
- short next minute open;
- fixed 3-minute hold;
- same half-day/session, valid complete path, non-overlapping trades;
- no confirmation wait and no mechanical stop.

Primary cost: 1 bp per leg.

## Results

| period | trades | gross bp/trade | net bp/trade @1bp/leg | one-way break-even bp |
|---|---:|---:|---:|---:|
| 2021 | 42 | 4.2292 | 2.2292 | 2.1146 |
| 2022 | 22 | 2.8769 | 0.8769 | 1.4384 |
| 2023 | 18 | 2.6014 | 0.6014 | 1.3007 |
| pooled | 82 | 3.5091 | 1.5091 | 1.7545 |

Pooled median gross return: `1.1219 bp/trade`; pooled gross hit rate: `53.66%`.

## Acceptance

All pre-registered primary Development gates passed:

- pooled trades >= 60: PASS (`82`);
- every year trades >= 15: PASS (`42 / 22 / 18`);
- every year net @1bp/leg > 0: PASS;
- pooled net @1bp/leg > 0: PASS (`+1.5091 bp/trade`);
- pooled one-way break-even > 1bp: PASS (`1.7545 bp`).

Therefore the frozen candidate is eligible to open the reusable Validation pool exactly once for this formal candidate evaluation under the already registered criteria. No parameter is changed between Development and Validation.

Development artifact ZIP SHA256 reported by Actions: `01c8e9dfb75860e7ff4511e9b340a31e8b6d97a39b8b511e9bf34ecdc337ea10`; artifact ID `10055730150`.
