# Current research entry

## 2026-09-11 current authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/gate. It is not a directional trading strategy.

## Current validated realtime multi-horizon recovery object — V17

V17 is complete through Development and its single authorized reusable Validation.

At exactly the preregistered `E-15s` checkpoint before each 5m close, the realtime risk annotation is:

- `15m = frozen V16 state + recent-shock age`, using the frozen V9 provisional partial-bar state;
- `30m = frozen V16 state + recent-shock age`, using the frozen V9 provisional partial-bar state;
- `60m = frozen V16 recent-shock-age-only anchor`.

Realtime gating is unchanged from the frozen V9/V10 semantics:

- fresh partial shock => annotation unavailable;
- provisional `NORMAL` => annotation unavailable;
- missing 3s checkpoint/reference window => annotation unavailable;
- otherwise emit the frozen V16 15/30/60m probabilities with no refit.

Every emitted curve must satisfy `p15 <= p30 <= p60` and the realtime 60m probability must equal the frozen V16 age-only anchor exactly.

### V17 Development authority

- branch: `research/highvol-realtime-horizon-adaptive-v17-20260911`;
- execution commit: `5ae8d6adab6c4afb617ed14ae44327d722e3db49`;
- run: `34603682244`;
- job: `103276864733`;
- artifact: `10265262086`;
- artifact SHA256: `759eda3d30900742bedd9494fef9c64ed91af66068892aceaa01e610a684101c`;
- frozen transfer blob: `5aca30ff398f73173a5424aa14b535bd461df5b4`;
- exact V11 cohort: `7327` rows;
- realtime-scored rows: `7310`;
- coverage: `0.9976798144`;
- exact realtime/final state agreement: `0.9954856361`;
- Development decision: `FREEZE_EXACT_E15S_TRANSFER_AND_RUN_REUSABLE_2024_2025_VALIDATION`.

Pooled Development transfer error versus frozen final-5m V16:

- 15m probability MAE `0.000381438`, Brier degradation `+0.000042377`;
- 30m probability MAE `0.000406241`, Brier degradation `+0.000099892`;
- 60m probability MAE/Brier/LogLoss degradation exactly `0.0`.

### V17 reusable Validation authority

- branch: `research/highvol-realtime-horizon-adaptive-v17-validation-20260911`;
- execution commit: `a35a9f496c7772bf9a81a7b85b0cd0b3d6fccfe2`;
- run: `34604089926`;
- job: `103278189791`;
- artifact: `10265472702`;
- artifact SHA256: `65783daff1ca83217ad8159b52e2c4f9d6c79f8195a11aa4b1c4af80aa2d1714`;
- Validation period: `2024-01-01` through `2025-12-31`;
- common cohort: `4540` rows (`2024=2339`, `2025=2201`);
- realtime-scored rows: `4516`;
- coverage: `0.9947136564`;
- exact realtime/final state agreement: `0.9918069088`;
- `full_validation_supported=true`.

Pooled reusable Validation transfer error versus frozen final-5m V16:

- 15m probability MAE `0.000824551`, Brier degradation `-0.000006965`, LogLoss degradation `+0.000006648`;
- 30m probability MAE `0.000637991`, Brier degradation `+0.000171425`, LogLoss degradation `+0.000543736`;
- 60m probability MAE/Brier/LogLoss degradation exactly `0.0`.

Annual coverage and Brier guards also passed:

- 2024 coverage `0.9961522018`; 15m/30m Brier degradation `+0.000109419 / +0.000317005`;
- 2025 coverage `0.9931849159`; 15m/30m Brier degradation `-0.000131016 / +0.000016254`.

All `4516` emitted Validation curves are monotone and the row-level 60m anchor difference is exactly `0.0`.

Primary sealed V17 evidence:

- `research/highvol_realtime_horizon_adaptive_v17/PROTOCOL.md`;
- `research/highvol_realtime_horizon_adaptive_v17/DEVELOPMENT_RESULTS.md`;
- `research/highvol_realtime_horizon_adaptive_v17/FROZEN_REALTIME_TRANSFER.json`;
- `research/highvol_realtime_horizon_adaptive_v17/DECISIVE_RECEIPT.json`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/PROTOCOL.md`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`;
- `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json`.

## Important realtime boundary

The repository's authorized 3s physical contract ends at `2025-12-31`.

Therefore V17 establishes realtime multi-horizon authority on available **2024-2025 3s reusable Validation coverage only**. It does **not** establish any 2026 realtime claim, and no 2026 3s data was queried or synthesized.

Do not extrapolate V17's realtime authority to 2026 merely because the final-5m V16 object has 2026 Validation support.

## Current validated final-5m recovery object — V16

V16 remains the final-5m multi-horizon authority through `2026-08-21`:

- `15m = current_state {UNSAFE, RECOVERING} + time-since-most-recent-shock`;
- `30m = current_state {UNSAFE, RECOVERING} + time-since-most-recent-shock`;
- `60m = time-since-most-recent-shock only`.

Age buckets remain fixed as `<15m`, `15-25m`, `30-40m`, `>=45m`. Every new shock resets the recovery clock.

V16 reusable Validation authority:

