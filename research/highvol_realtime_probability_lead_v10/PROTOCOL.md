# HighVol realtime probability lead V10 — Development protocol

Purpose: measure how early the already-frozen V9 risk probability object remains faithful to the final 5m V6 reference. No model, threshold, probability table, age bucket, payoff, or trading rule is fitted or changed.

Frozen source:
- V9 Development source commit `e01b293dcfc3100a02265315376bc63a9137c3d3`
- frozen V9 runner blob `ae2a7e095df58692ef9df0dfee5856cac727ca44`
- V6 probability table unchanged
- V8 state machine unchanged

Fixed checkpoints: `E-60s`, `E-30s`, `E-15s`, `E-6s`, `E-3s`.

Development boundary: 2020 warm-up/reference; scored 2021-2023; symbols `000688.SH`, `000852.SH`; 2024+ and BlackBox physically excluded.

At each checkpoint the exact V9 composition is rerun using the latest same-block 3s observation at or before the checkpoint. Rows are the exact frozen V6 reference scoring rows. If the partial bar is a fresh shock or provisional NORMAL, the realtime recovery probability remains unavailable exactly as in V9.

Frozen outputs per lead, pooled/by-year/by-symbol:
- probability coverage;
- exact state and probability-cell agreement;
- probability MAE vs final 5m V6 reference;
- realtime/reference Brier and LogLoss;
- Brier/LogLoss degradation;
- unscorable reason counts.

The fixed primary question is `E-15s`, chosen before this Development run. It is eligible for separate reusable Validation only if all hold:
1. pooled coverage >= 0.98;
2. each Development year coverage >= 0.95;
3. pooled probability MAE <= 0.01;
4. pooled Brier degradation <= 0.002;
5. each Development year Brier degradation <= 0.005;
6. frozen V6/V8/V9 definitions remain unchanged;
7. no Validation, BlackBox, PnL, payoff or trading rule is used.

The other leads are diagnostic and cannot be selected post hoc to rescue failure at E-15s.

`production_authority=false`.
