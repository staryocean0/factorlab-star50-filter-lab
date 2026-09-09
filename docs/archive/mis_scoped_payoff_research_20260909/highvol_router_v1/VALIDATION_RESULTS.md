# HighVol Router V1 — reusable Validation result

Status at the time: **VALIDATION-SUPPORTED / RESEARCH-ONLY**.

This historical result does **not** grant production authority. `production_authority=false`. BlackBox-V1 was not queried.

Candidate: `highvol_router_v1_csi1000_active_star50_no_trade`.

- CSI1000 (`000852.SH`): active frozen long 3-minute continuation module.
- STAR50 (`000688.SH`): `NO_TRADE`.
- Other HighVol contexts: `NO_TRADE`.

Development 2021-2023: 104 accepted non-overlap trades, pooled mean net at 1 bp/leg `+0.737746 bp/trade`, one-way break-even `1.368873 bp`.

Reusable Validation 2024-01-01 through 2026-08-21: 129 accepted trades, pooled mean net `+0.546255 bp/trade`, one-way break-even `1.273128 bp`, total net `+70.466928 bp`, 2 of 3 annual slices positive; 2026 through 08-21 slightly negative.

Decisive Validation run: `34300569936`; artifact `10084769189`; ZIP SHA256 `4e7d1aea626936c1170ee26d4f9787ff26edd66236241c62be5ac90807a91d71`.

Historical acceptance gates passed under the frozen router protocol. Subsequent stability audit showed material fragility: narrow cost margin, bootstrap interval crossing zero and dependence on strong positive days.

## Scope-repair status

As of 2026-09-09 this payoff/router result is archived because STAR50 Filter's current bucket authority is bottom-layer K-line risk-state research, not directional payoff strategy optimization. The statistical result is preserved; its placement as a current STAR50 research lane is revoked.
