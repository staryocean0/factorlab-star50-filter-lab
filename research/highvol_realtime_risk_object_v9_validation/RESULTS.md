# V9 realtime risk object — reusable Validation result

Status: **SUPPORTED on available 2024-2025 3s Validation subset**.

This does not constitute complete Validation through 2026-08-21 because the repository 3s physical contract ends at 2025-12-31. No 2026 3s or BlackBox data was queried.

Frozen object:

`E-3s causal state + time since most recent shock -> P(Normal within next 15 minutes)`

No V6 probability, V8 state threshold, checkpoint, fit, or trading/payoff rule changed.

## Evidence

- Validation run: `34445445737`
- artifact: `10139480476`
- artifact SHA256: `432c88ad4799834b0698e6c2db48f694e252da47da64b95e7077ae813bcae386`
- frozen Development source commit: `e01b293dcfc3100a02265315376bc63a9137c3d3`
- Development run: `34443013548`
- Development artifact: `10138625380`

## Primary E-3s result

Pooled 2024-2025:

- reference/scored rows: `4859`
- realtime probability coverage: `1.0`
- exact state agreement: `0.9997941963366948`
- exact probability-cell agreement: `0.9997941963366948`
- probability MAE vs frozen V6 reference: `0.000014624782133370469`
- frozen reference Brier: `0.08144334313214832`
- realtime Brier: `0.08144191191460566`
- Brier degradation: `-0.0000014312175426606233`
- frozen reference LogLoss: `0.2829004710410182`
- realtime LogLoss: `0.2828850866730461`

2024:

- n `2520`, coverage `1.0`
- exact probability-cell agreement `0.9996031746031746`
- probability MAE `0.00002819913348652663`
- Brier degradation `-0.000002759637317398256`

2025:

- n `2339`, coverage `1.0`
- exact probability-cell agreement `1.0`
- probability MAE `0.0`
- Brier degradation `0.0`

All frozen support gates passed.

## Interpretation

On the available out-of-Development 3s coverage, the V9 realtime object reproduces the frozen 5m shock-reset recovery probability essentially losslessly at `E-3s`. This supports the 3-second risk annotation layer as a faithful realtime representation of the validated 5m process, subject to the explicit 2026 3s coverage gap.

`production_authority=false`.
`blackbox_queried=false`.
