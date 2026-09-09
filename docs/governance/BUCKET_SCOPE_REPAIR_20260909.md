# STAR50 bucket scope repair — 2026-09-09

## Current authority

`factorlab-star50-filter-lab` owns **bottom-layer K-line risk research** only:

- causal volatility level and volatility expansion/contraction;
- isolated shock vs clustered shock morphology;
- Unsafe / Recovering / HighVol annotations;
- when a causal risk state should switch on, persist, recover, or remain `NO_RISK_SWITCH`;
- cross-scale risk attributes for STAR50 and bounded CSI1000 comparison.

It does not own a concrete payoff strategy and it does not own the generic parent-structure classification problem `Range / UpTrend / DownTrend`.

## Cross-bucket placement

- `Range / UpTrend / DownTrend` causal parent-structure recognition belongs to `factorlab-two-wave-strategy-lab`.
- concrete reversal / mean-reversion strategies including R1/R2 belong to `factorlab-trend-reversion-regime-lab`.
- R1/R2 have already been migrated out of this repository correctly.

## Mis-scoped historical payoff research retained here

This repository contains historical payoff/router experiments, including HighVol Router V1 and the V10-V17 HighVol sign-flip program. Those results are **not deleted**. They remain immutable historical evidence at and before pre-repair main commit:

`4232d20b143a9c532e14a39761370bf1eca8d084`

From this scope repair forward:

- they are not current STAR50 bucket authority;
- they must not be presented as the next research task in `README.md`, `CONTINUE_HERE.md`, or `CURRENT_RESEARCH.md`;
- no new payoff tuning, routing, holding-period, stop/target, leverage or strategy optimization should continue in this bucket;
- risk-state findings produced during those experiments may remain usable as risk evidence if separated from payoff conclusions.

There is no forced migration target for the CSI1000 3-minute continuation payoff module among the three current buckets: it is neither the Two-Wave morphology recognizer nor an R1/R2-style reversal strategy. Therefore it is archived/demoted rather than incorrectly moved into another bucket.

This repair changes current authority, not Git history.

`production_authority=false`.
