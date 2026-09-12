# Cross-index residual dislocation incremental utility V1 — results

Decision: **`CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

## What was tested

This study tested whether an E15 **dynamic cross-index relationship residual severity** adds future non-PnL risk information after both the target index's own D4-style current I/V information and the other index's contemporaneous current I/V are already known.

Frozen models:

- `B`: 99-column own-index D4-style baseline + current other-index I/V nuisance block;
- `R`: `B + RZ48`, where `RZ48` is the absolute 48-paired-return trailing-OLS residual severity;
- `Q`: `B + QZ48`, where `QZ48` is an equal-complexity equal-weight spread severity control;
- `R/Q = 107 columns`, same rows, same nonlinear/state expansion and ridge `0.01`.

Only absolute dislocation severity enters the model. Residual sign, rich/cheap direction and beta direction carry no predictive or trading authority.

## Decisive execution

- source main: `e30a0eb0e0884a569110c8819fb4b2696bb9dd29`;
- frozen study head: `f795845e3ec6abcd201e638c7264cb78ffe0e729`;
- decisive Actions run: `34688304454`;
- Development fit job: `103539075057`;
- reusable Validation job: `103539290902`;
- frozen-model artifact: `10296505999`, ZIP SHA256 `76efc29fcae706e698bc1ea6ae7918389f72766756f5b3ad90a0ba75929ea827`;
- Validation artifact: `10295914902`, ZIP SHA256 `80da5740e89582c47e147a7ce3a590c75eabee9599a35b5f52bc110f4403fb33`;
- frozen model SHA256: `8f37d237172a86c23aa75baf3f69f2f5b8948cbbd12c267bdde5da6864607d94`;
- `VALIDATION_RESULTS.json` SHA256: `2cc44ce7baff43dfd84884e6ce1ebf81aada12c2644e1bbe48384ac4d8f82654`.

Development 2021–2023 was fitted and frozen before 2024–2025 reusable Validation was opened. Protected 2026 rows were not read; synthetic 2026 data was not used; BlackBox was not queried; PnL was not computed.

## Formal Validation results

All six endpoint × horizon joint promotions are false. All 12 formal comparisons have `supported=false`.

| Horizon | Endpoint | R vs B relative gain | R vs Q relative gain | Joint supported |
|---|---|---:|---:|---|
| 15m | log future RMS | +0.11686% | -0.01174% | No |
| 15m | future tail | +0.23570% | +0.08571% | No |
| 30m | log future RMS | +0.20754% | +0.04428% | No |
| 30m | future tail | +0.17887% | +0.07457% | No |
| 60m | log future RMS | +0.19959% | +0.03745% | No |
| 60m | future tail | +0.22107% | +0.07897% | No |

This is a **weak-information / no-practical-promotion** result, not a claim that residual dislocation contains no signal.

Against `B`, all six pooled point estimates are positive. The strongest statistical case is 30m future RMS: `R vs B = +0.20754%`, its family-adjusted 5-day absolute-gain interval is entirely positive (`0.00002458597848098955` to `0.0007121645590173982`), and all 2024/2025 and both target-index slices are positive.

However, that effect is still only about one fifth of the frozen **1.00%** practical gate. The largest `R vs B` relative gain anywhere is only `+0.23570%`.

More importantly, once compared with the equal-complexity generic pairwise-dispersion control `Q`, the residual-specific increment nearly disappears:

- maximum `R vs Q` relative gain: only `+0.08571%`;
- 15m RMS is negative (`-0.01174%`);
- no `R vs Q` comparison has a positive family-adjusted 5-day lower bound;
- no `R vs Q` comparison is remotely close to the 1% practical gate.

Tail effects are also too small. The largest tail absolute Brier gain is `0.00018560800053409512`, below the frozen `0.0005` threshold.

## Coverage and sample boundary

Availability is not the cause of rejection. Common relationship/control coverage is 100% among otherwise-feasible `B` rows in both Development and Validation:

- 15m Validation: `39,770`;
- 30m Validation: `33,950`;
- 60m Validation: `22,310`.

Development final-fit sizes are `59,614 / 50,890 / 33,442`. All frozen sample-size gates are satisfied. Tail positive-event counts are `1,296 / 1,886 / 2,215`.

## Interpretation

The correct narrow conclusion is:

> Cross-index relative misalignment carries a small amount of future-risk information after current own/other I/V are known, but the preregistered trailing-beta residual geometry does not demonstrate a practically material independent increment over a simple equal-weight cross-index spread severity control.

The statistically clean 30m RMS `R vs B` result is therefore a **weak statistical hint**, not a promotion. It cannot be promoted by ignoring the 1% gate or the `R vs Q` control.

## Closed rescue paths

This V1 may not be rescued by:

- changing the 48-return relationship window;
- robust/ridge/rolling-correlation/cointegration alternatives;
- changing or removing `QZ48`;
- using residual sign, rich/cheap direction or beta direction;
- selecting one index, year, state, slot or horizon;
- moving E15 or reading the final current-bar close;
- lowering the 1% or tail `0.0005` practical gates;
- reopening directional RMR mean-reversion, intrabar ordering, signed asymmetry or multiscale-volatility variants.

## Research-program consequence

The repository audit had already closed the executable historical backlog. The remaining old RMR mechanisms were either directional/reversal questions outside the current risk-attribute mandate or duplicates of closed axes. Residual-dislocation was the remaining independently preregisterable non-directional mechanism identified in that audit, and this fixed V1 is now closed.

Therefore the current research action is **HOLD CURRENT AUTHORITY** until either:

1. a genuinely new causal mechanism can be defined before outcomes are inspected, or
2. new prospective data creates a scientifically different test opportunity.

This does not assert that no future mechanism can ever exist; it means no currently identified repository mechanism is eligible for immediate execution without post-hoc feature search.

## Authority boundary

No residual-dislocation field or gate is added to D5. D4/D5 decisions remain unchanged. V19 remains frozen. Intrabar temporal ordering, signed asymmetry and multiscale-volatility rescue paths remain closed. No D6/V20, candidate, trading action, PnL interpretation, router change or production authority is created.

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `synthetic_2026_used=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `research_hold=true`; `production_authority=false`.
