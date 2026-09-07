# V3.3 result — STAR50 e-2 single-score fixed-budget gate

Date: 2026-09-07  
Frozen scientific ref: `b435818a85048327bc099a6c358fb26719c09f56`  
Protocol frozen before outcomes: `03ff96ea7baec90987ba46183254d9b85eed96d6`  
Actions run/job: `34137842371` / `101792851055`  
Actions conclusion: **success**; inherited V3.2 + V3.3 tests: **10 passed**.  
Artifact: `10024730912`, ZIP digest `sha256:b459ac6daea400d727da21130fe488fbdbe65b518c59afc4bcb7298cdf8d3df6`.

## Question and answer

V3.2 found a moderate STAR50 quiet-first precursor shift in the fixed e-2 fast-vs-slow scale score. V3.3 asked the stricter operational question: if thresholds are calibrated without event labels from **all eligible 2022–2023 market opportunities**, how much 2024–2025 market time must be marked Risk to cover quiet-first shocks at least one complete minute before the event minute?

**Answer: the raw-score route is only weak/descriptive. It does not meet the preregistered candidate threshold.**

The primary 20% nominal budget realizes 16.1771% flagged time in 2024–2025 and catches only 4/16 = 25% of in-scope quiet-first events. Lift versus marked time is 1.5454x. The frozen interpretation is therefore `weak_descriptive_only`.

## Frozen score and calibration

`S_t = 0.5 * [(logE30_t - logE240_t) + (logE60_t - logE240_t)]`

2022–2023 calibration uses 69,852 finite label-free opportunities. Empirical quantiles use `method="higher"`; event labels are not used to set thresholds.

| Nominal budget | Frozen threshold | Calibration realized share |
|---:|---:|---:|
| 10% | 0.8400700 | 10.0011% |
| **20% primary** | **0.4912942** | **20.0009%** |
| 30% | 0.2252549 | 30.0006% |

## 2024–2025 fixed-threshold evaluation

| Budget | Realized Risk-time share | Quiet-first recall | Lift vs time share | Clean event leakage |
|---:|---:|---:|---:|---:|
| 10% | 7.6259% | 0/16 = **0%** | 0.00x | 100% |
| **20% primary** | **16.1771%** | **4/16 = 25%** | **1.5454x** | **75%** |
| 30% | 25.5567% | 6/16 = **37.5%** | 1.4673x | 62.5% |

All 16 in-scope 2024–2025 events are evaluable; Unknown = 0. The 30-minute energy definition means this experiment does **not** claim coverage during the first 30 minutes after a half-session opens.

### Year split

2024 has 14 events. At the primary 20% budget, realized Risk time is 15.8822%, recall is 3/14 = 21.43%, lift 1.3492x. At 30%, recall is 5/14 = 35.71%, lift 1.4304x. The 10% gate catches none.

2025 has only two events. The 20% gate catches one, but this n=2 slice cannot override the combined/2024 result and was not used to retune anything.

### Time-of-session descriptive split

For event minutes 33–60, the 20% gate catches 2/7 = 28.57%; for ordinary event minutes >60 it catches 2/9 = 22.22%. Neither split changes the primary combined decision.

## Scientific interpretation

V3.2's matched-control result showed that STAR50 event scores tend to be higher **relative to specifically matched background states**. V3.3 shows that this is not the same as a sparse absolute-score early-warning gate: the strongest raw-score tail is particularly unhelpful, with the 10% nominal gate catching zero evaluation events.

Therefore:

1. do **not** promote the raw `primary_scale_score` gate;
2. do **not** search a better threshold on 2024–2025;
3. any next precursor experiment must test whether the V3.2 effect is a conditional anomaly that can be normalized using only information available at e-2, never the event minute or future event proximity;
4. if a strictly causal conditional-rank variant does not materially improve the frozen primary budget, close this single-score pre-first-shock route rather than adding model complexity.

## Integrity / governance

- frozen scientific ref was checked out exactly by Actions;
- only STAR50 2022–2025 bounded 1m/3s inputs were mounted;
- no CSI1000, 2026, returns, P&L, OOS, trading or production inputs were consumed by V3.3;
- `fresh_oos=false` and `production_authority=false`;
- morphology replication acceptance, direction, third-wave, returns/P&L, fresh OOS, trading, position sizing and production remain frozen;
- the separate v0.6.17 prior-identity blocker is unchanged.
