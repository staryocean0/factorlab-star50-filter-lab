# V14 horizon-specific recovery surface — frozen full Validation protocol

Purpose: evaluate the already-frozen V14 horizon-specific recovery surface on the reusable Validation pool through 2026-08-21 without refitting, tuning, or changing any risk-state rule.

## Frozen Development authority

- source branch: `research/highvol-horizon-specific-state-value-v14-20260910`
- frozen Development head: `30fdc567dab552c165a703dbfd623151c077bfd5`
- execution commit: `a9223748933fc842a68865a3837e24f49f014691`
- Development run: `34454169246`
- artifact: `10142758729`
- artifact SHA256: `129271138720dcf972345006ea7e938aed0356531d2fa2d872e2aaa8d06d7f9f`
- frozen surface blob: `be06a4988fb4a602e2b72d115268c926421aa1f5`

The frozen object contains two fixed comparators:

1. `age_only`: 4 recent-shock-age cells;
2. `state_plus_age`: 8 current-state × recent-shock-age cells.

Each contains fixed Beta(1,1)-smoothed probabilities for Normal-within-15m, Normal-within-30m and Normal-within-60m. No probability may be re-estimated in Validation.

## Validation boundary

Measured years: 2024, 2025, 2026 through 2026-08-21.

- Native 5m 2020–2025 may be used for causal history and measured 2024/2025 rows.
- 2026 5m is deterministically synthesized from the already-sealed 1m Validation inputs under the user-authorized contract previously verified in V6.
- 2023 1m→5m synthesis must match the existing native 2023 5m closes exactly before 2026 scoring is permitted.
- sealed 2026 Git blobs must equal:
  - `000688.SH`: `4626fb307bbcae1c417ddcd69ac694cf322c8bbc`
  - `000852.SH`: `8de5cd3caab99dbacae229a2c87f15c4ff2f8558`
- 2026 source maximum trading day must be `<= 2026-08-21`.
- BlackBox rows are physically and logically excluded.

## Frozen sample and state semantics

Identical to V11/V14 Development:

- same two symbols;
- same V6 state machine and thresholds;
- every new shock resets recent-shock age;
- same age buckets: `<15m`, `15–25m`, `30–40m`, `>=45m`;
- same common cohort requiring full 60 trading minutes of same-day future support;
- same cumulative outcomes: Normal within 15m / 30m / 60m.

No PnL, payoff, routing, position sizing or trading rule is permitted.

## Pre-registered acceptance

V14 full Validation is supported only if all are true:

1. pooled common-cohort rows >= 3000 and every Validation year is nonempty;
2. frozen `state_plus_age` Brier is lower than frozen `age_only` Brier at all 15/30/60m horizons pooled;
3. frozen `state_plus_age` LogLoss is lower than frozen `age_only` LogLoss at all three horizons pooled;
4. for each horizon, `state_plus_age` Brier is lower than `age_only` in at least 2 of the 3 Validation years;
5. no fit/refit, threshold search, parameter change or post-hoc horizon selection occurs;
6. 2023 synthesis equivalence passes, 2026 blob/cutoff guards pass, and BlackBox remains unqueried.

Failure at 60m cannot be rescued by dropping 60m or selecting only 15m/30m. A PASS means the horizon-specific recovery surface is reusable-Validation-supported through 2026-08-21; it does not grant production authority.

`production_authority=false`.