- run: `34602527314`;
- artifact: `10264689647`;
- artifact SHA256: `e28a877d40c3bd2464b4f09b1078cdfae83a7ecebcc8bbd34fdb7bad4e8d82f5`;
- common scored rows: `5908`;
- year rows: `2024=2339`, `2025=2201`, `2026=1368` through `2026-08-21`;
- `full_validation_supported=true`.

Pooled frozen improvement over age-only:

- 15m: Brier `+0.00268837`, LogLoss `+0.00890434`;
- 30m: Brier `+0.00305660`, LogLoss `+0.00980693`;
- 60m: exactly the age-only anchor.

V11-V16 are a completed causal evidence chain and must not be rerun merely to reconfirm V17.

## Why V16/V17 have this structure

- V11: unified 15/30/60m `state + age` survival surface rejected in Development;
- V12: simple shock-expiry explanation rejected;
- V13: exact recent-shock-age sample composition did not explain the 60m crossover;
- V14: established horizon-dependent incremental state value — useful at 15m/30m, unstable at 60m;
- V15: Development block/bootstrap adjudication supported the same conclusion;
- V16: froze horizon-adaptive 5m surface and passed reusable Validation through 2026-08-21;
- V17: transferred that exact surface to the frozen `E-15s` realtime measurement and passed Development plus reusable 2024-2025 3s Validation.

The scientific conclusion is now two-layered:

1. final-5m recovery probability is horizon-adaptive: state adds stable information at 15m/30m but not 60m;
2. this exact 15/30/60m object can be emitted 15 seconds before the 5m close with very small degradation on the available 3s coverage.

## 2026 5m construction authority

2026 final-5m Validation bars were deterministically synthesized from sealed one-minute Validation inputs only after the historical 2023 equivalence guard passed exactly for both indices:

- 242 common 2023 days per symbol;
- 11,616 rows per symbol;
- `max_abs_close_diff=0.0` for both symbols.

The authorized 2026 one-minute inputs contain 154 complete trading days through `2026-08-21` and synthesize to 7,392 5m rows per symbol.

This construction authority applies to V16's final-5m object; it does not create 2026 3s data for V17.

## Earlier supported risk process

The supported post-shock mechanism remains:

`shock -> UNSAFE / RECOVERING -> Normal`

with the clock rule:

> Every new shock resets the recovery clock. Recovery risk is indexed by time since the most recent shock, not time since the first shock of the episode.

Relevant prior authority:

- V3: `UNSAFE` vs `RECOVERING` separates near-term normalization probability;
- V4: state×age recovery calibration passed Development and reusable Validation;
- V5: recurrent shock sharply lowers near-term normalization probability and resets recovery; no universal separate `CLUSTERED` state was supported;
- V6: recent-shock age beat episode-start age and passed full reusable Validation through 2026-08-21;
- V7: 1m realtime detector failed preregistered UNSAFE recall and was not promoted;
- V8: frozen 3s detector passed Development and available 2024-2025 reusable Validation subset;
- V9: unified realtime risk object passed the same subset;
- V10: preregistered `E-15s` realtime 15m probability annotation passed Development and available 2024-2025 reusable Validation subset.

## Scope-repaired bucket authority

This repository owns bottom-layer causal K-line risk-state research only, including:

- volatility level / expansion;
- shock isolation and recurrence;
- `Unsafe / Recovering / HighVol` state evolution;
- switch-on, persistence, recovery and recovery probability;
- cross-scale 3s / 1m / 5m risk attributes and failure cases.

The current task is **not** to optimize a directional trading strategy, holding period, stop/target, sizing, account overlay or payoff router.

Historical HighVol Router V1, historical directional STAR50 V10-V17 sign-flip work, half-day slope work, drawdown/account/payoff diagnostics and misplaced R1/R2 material remain preserved but are not current authority. The historical payoff V17 branches are unrelated to the current risk-state V17 and must not be revived.

Correct neighboring buckets:

- `factorlab-two-wave-strategy-lab`: causal parent-structure classification into range / uptrend / downtrend from completed same-scale waves;
- `factorlab-trend-reversion-regime-lab`: concrete reversal / mean-reversion strategy research including R1/R2.

## Data and governance

Read before new work:

- `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`;
- `docs/governance/DATA_USAGE_POLICY_V2.md`;
- `docs/governance/data_usage_declaration.json`;
- `docs/governance/blackbox_query_ledger.json`.

Forward data roles:

- 2020: warm-up only where needed;
- Development: 2021-2023;
- reusable Validation: 2024 through 2026-08-21 for authorized 5m work;
- 3s realtime Validation coverage: 2024-2025 only under the physical contract;
- protected BlackBox-V1: strictly after the cutoff under its frozen aggregate-only protocol.

No prior payoff or risk-state Validation result automatically authorizes BlackBox access.

## Current breakpoint

V17 is complete and sealed. The current decisive state is:

`V17_E15S_MULTI_HORIZON_REALTIME_VALIDATION_SUPPORTED_2024_2025`

Do **not** rerun V11-V17, refit V16, alter V17 gating, test E-30s/E-60s post hoc on the inspected Validation pool, fabricate/synthesize 2026 3s coverage, or query BlackBox.

No V18 protocol has been authorized or started.

`queried_2026_3s=false`.
`blackbox_queried=false`.
`production_authority=false`.
