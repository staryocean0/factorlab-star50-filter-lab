# Signed-risk asymmetry incremental utility V1 — Results

Date: 2026-09-12  
Decision: **`SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED`**

This study tested whether the sign structure of the previous 12 valid completed 5-minute returns adds practical causal information about future non-PnL risk after the established own-index current E-15 intensity / volatility-ratio baseline and absolute-magnitude history are known.

The fixed V1 result is **not supported for promotion**. The signed block contains a real pooled hint, strongest at 60-minute future RMS: it clears the frozen 1% relative-improvement threshold against both the established C baseline and an equal-complexity magnitude-only M control. However, both family-adjusted 5-trading-day intervals cross zero, and the symbol slices have opposite signs: STAR50 (`000688.SH`) is negative while CSI1000 (`000852.SH`) is strongly positive. The preregistered cross-slice gate therefore rejects the result.

This is a heterogeneous statistical hint, not a robust cross-index risk mechanism. The protocol expressly forbids rescuing V1 by selecting only CSI1000 or by retuning the sign representation after Validation.

## Frozen identities

- source main at freeze: `291d04861e85492337a2f86f1fade0419254972d`
- protocol Git blob: `8e5690d4fa1250fcc2e3b5cc3bfdea733dd46880`
- study runner Git blob: `52fe22bef0b1e34364d908fc306fd076c8a20264`
- frozen parent degree-trajectory / D4-style runner blob: `0afc45e5061f45f544ecc7ee4519eae4e5204bca`
- frozen model SHA256: `92a5fdd5a75a57a1ca3adb567e8a12d03309c7de4ef33a601fc67cbb8c38f4d2`
- decisive Actions run: `34681733485`
- fit job: `103521475450`
- Validation job: `103521623283`
- fit artifact: `10294178564`, 26,054 bytes, ZIP SHA256 `f7704e9e77163a6c7f977fb8d9007543d03b579aebf80ef5f403fb830a63a369`
- Validation artifact: `10293179281`, 67,661 bytes, ZIP SHA256 `f9597bb93b91a481b6a07a225dfae22c90c2f9178216079f41e6053f3076af79`
- `VALIDATION_RESULTS.json` SHA256: `c0ffac04a70fed796bfb766876bd51f1781c788e4648b202eefd3b9ef01b203b`

The complete decisive Validation artifact is persisted byte-for-byte under `evidence/`; `EVIDENCE_SOURCE.json` records the source identities.

## Frozen information blocks

The previous 12 **valid completed** 5-minute returns are used; the current unfinished bar is excluded by construction.

Signed coordinates:

- `SEI12 = sum(r * abs(r)) / sum(r^2)` — signed squared-return energy imbalance;
- `SAI12 = sum(r) / sum(abs(r))` — signed absolute-return imbalance.

Equal-complexity magnitude-only controls on the same 12 bars:

- `L1L2_12 = sum(abs(r)) / (sqrt(12) * sqrt(sum(r^2)))`;
- `MAXL2_12 = max(abs(r)) / sqrt(sum(r^2))`.

Models:

- **C**: 84-column inherited own-index D4-style baseline;
- **A**: C + 20-column signed-asymmetry nonlinear/state-interaction block;
- **M**: C + 20-column magnitude-only nonlinear/state-interaction control.

A and M are both 104 columns with the same block size, transformations, state interactions, ridge lambda and fitting rows. Six causal/complexity invariants passed before fit and again before Validation.

## Population / availability

Coverage among otherwise baseline + future-feasible rows is 100% in Development and Validation:

- 15m: Development 59,614; Validation 39,770;
- 30m: Development 50,890; Validation 33,950;
- 60m: Development 33,442; Validation 22,310.

No 2026 protected detail was checked out. BlackBox-V1 was not queried.

## Formal Validation results

Relative squared-loss improvements of A are:

| Horizon | Endpoint | A vs C | A vs M | Joint supported |
|---|---|---:|---:|---|
| 15m | log future RMS | +0.35160% | +0.19345% | No |
| 15m | future tail | +0.19928% | +0.11586% | No |
| 30m | log future RMS | +0.89813% | +0.70577% | No |
| 30m | future tail | +0.30819% | +0.23314% | No |
| 60m | log future RMS | **+1.35593%** | **+1.02822%** | **No** |
| 60m | future tail | +0.54520% | +0.43298% | No |

