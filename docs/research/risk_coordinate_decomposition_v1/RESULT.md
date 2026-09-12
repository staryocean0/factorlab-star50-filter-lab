# Two-coordinate risk decomposition V1 — accepted Development diagnostic

Date: 2026-09-09
Branch: `research/risk-coordinate-decomposition-v1-20260909`
Frozen protocol: `FROZEN_PROTOCOL.md`
Dedicated run: `34303542018`
Execution commit: `e89ac7125f446b0da87fc786397c5271dd563ba4`
Artifact id: `10085849822`
Artifact ZIP SHA-256: `c837bc38c067f59b4ec38f6c5efee3798f47a1208c0722bae02634c64f2451ad`

## Decision

**`two_axis_decomposition_descriptively_consistent`** on the already-inspected 2023 Development evidence.

This is a failure-mechanism diagnostic following the negative parent V1 result. It is not independent confirmation, not fresh/OOS evidence, and not candidate promotion.

## Population

Rows with both coordinates defined: `64,020`.

No Validation or BlackBox rows were read. No returns/P&L or trading outcomes were evaluated. `candidate_nominated=false`; `production_authority=false`.

## Coordinate A: future movement amplitude

M3 remains strongly associated with future 15-minute RMS after splitting rows by the inherited current Unsafe state.

### STAR50

Current NonUnsafe:
- M3<=0: n=20,401, median future RMS `4.2985 bp`;
- M3>2: n=174, median future RMS `7.4180 bp`.

Current Unsafe:
- M3<=0: n=554, median future RMS `3.6977 bp`;
- M3>2: n=37, median future RMS `7.3980 bp`.

### CSI1000

Current NonUnsafe:
- M3<=0: n=19,684, median future RMS `2.8248 bp`;
- M3>2: n=109, median future RMS `6.0252 bp`.

Current Unsafe:
- M3<=0: n=406, median future RMS `2.5434 bp`;
- M3>2: n=48, median future RMS `5.6335 bp`.

The frozen >=10% top/bottom amplitude check passes in both current states for both indices.

## Coordinate B: relative abnormal-state persistence

Pooling M3 bands within each index:

### STAR50
- current NonUnsafe: n=29,243, P(any future Unsafe in next 15m)=`26.66%`;
- current Unsafe: n=1,559, probability=`77.49%`;
- difference: `+50.82pp`.

### CSI1000
- current NonUnsafe: n=31,091, probability=`27.06%`;
- current Unsafe: n=2,127, probability=`78.42%`;
- difference: `+51.36pp`.

Both pass the frozen >=30pp persistence-axis check.

## Important non-monotonicity

Inside current Unsafe, future Unsafe probability **declines** as M3 rises even while future RMS rises:

STAR50:
- M3<=0: `79.78%` future Unsafe;
- M3>2: `70.27%`.

CSI1000:
- M3<=0: `81.03%`;
- M3>2: `70.83%`.

Inside current NonUnsafe, M3 also does not produce a monotone future-Unsafe ladder even though the future-RMS ladder is strong.

This is the central architectural result: **movement amplitude and relative abnormal-state persistence are not the same risk dimension.**

## Current architecture implication

The evidence is consistent with retaining at least two causal coordinates rather than compressing risk into one ordinal scalar:

1. `activity_surprise` / movement-budget coordinate: M3;
2. `relative_vol_state` / abnormal-state persistence coordinate: current 5m RMS divided by preceding non-overlapping 30m RMS, Unsafe boundary 1.5.

Neither coordinate should be interpreted as a trading action. In particular:
- high M3 does not mean `Unsafe => flat`;
- high M3 does not reopen first-shock prediction;
- current Unsafe remains a state annotation, not a universal execution gate.

## Next admissible step

Freeze an unchanged-coordinate reusable Validation diagnostic on available 2024/2025 1m + 3s index data.

The Validation diagnostic must:
- preserve M3 exactly;
- preserve current ratio and 1.5 Unsafe threshold exactly;
- preserve the low-amplitude <30bp conditioning and future 15m targets;
- report 2024 and 2025 separately;
- not call the result fresh/OOS;
- not read BlackBox;
- not nominate a trading/production candidate.
