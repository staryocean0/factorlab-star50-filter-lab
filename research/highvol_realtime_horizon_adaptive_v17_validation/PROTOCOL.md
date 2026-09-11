# HighVol realtime horizon-adaptive recovery V17 — reusable Validation protocol

## Purpose

Validate the exact frozen V17 `E-15s` transfer on the repository's already-existing 2024-2025 3s coverage. No 2026 3s data is available or authorized, so this Validation does not make a 2026 realtime claim.

The frozen object is unchanged:

- 15m: frozen V16 `(partial_state, recent-shock age bucket)` probability;
- 30m: frozen V16 `(partial_state, recent-shock age bucket)` probability;
- 60m: frozen V16 age-only anchor;
- checkpoint: exactly `E-15s`;
- fresh partial shock / provisional `NORMAL` / missing checkpoint or reference window => realtime object unavailable.

## Frozen Development authority

- V17 Development execution commit: `5ae8d6adab6c4afb617ed14ae44327d722e3db49`;
- run: `34603682244`;
- artifact: `10265262086`;
- artifact SHA256: `759eda3d30900742bedd9494fef9c64ed91af66068892aceaa01e610a684101c`;
- frozen transfer blob: `5aca30ff398f73173a5424aa14b535bd461df5b4`;
- frozen Development runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`;
- frozen Development protocol blob: `e99c56394699642bf86fbe316ff2b05338f23896`;
- Development decision: `FREEZE_EXACT_E15S_TRANSFER_AND_RUN_REUSABLE_2024_2025_VALIDATION`.

## Validation boundary

- 5m reference/warm-up: 2020-2025;
- scored reusable Validation: 2024-01-01 through 2025-12-31;
- 3s inputs: 2024 and 2025 only;
- symbols: `000688.SH`, `000852.SH`;
- 2026 3s data is physically excluded;
- BlackBox is physically and logically excluded.

The exact frozen V11 cohort construction is reused with only the role years changed to 2024-2025. The V9 realtime state measurement is reused with only the role years changed to 2024-2025.

## Fixed acceptance

The frozen V17 transfer is reusable-Validation-supported only if all hold:

1. pooled common cohort has at least `3000` rows and both Validation years are nonempty;
2. V11 and V9 final 5m states align exactly on every cohort row;
3. pooled realtime coverage is at least `0.98`;
4. each Validation year coverage is at least `0.95`;
5. pooled probability MAE versus frozen final-5m V16 is at most `0.01` at both 15m and 30m;
6. pooled Brier degradation is at most `0.002` at both 15m and 30m;
7. each Validation year Brier degradation is at most `0.005` at both 15m and 30m;
8. every emitted realtime row remains monotone: `p15 <= p30 <= p60`;
9. 60m realtime probability remains exactly the frozen V16 age-only anchor, with MAE/Brier/LogLoss degradation zero within `1e-12`;
10. the frozen transfer, V16 probabilities, V9 thresholds, V11 cohort definition, age buckets, horizons, and E-15s checkpoint are unchanged;
11. no fit, threshold search, projection change, lead-time search, or post-hoc horizon selection is performed;
12. no 2026 3s data and no BlackBox data is queried;
13. no PnL, payoff, routing, sizing, leverage, or trading rule is computed.

A failure cannot be rescued by another checkpoint, changing gating semantics, dropping a year/horizon, or modifying probabilities/state definitions.

A PASS validates the realtime V17 multi-horizon risk annotation only on available 2024-2025 3s coverage. It does not create production authority and does not authorize BlackBox.

`production_authority=false`.
