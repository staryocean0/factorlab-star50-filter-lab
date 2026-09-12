# One-step degree-trajectory incremental utility V1 — Results

Date: 2026-09-12  
Decision: **`ONE_STEP_DEGREE_TRAJECTORY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**

This study formally tested a field family that D4/D5 had already carried but had never independently validated for predictive utility: the one-step change in own-index continuous risk degree. Because current E-15 intensity / volatility ratio is already present in the C baseline, adding the immediately preceding confirmed degree is raw-information equivalent to adding the current-minus-lag1 delta pair.

The frozen V1 result is negative for promotion. Lag-1 degree contains a small amount of extra future-RMS information relative to the current-level baseline, especially at 30 minutes, but the effect is only about 0.1%–0.15%, far below the preregistered 1% practical gate. The equal-complexity lag-2 control also prevents interpreting this small gain as a stable, uniquely one-step trajectory effect. Tail gains are tiny and several T-vs-O comparisons are negative.

Therefore D4/D5 `delta_intensity` / `delta_ratio` remain descriptive transport fields only; this study does **not** grant them independent predictive promotion.

## Frozen identities

- source main at freeze: `e29c44cd61cdfcead7321a036850d7cd1b33006b`
- protocol Git blob: `fe2eebaa6b15c3f9a57ce05b3295b015acba7ea7`
- study runner Git blob: `0afc45e5061f45f544ecc7ee4519eae4e5204bca`
- frozen parent cross-index/D4-style runner blob: `b4d3c72e58706b2eb9ae8425f7e7f5439ba002c5`
- original frozen model SHA256: `04b49e8613cad5b24822f8e827f8d6513f6fef74da5c2df0851e03473b4db188`
- decisive Actions run: `34680352701`
- fit job: `103517762036`
- Validation job: `103517878447`
- fit artifact: `10293132822`, ZIP SHA256 `01cb69405d54b2af333e9d4de768669c9ccf42f0f789b2cf0dfc01b78864b64c`
- Validation artifact: `10294052627`, 68,727 bytes, ZIP SHA256 `60c9133dbf6632b2f7dcf9795c70038ed50f4d18718fc54aaf2378010ceaeba8`
- `VALIDATION_RESULTS.json` SHA256: `16e7db8b780f64cfa0fcc5091d3ab1feed4c63658465697381b2ae9dda390763`

The complete decisive Validation artifact has been copied byte-for-byte into `evidence/`. `EVIDENCE_SOURCE.json` records its source identity.

## Frozen model family

- **C**: 84-column own-index D4-style causal baseline containing confirmed history, previous state / recent-shock age, and current E-15 I/V.
- **T**: C + 20-column nonlinear/state-interaction block from the immediately preceding confirmed degree (`lag1_intensity`, `lag1_ratio`).
- **O**: C + the identical 20-column block from the two-valid-return-bars-back degree (`lag2_intensity`, `lag2_ratio`).

T and O are both 104 columns with identical feature names, scaling and ridge penalty. `T vs O` is the critical recency/trajectory control.

With current I/V already in C, `current - lag1 = delta1`; thus lag1 and the delivered one-step delta are bijective at the raw-coordinate level. This validates the information question for the one-step trajectory, not every imaginable nonlinear re-encoding of delta.

Five causal/complexity tests passed before Development fit and again before Validation. Current final price/return/state and future rows are not used to construct the current lag coordinates.

## Cohort / availability

Trajectory coverage among otherwise own-base + future-feasible rows is 100% in Development and Validation:

- 15m: Development 59,614; Validation 39,770;
- 30m: Development 50,890; Validation 33,950;
- 60m: Development 33,442; Validation 22,310.

No 2026 protected detail was checked out. BlackBox was not queried.

## Formal Validation results

Relative squared-loss reductions of T are:

| Horizon | Endpoint | T vs C | T vs O | Joint supported |
|---|---|---:|---:|---|
| 15m | log future RMS | +0.11415% | +0.11321% | No |
| 15m | future tail | +0.03753% | **-0.00340%** | No |
| 30m | log future RMS | **+0.14957%** | **+0.15160%** | No |
| 30m | future tail | +0.03919% | **-0.03684%** | No |
| 60m | log future RMS | +0.02416% | **-0.04063%** | No |
| 60m | future tail | +0.04523% | +0.01985% | No |

All twelve formal comparisons fail the frozen 1% relative practical gate. Six endpoint × horizon joint promotions are all false.

Tail absolute Brier gains are also tiny, around `-0.000018` to `+0.000038`, all far below the frozen `0.0005` gate.

## What the strongest signal does and does not mean

30m log future RMS is the strongest trajectory result:

### T vs C

- n = 33,950;
- relative gain = **+0.14957%**;
- absolute squared-loss gain = `0.00025438`;
- adjusted 5-day interval = `[0.00002614, 0.00051244]`, positive;
- both symbols and both Validation years have nonnegative gain signs;
- 2023 forward gain is positive.

So it is fair to say the immediately preceding confirmed degree contains **a small amount of incremental statistical information** beyond C for 30m future RMS.

### T vs O

- relative gain = **+0.15160%**;
- absolute gain = `0.00025784`;
- adjusted 5-day interval = `[-0.00004682, 0.00058918]`, crossing zero;
- year/symbol signs are nonnegative;
- 2023 forward gain is positive.

The mechanism comparison therefore does not establish that the most recent step is stably better than an equally complex older-degree history representation. More importantly, both point estimates are only about **0.15%**, roughly one-seventh of the frozen 1% practical threshold.

15m RMS is similarly small (~0.11%) and both adjusted intervals cross zero. At 60m T vs O becomes negative.

## Tail endpoints are unsupported

All 15/30/60m tail comparisons are <0.05% in magnitude. `T vs O` is negative at both 15m and 30m. Tail absolute Brier gains never approach `0.0005`; adjusted intervals cross zero and several cross-slice / forward gates fail.

There is no support for using one-step degree trajectory as an independently validated tail-risk coordinate.

## Development-forward discipline

The final model bytes were frozen on 2021–2023 before Validation. The pre-Validation 2023 forward diagnostics showed:

- future-RMS: small positive gains for T vs both C and O at all 15/30/60m horizons;
- future-tail: T vs C negative at all three horizons; T vs O only small positive values.

These signs were recorded before Validation and not used to alter the frozen specification.

## Scientific interpretation

The correct conclusion is not “delta is useless.” It is narrower:

> Once current own-index I/V and the existing state/history context are known, this fixed one-step degree trajectory contains at most a small future-RMS increment, but it does not show enough magnitude or stable advantage over a same-complexity lag-2 degree control to justify independent predictive promotion.

Accordingly:

- D4/D5 may continue to expose `lag_intensity`, `lag_ratio`, `delta_intensity`, `delta_ratio` as descriptive/diagnostic fields under the existing contract;
- this V1 does **not** mark them as independently validated predictive gates;
- no D5 consumer decision logic changes;
- V19 remains frozen;
- no new risk state, threshold or production field is created.

## Closed path / no rescue

This exact lag1-vs-lag2 trajectory specification is closed on reusable Validation. Do not rescue it by testing lag3/lag4, smoothing/decay, alternative normalizers, selected symbols/states/times, different nonlinear transforms, altered ridge/horizons/bootstrap family, or by deleting O.

Any future degree-dynamics study must be a genuinely different causal mechanism hypothesis frozen independently before outcomes, not a parameter search around this negative result.

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
