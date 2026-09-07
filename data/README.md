# STAR50 research bars

Current active data catalog: `cross_index_risk_gate_v1/manifest.json` and
`cross_index_risk_gate_3s_v1/manifest.json`; see
[`../docs/handoff/cloud_risk_gate_20260907/DATA.md`](../docs/handoff/cloud_risk_gate_20260907/DATA.md).
These bounded exports contain STAR50 and CSI1000, through 2025 only. The legacy
`development/` directory below contains 2026 and is not the current research input.
Its original files/manifests are retained unchanged; the old exclusion of CSI1000
does not apply to the new explicitly authorized cross-index scope.

Every Parquet in `development/` contains only `000688.SH` (科创50).

Source: DataHub `factorlab_unified_index_kline_v3_20260824`.
Range: 2020-07-23 through 2026-08-21 (index listing start through current export).

`timestamp` in the source export used a `Z` suffix around Shanghai wall-clock labels.
Treat `trading_day` plus session clock as the trading calendar. Do not locally resample
new frequencies. These are identity index-point rows, not tradable fills.

Data roles (see `docs/governance/data_usage_declaration.json`):

- 2020-07-23 to 2020-12-31: warmup only
- 2021-01-01 to 2025-12-31: development
- 2026-01-01 to 2026-08-21: consumed repeat audit, not for selection

Do not mix CSI1000, overnight-open, two-wave, or multifactor-stock labs into this repo.
