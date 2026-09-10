# STAR50 research bars

Current active data catalog: `cross_index_risk_gate_v1/manifest.json` and
`cross_index_risk_gate_3s_v1/manifest.json`; see
[`../docs/handoff/cloud_risk_gate_20260907/DATA.md`](../docs/handoff/cloud_risk_gate_20260907/DATA.md).
These bounded exports contain STAR50 and CSI1000 through 2025. The independent
2026 cross-index Validation pack is preserved separately on the historical
`research/post-shock-recovery-2026-validation` evidence branch and covers complete
trading days through 2026-08-21.

The legacy `development/` directory is not the current research input. Its original
files/manifests are retained unchanged.

Source: DataHub `factorlab_unified_index_kline_v3_20260824`.
Range available across retained evidence: 2020-07-23 through 2026-08-21.

`timestamp` in the source export used a `Z` suffix around Shanghai wall-clock labels.
Treat `trading_day` plus session clock as the trading calendar. These are identity
index-point rows, not tradable fills.

## Frequency construction rule

Default rule: do not invent a new frequency ad hoc.

Explicit exception authorized by the user on 2026-09-10: deterministic 5m bars may
be constructed from the repository's 1m index bars because the user's existing 5m
bars are themselves constructed from 1m. Before a synthesized frequency is used in
a scored study, its construction must be frozen and, where overlapping native bars
exist, checked for exact historical equivalence. For V6 recovery-clock Validation,
2023 1m->5m close sequences matched the existing 5m bars exactly for both indices
(max absolute close difference `0.0`) before 2026 was scored.

## Data roles

See `docs/governance/data_usage_declaration.json` and
`docs/governance/DATA_USAGE_POLICY_V2.md`:

- 2020: warm-up only where required;
- 2021-2023: Development;
- 2024 through 2026-08-21: reusable Validation after Development freeze;
- protected BlackBox-V1: strictly after the Validation cutoff under its existing
  aggregate-only protocol.

No Validation result automatically authorizes BlackBox access.

Do not mix overnight-open, two-wave, multifactor-stock, or migrated R1/R2 payoff
research back into this bottom-layer risk-state bucket.
