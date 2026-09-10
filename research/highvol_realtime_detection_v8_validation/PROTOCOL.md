# HighVol realtime detection V8 — frozen 3s Validation protocol

Purpose: evaluate the already-frozen V8 3-second partial-bar detector on the available reusable Validation subset without changing any state threshold, checkpoint, feature, or acceptance rule. This remains a risk-state measurement study only; no PnL, payoff, routing, position sizing, or trading rule is created.

## Frozen Development authority

The detector is frozen from Development branch `research/highvol-realtime-detection-v8-3s-20260910` at commit `07bfa63018fe4d1a1afa4f108a14d9be5ae86777`.

Development evidence:

- Actions run: `34426934097`
- artifact: `10133063809`
- frozen runner blob SHA: `9e1828a8e7ff6b45eba0b4d1e31e79c1f9c1568a`
- frozen protocol blob SHA: `a23728a029c17c28384d8ce372e73dac0d312944`
- Development primary checkpoint: `E-3s`
- Development pooled UNSAFE precision: `0.9996562392574768`
- Development pooled UNSAFE recall: `0.9979409746053535`
- Development eligibility: PASS

## Frozen state machine

Unchanged from V8 Development:

- 5m log return within trading day;
- `rv12 = std(last 12 valid 5m returns, ddof=0)`;
- `bg48 = std(previous 48 valid 5m returns, ddof=0)`;
- `shock = abs(ret_5m)/bg48 >= 3.0`;
- `UNSAFE` after shock, or while `vol_ratio=rv12/bg48 >= 1.50`;
- `RECOVERING` while `1.10 < vol_ratio < 1.50` after an active risk episode;
- `NORMAL` once `vol_ratio <= 1.10`;
- state transition uses the previous completed 5m reference state.

Frozen checkpoints remain `E-60s`, `E-30s`, `E-15s`, `E-6s`, `E-3s`. The primary acceptance checkpoint remains `E-3s`; earlier checkpoints are descriptive only.

At each checkpoint, use the latest same-block 3s observation at or before the checkpoint; if duplicate timestamps exist, the greatest stable `row_index` wins. No interpolation and no future observation are allowed.

## Validation data boundary

The project Validation pool is broader, but the repository 3s physical contract currently ends at 2025-12-31. Therefore this run evaluates only the physically available Validation subset:

- 5m reference history: 2020-2025, used only to construct the unchanged causal reference state;
- measured Validation years: 2024 and 2025;
- symbols: `000688.SH`, `000852.SH`;
- 3s measured inputs: only 2024 and 2025 files for both symbols;
- no 2026 3s data is available or queried;
- BlackBox is excluded physically and logically.

A PASS here means “passes available 2024-2025 3s Validation subset.” It must not be represented as complete 2024-2026-08-21 validation.

## Frozen acceptance rule

At `E-3s`, all must hold:

1. pooled usable coverage >= 0.95;
2. each measured Validation year usable coverage >= 0.95;
3. pooled final-UNSAFE precision >= 0.90 and recall >= 0.90;
4. each measured Validation year final-UNSAFE precision >= 0.85 and recall >= 0.85;
5. frozen state thresholds, checkpoint selection, and source detector are unchanged;
6. no PnL, payoff, trading rule, parameter search, or BlackBox query occurs.

All `60/30/15/6/3s` diagnostics are reported, but no lead may be selected post hoc to rescue a failure at 3 seconds.

`production_authority=false` regardless of PASS/FAIL.
