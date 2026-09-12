# Intrabar temporal reversal incremental utility V1 — results

Decision: **`INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_NOT_SUPPORTED`**.

## What was tested

This study tested a genuinely order-sensitive current-bar mechanism at E15: whether the ordering of the current 5-minute bar's 19 valid adjacent 15-second returns adds future non-PnL risk information beyond the inherited D4-style own-index current continuous baseline.

Frozen models:

- `C`: inherited 84-column D4-style own-index current E15 baseline;
- `T`: `C` + `ARF19` / `LAC19` order-sensitive block;
- `O`: `C` + `FRMS19` / `NPE19` equal-complexity order-invariant current-bar control;
- `T` and `O` are both 104 columns, use the same rows, same nonlinear expansion, same state interactions and ridge lambda `0.01`.

`ARF19` measures adjacent sign reversals. `LAC19` measures amplitude-weighted lag-1 local persistence/reversal. Both are invariant to a global sign flip, so the study does not encode trade direction.

## Execution authority

Decisive Actions run: `34685234360`.

- fit job: `103530973458`;
- reusable Validation job: `103531117262`;
- frozen-model artifact: `10295610761`, ZIP SHA256 `cc1602a19c3dd802737a279c19ebe2ac42a51dd46d6e88dfc42d52f75b84ec2c`;
- Validation artifact: `10294993214`, ZIP SHA256 `3066af6fc8963fb5948d6ac6d0afd26de7fa87746d00294c22630b62dc4f3a0e`;
- frozen model SHA256: `bd01e23def9300781c64a03f8377247ff30c67d0191c6cd213329d382ff8262c`;
- `VALIDATION_RESULTS.json` SHA256: `67b267af11802562f4f576d151472b064323c82af2a34e4451e471beb99b2cdc`.

The fit workspace physically excluded 2024–2026. Only after Development fit completed and exact model bytes were frozen did the same run unlock 2024–2025 reusable Validation. Protected 2026 rows were not read; synthetic 2026 data was not used; BlackBox was not queried; PnL was not computed.

## Decisive Validation results

All six endpoint × horizon joint promotions are false. All 12 formal comparisons are unsupported, and more strongly, **all 12 pooled Validation point estimates are negative**.

| Horizon | Endpoint | T vs C relative gain | T vs O relative gain | Joint supported |
|---|---|---:|---:|---|
| 15m | log future RMS | -0.11882% | -3.39167% | No |
| 15m | future tail | -0.03582% | -1.20147% | No |
| 30m | log future RMS | -0.16112% | -4.87737% | No |
| 30m | future tail | -0.02648% | -1.41548% | No |
| 60m | log future RMS | -0.19747% | -6.13570% | No |
| 60m | future tail | -0.00902% | -2.00825% | No |

This is not a near-promotion result blocked only by confidence intervals or practical thresholds. The fixed temporal-order model is worse than `C` at every endpoint/horizon and is materially worse than the equal-complexity order-invariant `O` control at every endpoint/horizon.

The strongest negative separation is 60m future RMS: `T vs O = -6.13570%`. Its family-adjusted 5-day absolute-gain interval is entirely negative (`-0.009490820998304195` to `-0.0043866678382002994`), and both index slices are negative. The 15m and 30m `T vs O` RMS intervals are also entirely negative.

Tail endpoints also fail decisively. Every tail absolute gain is negative, so none can satisfy the frozen `+0.0005` Brier practical gate.

## Availability and sample boundary

Validation common-path coverage passes the frozen 95% gate:

- 15m: `96.9902%` (`38,573 / 39,770`);
- 30m: `96.5891%` (`32,792 / 33,950`);
- 60m: `95.0515%` (`21,206 / 22,310`).

Development common-path coverage is much lower:

- 15m: `53.4941%`;
- 30m: `53.2757%`;
- 60m: `52.4759%`.

This historical availability limitation does not cause the main scientific rejection because the Validation point estimates themselves are already negative. It does, however, make the 60m formal sample-size gate fail: Development `n=17,549 < 20,000`.

## Interpretation

The result supports a narrow negative statement about this frozen representation:

> Given the inherited D4 current E15 risk coordinates, the fixed pair `ARF19/LAC19` does not provide robust incremental future-risk information. On the same feasible rows, the permutation-invariant fine-scale amplitude/path block `FRMS19/NPE19` is consistently more predictive than the temporal-order block.

This does **not** prove that all possible intrabar ordering information is useless. It does prove that this preregistered 15-second, 19-return adjacent-reversal/lag-1-alignment specification is not promotable and may not be rescued after Validation.

## Closed rescue paths

The V1 result may not be rescued by:

- changing to the raw 3-second grid;
- moving E15 nearer to bar close;
- changing the number of returns;
- adding run length, entropy, crossing count, motif, DTW or other path-shape searches;
- changing zero-return treatment;
- selecting a favorable state, slot, year, horizon or index;
- changing ridge lambda or thresholds;
- lowering the 1% practical gate or tail `0.0005` gate;
- removing the order-invariant `O` control;
- reopening multiscale-volatility or signed-asymmetry rescue paths.

Any future study must pose a genuinely different causal mechanism before seeing results. Otherwise the correct action is hold/maintain authority.

## Authority boundary

No temporal-reversal field or decision gate is added to D5. D4 and D5 decisions remain unchanged. V19 remains frozen. No D6/V20 is started. No candidate, trading action, PnL interpretation, router change or production authority is created.

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `synthetic_2026_used=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`.
