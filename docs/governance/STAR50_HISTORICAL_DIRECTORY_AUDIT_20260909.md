# STAR50 historical directory audit — 2026-09-09

## Current bucket authority

`factorlab-star50-filter-lab` owns bottom-layer causal K-line risk-state research only: volatility level/expansion, shock isolation/clustering, `Unsafe / Recovering / HighVol`, switch-on/persistence/recovery, cross-scale 3s/1m/5m risk attributes and failure cases.

It does not own concrete payoff strategies, account optimization, routing, holding-period rules, stops/targets, sizing/leverage, or generic `Range / UpTrend / DownTrend` parent-structure recognition.

## Keep in `docs/research`

The following are in-scope risk/state evidence and remain active research material:

- `causal_volatility_tool_v1/` — causal volatility/risk measurement;
- `tail_distribution_v1/` — tail/shock distribution and antecedent volatility conditions;
- `resolution_transfer_v1/` — cross-resolution risk/measurement transfer;
- `cross_scale_root_cause/` and its closeout — cross-scale K-line/risk attribution;
- `csi1000_overlap_comparison/` — cross-index ER/volatility/noise overlap evidence;
- `apr_sep_2025_morphology/` — morphology measurement evidence;
- `wave_shape_v1/` — displacement concentration, phase, sharp-move and filter-delay morphology; strategy capture is only a diagnostic coordinate, not a promoted payoff strategy;
- cloud risk-gate handoff and current Unsafe/Recovering/HighVol state materials.

## Moved to archive as mis-scoped strategy/account research

The following were physically moved from `docs/research` to `docs/archive/mis_scoped_strategy_research_20260909/` with original blob contents preserved:

- `half_day_slope_union_v1/`;
- `half_day_slope_union_v2/`;
- `conditional_bucket_v1/`;
- `drawdown_conditions/`;
- `execution_counterexamples/`;
- `three_proposals_v1/`;
- `original_drawdown_trade_audit_v1.md`.

These bundles are dominated by payoff, MDD, account, transaction-cost, position-reduction, execution or policy-selection questions. Their historical results remain valid records of the protocol that produced them, but they are no longer active STAR50 bucket authority.

HighVol Router V1 and the V10–V17 directional sign-flip payoff program were already separately downgraded under `docs/archive/mis_scoped_payoff_research_20260909/`.

## Mixed-result retention rule

Archiving a strategy bundle must not discard any bottom-layer risk knowledge it happened to reveal. Reusable risk/state findings extracted from archived strategy work are summarized in `docs/research/RISK_STATE_LEGACY_FINDINGS_20260909.md`.

The archived strategy result itself does not regain current authority merely because one of its diagnostic coordinates is retained.

## Forward rule

Before adding a new STAR50 research item, ask:

1. Is the object a causal property/state of the K-line path itself? If yes, it may belong here.
2. Does it primarily answer whether/when/how to trade, route, size, hold or exit? If yes, it does not belong in current STAR50 research authority.
3. Is it generic parent structure `Range / UpTrend / DownTrend`? If yes, route to `factorlab-two-wave-strategy-lab`.
4. Is it reversal/mean-reversion payoff such as R1/R2? If yes, route to `factorlab-trend-reversion-regime-lab`.

Historical Git evidence is never deleted merely to make the bucket look clean.