All six endpoint × horizon joint promotions are false. None of the twelve formal comparisons is supported.

## Why the strongest 60m RMS hint is rejected

### A vs C

- n = 22,310;
- relative improvement = **+1.35593%**;
- absolute squared-loss gain = `0.0016150634791540668`;
- adjusted 5-day interval = `[-0.0016721298128465787, 0.005202802628438307]` — crosses zero;
- STAR50 `000688.SH`: absolute gain `-0.0014313887449799766`, relative `-1.18485%`;
- CSI1000 `000852.SH`: absolute gain `+0.00466151570328811`, relative `+3.97011%`;
- 2024 and 2025 annual pooled gains are both positive;
- 2023 Development-forward gain is positive.

### A vs M

- n = 22,310;
- relative improvement = **+1.02822%**;
- absolute gain = `0.0012206750419079722`;
- adjusted 5-day interval = `[-0.0019976749339485705, 0.0046879801939438675]` — crosses zero;
- STAR50 `000688.SH`: absolute gain `-0.0019827228783220884`, relative `-1.64874%`;
- CSI1000 `000852.SH`: absolute gain `+0.004424072962138033`, relative `+3.77552%`;
- both Validation years are positive;
- 2023 Development-forward gain is positive.

Thus the pooled 1% practical threshold is **not sufficient**. The frozen protocol also requires a positive multiplicity-adjusted interval and nonnegative gains in every annual and symbol slice. Both 60m RMS comparisons fail those robustness gates.

The scientific reading is therefore:

> Recent return-sign asymmetry appears to carry a materially sized 60m RMS signal in CSI1000, but the same fixed representation is harmful in STAR50. The pooled effect is not stable enough to establish a shared bottom-layer risk attribute for the two-index research object.

This does **not** authorize a CSI1000-only rescue. Selecting the favorable index after seeing Validation would violate the frozen V1 protocol.

## Other horizons and tail endpoints

15m effects are small. 30m RMS is directionally stronger, but remains below 1% and already shows the same STAR50-negative / CSI1000-positive split.

Tail endpoints do not pass practical gates:

- 15m: +0.19928% / +0.11586%;
- 30m: +0.30819% / +0.23314%;
- 60m: +0.54520% / +0.43298%.

The strongest tail absolute Brier gain is `0.0004583935491319103`, below the frozen `0.0005` gate, and its adjusted interval also crosses zero.

## Development-forward discipline

The final 2021–2023 model bytes were frozen before reusable Validation was scored. The pre-Validation 2023 forward diagnostic had stronger signals at 30m/60m, including >1% 30m/60m RMS and >1% 60m tail relative gains. Those diagnostics were recorded before Validation and were not used to change the 12-bar window, sign definitions, comparator, ridge lambda, horizons or gates.

Validation therefore legitimately falsified the stronger Development interpretation rather than triggering a retune.

## Scientific and consumer interpretation

The correct conclusion is not “return sign has no information.” It is narrower:

> This fixed 12-completed-bar signed-asymmetry representation does not demonstrate a robust, cross-index, independently promotable future-risk increment beyond the current-I/V baseline and an equal-complexity magnitude-history control.

Accordingly:

- V19 remains frozen;
- the D4 decision remains unchanged;
- the D5 consumer contract remains unchanged;
- no signed-asymmetry field is added to D5;
- no new state, threshold, warning, direction signal or production field is created;
- no PnL/trading interpretation is authorized.

## Closed path / no rescue

This fixed V1 signed-asymmetry specification is closed on reusable Validation. Do not rescue it by:

- selecting only `000852.SH`;
- changing to 6/24/48-bar windows;
- introducing exponential decay;
- replacing the frozen coordinates with skewness or downside-count variants;
- state/time/symbol filtering after outcomes;
- lowering the 1% / 0.0005 gates;
- changing ridge lambda, horizons, bootstrap family or comparator M.

A future study must pose a genuinely distinct causal mechanism and freeze it before outcomes; it may not be a parameter search around this result.

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
