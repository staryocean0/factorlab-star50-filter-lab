# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `docs/research/highvol_horizon_adaptive_v16_validation_20260911.md`
3. `docs/research/highvol_horizon_adaptive_v16_validation_receipt_20260911.json`
4. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
5. `docs/governance/DATA_USAGE_POLICY_V2.md`
6. `docs/governance/data_usage_declaration.json`
7. `docs/governance/blackbox_query_ledger.json`
8. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

V16 horizon-adaptive recovery surface has completed Development and its one frozen reusable Validation.

Current decisive state:

`V16_REUSABLE_VALIDATION_SUPPORTED`

Frozen validated 5m object:

- `15m = current_state + time-since-most-recent-shock`;
- `30m = current_state + time-since-most-recent-shock`;
- `60m = time-since-most-recent-shock only`.

Validation authority: run `34602527314`, artifact `10264689647`, 5,908 scored rows over 2024 through 2026-08-21. The 15m and 30m components beat frozen age-only in pooled Brier/LogLoss and in all three annual Brier slices; 60m is exactly the age-only anchor.

Do **not** rerun V11-V16, refit this surface, inspect post-2026-08-21 data, or query BlackBox.

A future realtime transfer of this multi-horizon 5m object has not been started and requires its own preregistered protocol.

## Current research question

This bucket studies **when K-line conditions causally justify entering, staying in, or leaving a risk state**.

Allowed current objects:

- current/recent volatility and volatility expansion;
- clustered vs isolated shocks;
- cross-scale 3s/1m/5m risk evidence;
- `Unsafe`, `Recovering`, `HighVol` and related risk annotations;
- causal risk-state switch-on, persistence, hysteresis and recovery;
- diagnostics explaining false risk switches or missed dangerous states.

The output should be a risk-state annotation / gate, not a directional payoff strategy.

## Do not continue these as active research here

- HighVol Router V1 payoff optimization;
- V10-V17 directional sign-flip/continuation payoff search;
- new hold/stop/target/sizing/leverage/router variants;
- R1/R2 reversal/MR strategies;
- generic `Range / UpTrend / DownTrend` parent-structure classification.

Historical reports/results remain preserved and may supply **risk-state evidence only** when the payoff conclusion is kept separate. The pre-scope-repair main snapshot is commit `4232d20b143a9c532e14a39761370bf1eca8d084`.

R1/R2 are already in `factorlab-trend-reversion-regime-lab`.
Generic range/up/down causal structure recognition belongs to `factorlab-two-wave-strategy-lab`.

## Data-use regime

- Development: 2021-01-01 through 2023-12-31.
- Validation: 2024-01-01 through 2026-08-21; reusable but not fresh OOS.
- BlackBox-V1: protected post-cutoff aggregate-only regime under its frozen protocol.

Do not query BlackBox merely because old payoff research or a reusable risk-state Validation passed. A new BlackBox query still requires its own authority.

`blackbox_queried=false`.
`production_authority=false`.
