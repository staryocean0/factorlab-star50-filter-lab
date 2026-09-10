# HighVol realtime risk object V9 — Validation evidence

Status: **SUPPORTED on available 2024-2025 3s Validation subset**.

Frozen object:

`E-3s causal risk state + time since most recent shock -> P(Normal within next 15 minutes)`

The V6 probability table, V8 thresholds, state transition rules and `E-3s` checkpoint were not changed or refit.

## Evidence

- Development source commit: `e01b293dcfc3100a02265315376bc63a9137c3d3`
- Development run/artifact: `34443013548` / `10138625380`
- Development artifact SHA256: `70abd300bfc2c66eba758b2d7fca0f51f91102d9e06db6be574af2958091ba07`
- Validation run/artifact: `34445445737` / `10139480476`
- Validation artifact SHA256: `432c88ad4799834b0698e6c2db48f694e252da47da64b95e7077ae813bcae386`

## Validation result

Pooled 2024-2025, `n=4859`:

- realtime probability coverage: `1.0`
- exact state agreement: `0.9997941963366948`
- exact probability-cell agreement: `0.9997941963366948`
- probability MAE vs frozen V6 reference: `0.000014624782133370469`
- frozen reference Brier: `0.08144334313214832`
- realtime Brier: `0.08144191191460566`
- Brier degradation: `-0.0000014312175426606233`
- frozen reference LogLoss: `0.2829004710410182`
- realtime LogLoss: `0.2828850866730461`

2024 and 2025 each separately passed the frozen coverage/MAE/Brier-degradation screen. All frozen support gates passed.

## Boundary

The repository 3s physical contract currently ends at 2025-12-31. Therefore this evidence does **not** claim complete realtime Validation through 2026-08-21. No 2026 3s data and no BlackBox data were queried.

Interpretation: on all physically available out-of-Development 3s coverage, the unified realtime object reproduces the validated 5m shock-reset recovery probability essentially losslessly at `E-3s`.

`production_authority=false`.
