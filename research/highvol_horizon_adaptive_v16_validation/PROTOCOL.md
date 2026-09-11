# HighVol recovery V16 — frozen horizon-adaptive surface reusable Validation

## Purpose

Run exactly one reusable Validation of the already-frozen V16 horizon-adaptive recovery surface on 2024-01-01 through 2026-08-21. This Validation does not fit, tune, select, rescue, or alter any probability, horizon, state definition, age bucket, shock-reset clock, threshold, or projection.

## Frozen Development authority

- source branch: `research/highvol-horizon-adaptive-surface-v16-20260910`
- Development execution commit: `bcdc18d5886869865c6454fa323ebc6858090249`
- Development run: `34497737506`
- Development artifact: `10160511846`
- frozen surface: `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
- frozen surface Git blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`
- decisive Development action: `FREEZE_EXACT_SURFACE_AND_RUN_REUSABLE_VALIDATION`

The exact frozen object is:

- 15m: frozen `(current_state, recent_shock_age_bucket)` probability;
- 30m: frozen `(current_state, recent_shock_age_bucket)` probability;
- 60m: frozen `recent_shock_age_bucket` probability only;
- emitted probabilities must satisfy `p15 <= p30 <= p60` without any Validation-time projection or adjustment.

## Validation data boundary

- symbols: `000688.SH`, `000852.SH`;
- Validation: 2024-01-01 through 2026-08-21 inclusive;
- 2024 and 2025 use native frozen 5m repository inputs;
- 2026 5m is deterministically synthesized from the sealed one-minute Validation inputs only;
- the already-authorized historical equivalence guard must reproduce native 2023 5m close exactly for both symbols before 2026 synthesis is accepted;
- no observation after 2026-08-21 may enter the physical or measured Validation cohort;
- BlackBox is not queried.

## Frozen comparator

The comparator is the frozen V16 `age_only_comparator` at all three horizons. No comparator is refit on Validation.

## Preregistered support rule

V16 reusable Validation is supported only if all are true:

1. pooled common Validation cohort has at least 3,000 rows and every Validation year is non-empty;
2. every scored row maps to one of the frozen state×age cells and satisfies `p15 <= p30 <= p60`;
3. pooled frozen V16 Brier beats frozen age-only at 15m and 30m;
4. pooled frozen V16 LogLoss beats frozen age-only at 15m and 30m;
5. annual held-out Brier beats age-only in at least 2 of 3 Validation years at both 15m and 30m;
6. at 60m the V16 prediction is exactly the frozen age-only anchor row-by-row, with pooled Brier and LogLoss differences within `1e-12`;
7. the 2023 1m->5m equivalence guard passes for both symbols;
8. sealed 2026 source blobs match the authorized inputs and end no later than 2026-08-21;
9. no fitting, parameter change, threshold search, post-hoc horizon selection, projection change, or rescue is performed;
10. no PnL, payoff, routing, position sizing, or trading rule is computed;
11. BlackBox is not queried and `production_authority=false`.

A failure cannot be rescued using this Validation pool. The result must be sealed as supported or rejected exactly as run.

`production_authority=false`.
