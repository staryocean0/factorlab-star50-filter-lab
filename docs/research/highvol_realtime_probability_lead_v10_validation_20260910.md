# HighVol realtime probability lead V10 — Validation evidence

Status: **SUPPORTED at the preregistered E-15s checkpoint on the available 2024-2025 3s Validation subset**.

This study did not choose a lead after seeing Validation. `E-15s` was fixed as the primary Development question before the V10 Development run. The other `60/30/6/3s` checkpoints remain descriptive and cannot replace failure of the 15-second checkpoint.

Frozen object:

`E-15s causal partial-bar state + time since most recent shock -> frozen V6 P(Normal within next 15 minutes)`

No V6 probability, V8 state threshold, age bucket, state transition, or probability fit changed.

## Evidence

- Development source commit: `c20927b4982655a218521e1187efab2de6ada050`
- Development run: `34445913929`
- Development artifact: `10139657807`
- Development artifact SHA256: `c11c5bd1003a49cd878ad3e19a6be3dcb2c60c1ace34ec0cb66800a1d66c1d47`
- Validation run: `34446224846`
- Validation artifact: `10139762592`
- Validation artifact SHA256: `5b2d1349d7243084981fe5171438eeab9fc4da574bcf7b3c11397416ac1e3ebd`

## Preregistered E-15s Validation result

Pooled 2024-2025:

- reference rows: `4859`
- realtime scored rows: `4833`
- probability coverage: `0.9946491047540647`
- exact state/probability-cell agreement: `0.9921373887854334`
- probability MAE vs final-5m V6 reference: `0.0008067636242397704`
- realtime Brier on matched rows: `0.0805427125993496`
- frozen reference Brier on matched rows: `0.08054771206398999`
- Brier degradation: `-0.000004999464640387252`
- LogLoss degradation: `0.000016100223313331163`

2024:

- coverage: `0.996031746031746`
- probability MAE: `0.0009775257223142327`
- Brier degradation: `0.00010651522930996138`

2025:

- coverage: `0.993159469858914`
- probability MAE: `0.0006222552875342599`
- Brier degradation: `-0.00012549101944683838`

All frozen E-15s support gates passed.

## Interpretation

The validated shock-reset recovery probability can be emitted approximately 15 seconds before the 5-minute reference close with negligible probability error and no material Brier degradation on the available out-of-Development 3s coverage. This promotes `E-15s` as the earliest preregistered realtime probability checkpoint currently supported by both Development and reusable Validation.

The observed 60/30/6/3-second curves are retained as diagnostics only. In particular, 30 seconds must not be promoted post hoc from this same Validation pool.

The repository 3s physical contract ends at 2025-12-31, so this is not complete realtime Validation through 2026-08-21. No 2026 3s or BlackBox data was queried.

`production_authority=false`.
