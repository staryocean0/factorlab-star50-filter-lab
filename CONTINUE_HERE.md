# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
2. `docs/governance/DATA_USAGE_POLICY_V2.md`
3. `docs/governance/data_usage_declaration.json`
4. `docs/governance/blackbox_query_ledger.json`
5. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

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

Do not query BlackBox merely because old payoff research had passed Validation. A new risk-state protocol must earn its own authority.

`production_authority=false`.
