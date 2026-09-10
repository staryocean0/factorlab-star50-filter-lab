# HighVol realtime probability lead V10 — frozen Validation protocol

Frozen Development authority:

- source branch: `research/highvol-realtime-probability-lead-v10-20260910`
- source commit: `c20927b4982655a218521e1187efab2de6ada050`
- Development run: `34445913929`
- Development artifact: `10139657807`
- artifact SHA256: `c11c5bd1003a49cd878ad3e19a6be3dcb2c60c1ace34ec0cb66800a1d66c1d47`
- frozen V10 runner blob: `783b5bb474758956b7b86a0e8c72a1264ab2e1e5`
- frozen V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`

Primary checkpoint remains `E-15s`. The 60/30/6/3-second leads are diagnostics only and cannot replace a failure at 15 seconds.

No V6 probability, V8 state threshold, age bucket, checkpoint, probability fit or state transition may change.

Validation uses only the physically available 3s subset 2024-2025 for both indices; 5m reference history is 2020-2025. No 2026 3s or BlackBox input is queried.

Frozen E-15s support screen is unchanged from Development:

1. pooled probability coverage >= 0.98;
2. each measured year coverage >= 0.95;
3. pooled probability MAE versus final-5m V6 reference <= 0.01;
4. pooled Brier degradation <= 0.002;
5. each measured year Brier degradation <= 0.005;
6. no fitting/tuning/PnL/payoff/trading/BlackBox.

A PASS is support on the available 2024-2025 3s Validation subset, not complete realtime Validation through 2026-08-21.

`production_authority=false`.
