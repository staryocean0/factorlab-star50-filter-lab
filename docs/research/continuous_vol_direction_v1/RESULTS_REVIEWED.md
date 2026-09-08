# Continuous HighVol direction V1 — reviewed results

Date: 2026-09-08
Status: completed under three-pool governance; no BlackBox-V1 query; no candidate promotion.

## Governance and execution

- Development pool: 2021-2023 only for candidate selection.
- Validation pool: 2024-2026-08-21, inspected only after the development decision was fixed.
- BlackBox-V1: not touched.
- Frozen Actions run: `34211990073`.
- Artifact: `continuous-vol-direction-v1-34211990073`.
- Artifact SHA-256: `b52300c3cef256479c8ff45fb9ab24bfa479c7546865ca86dd0ed9426aa9c0e8`.
- All frozen causality/execution tests passed before market results.

## Development decision

Frozen menu: momentum/reversal × lookback 1/2/3/5/10m × execution delay 1/2m, all evaluated inside the already-frozen continuous HighVol state.

Eligibility required nonzero HighVol exposure in all development years, positive net after 1bp one-way cost in at least 2 of 3 development years, and pooled development break-even one-way cost >1bp.

Result:

- STAR50: `NONE`.
- CSI1000: `NONE`.

No primary validation candidate was therefore promoted.

## STAR50 diagnostic

The best development pooled HighVol score was 3-minute momentum with 1-minute execution delay:

- gross `+1704.36 bp`;
- one-way turnover `6804`;
- exposure `7024 min`;
- break-even one-way cost only `0.250 bp`;
- net after 1bp cost `-0.726 bp / exposure min`.

It was negative after 1bp in every development year. Validation remained negative as well. Simple short-horizon momentum/reversal is therefore not economically viable for STAR50 in this state under the frozen cost stress.

## CSI1000 diagnostic

The closest development candidate was 1-minute momentum with 1-minute execution delay:

Pooled 2021-2023 HighVol:

- gross `+7818.59 bp`;
- one-way turnover `8398`;
- exposure `7241 min`;
- break-even one-way cost `0.931 bp`;
- net after 1bp cost `-0.080 bp / exposure min`.

Annual detail:

- 2021: break-even `1.176 bp`; net1/min `+0.194`;
- 2022: break-even `1.223 bp`; net1/min `+0.256`;
- 2023: break-even `0.506 bp`; net1/min `-0.602`.

Thus it satisfied the two-positive-years condition but failed the frozen pooled >1bp break-even condition. The threshold is not relaxed post hoc.

Validation diagnostic after the development rejection:

- 2024: break-even `0.862 bp`; net1/min `-0.167`;
- 2025: break-even `0.685 bp`; net1/min `-0.381`;
- 2026-through-08-21: break-even `0.176 bp`; net1/min `-1.093`.

The apparent early-development edge therefore decays rather than strengthening out of sample within the reusable Validation pool.

## Interpretation

1. Continuous HighVol contains some short-horizon **momentum**, especially CSI1000 in 2021-2022; the evidence does not favor a generic reversal interpretation.
2. Updating the target every minute creates very high turnover. Even substantial gross movement is not enough to clear a 1bp one-way abstract cost consistently.
3. The next development iteration should therefore change the **trade construction**, not relax the cost hurdle: make decisions at HighVol episode onset, trade once or sparsely, and condition continuation/reversal on a causal path-shape variable such as recent path efficiency.
4. This is a new development hypothesis. It must be developed on 2021-2023 and then frozen before Validation is evaluated.

## Decision

No V1 candidate promotion. Retain the continuous HighVol state and move to eventized, lower-turnover onset trading with causal path-shape conditioning. BlackBox-V1 remains untouched.
