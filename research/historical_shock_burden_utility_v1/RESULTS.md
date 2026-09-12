# Historical shock-burden incremental utility V1 — Results

Date: 2026-09-12  
Decision: **`HISTORICAL_SHOCK_BURDEN_INCREMENTAL_UTILITY_NOT_SUPPORTED`**

This study asked whether a backward-looking 12-valid-completed-bar history of confirmed 3σ shocks adds practical future-risk information after the target index's own D4-style current E-15 intensity / volatility ratio, previous risk state, recent confirmed-shock age and ordinary confirmed-history volatility are already known.

The answer for the frozen V1 specification is **no**. The shock-memory block produces small positive pooled point estimates for future RMS on reusable 2024–2025 Validation, especially at 15 minutes, but every comparison remains far below the preregistered 1% practical relative-loss gate. Tail gains are tiny, and the 30/60-minute Development forward diagnostics are mostly negative. No endpoint × horizon clears the required joint `S vs C` and `S vs H` gates.

## Frozen identities

- protocol Git blob: `3f093d702d069ffd4488fec222dded3f80bcedd1`
- study runner Git blob: `3607f4f56ece54b745741611e8e9d7fe236dc4ec`
- frozen parent cross-index/D4-style runner blob: `b4d3c72e58706b2eb9ae8425f7e7f5439ba002c5`
- original frozen model SHA256: `65f9403e3aae00873432403f833c1d8772429c5172fc7f3fd76581a19a4222d3`
- decisive Actions run: `34679293167`
- fit job: `103514769483`
- Validation job: `103514946904`
- fit artifact: `10293986119`, ZIP SHA256 `153476b787b8ae8401d3029e36303f6ef8af0285a6ba245725e5ae12b5d032cd`
- Validation artifact: `10294046103`, 67,129 bytes, ZIP SHA256 `943d44b741888307c978b4504edeb704ecdeedb75ecdf8f521eec07a4809f215`
- `VALIDATION_RESULTS.json` SHA256: `8fa3f332a033e8f57ebf3240e3891295444dd9b48a8e2f699e2244928eb2f8bd`

The complete decisive Validation artifact has been copied into `evidence/`; the original files are unchanged and `EVIDENCE_SOURCE.json` records their origin.

## Frozen comparison

`C` is the 84-column own-index D4-style causal baseline. `S` adds a 20-column transform/state-interaction block derived from the latest 12 valid completed bars:

- count of confirmed bars with final shock intensity `>=3σ`;
- cumulative excess intensity above `3σ`.

`H` adds the same 20-column schema, same transforms, same scaling and ridge penalty, but summarizes confirmed historical high-volatility burden (`final volatility ratio >=1.5`). Thus `S vs H` asks whether **shock-specific recurrence memory** adds more than a similarly complex generic high-volatility-history representation.

Feature identity passed before outcomes:

- C: 84 columns;
- S: 104 columns;
- H: 104 columns;
- S/H schema identical: true.

Current bar final price / return / shock label never enters its own memory feature. Five causal/complexity tests passed before Development fit and again before Validation.

## Formal Validation results

Relative squared-loss reductions of S are:

| Horizon | Endpoint | S vs C | S vs H | Joint supported |
|---|---|---:|---:|---|
| 15m | log future RMS | **+0.16994%** | **+0.16951%** | No |
| 15m | future tail | +0.03773% | +0.02048% | No |
| 30m | log future RMS | +0.18307% | +0.19834% | No |
| 30m | future tail | +0.03925% | +0.03670% | No |
| 60m | log future RMS | +0.24096% | +0.34717% | No |
| 60m | future tail | +0.03330% | +0.04419% | No |

Every one of the twelve comparisons fails the frozen 1% relative practical gate.

Tail absolute Brier gains are only about `0.000006`–`0.000037`, all well below the frozen `0.0005` gate.

### The strongest-looking result is still not promotable

15m log future RMS `S vs C`:

- n = 39,770;
- relative gain = +0.16994%;
- absolute squared-loss gain = `0.00051527`;
- adjusted 5-day interval = `[0.00001510, 0.00114867]` — positive;
- both symbols and both Validation years have nonnegative signs;
- 2023 forward gain is positive.

So it is reasonable to say that the frozen shock-memory summary carries **some statistical information** at 15 minutes relative to C.

But promotion requires practical magnitude and the complexity-matched mechanism comparison. `S vs H` at the same endpoint is also only +0.16951%, below 1%, and its adjusted 5-day interval is `[-0.00003330, 0.00114301]`, crossing zero. Therefore this does not establish a stable, practically material shock-specific memory effect.

At 30/60 minutes the pooled RMS point estimates remain small; primary intervals cross zero, and the `S vs C` 2023 forward gains are negative. 60m `S vs H` is +0.34717% in reusable Validation but its 2023 forward gain is negative and its adjusted interval crosses zero.

## Tail endpoints are clearly unsupported

All 15/30/60m tail comparisons are <0.05% relative improvement and fail the `0.0005` absolute Brier gate. Most also fail adjusted-interval, cross-slice sign and 2023-forward gates. There is no basis to add this memory to the validated tail-risk interface.

## Coverage and sparsity

Memory coverage is 100% among otherwise baseline-available + future-feasible rows for every horizon in both Development and Validation:

- 15m Validation n = 39,770;
- 30m n = 33,950;
- 60m n = 22,310.

On the 15m Validation cohort, the 12-bar shock count is sparse:

- zero prior confirmed shocks: 33,316 rows;
- exactly one: 5,464;
- two or more: 990.

Mean shock count is about 0.191 and p95 is 1. This sparsity is descriptive only; it is **not** permission to post-hoc filter to multi-shock rows.

## Development-forward discipline

The model was frozen on 2021–2023 before Validation. 2023 forward diagnostics were not uniformly favorable:

- 15m RMS: small positive S vs C/H;
- 15m tail: negative vs both;
- 30m RMS: negative vs C, small positive vs H;
- 30m tail: negative vs both;
- 60m RMS and tail: negative vs both.

These signs are part of the preregistered gates and reinforce the negative promotion decision. They were not used to alter the specification.

## Scientific interpretation

The study does **not** show that shock history is meaningless. It shows something narrower:

> Once current own-index I/V, previous state, recent-shock age and ordinary rolling volatility are known, this fixed 12-completed-bar count/excess representation of 3σ shock burden does not provide enough stable practical incremental value to justify a new research coordinate.

This is compatible with V5's established finding that a recurrent shock resets the recovery clock. V5's “time since most recent shock” role remains embedded in the existing state/recovery ancestry; this V1 tested a different question — whether **additional cumulative burden beyond that timing/current-degree information** deserves promotion — and it did not.

## Closed path / no rescue

This V1 specification is closed. Do not use these reusable Validation results to tune:

- 12 bars into 6/24 or another memory length;
- decayed weights;
- 3σ or 1.5 thresholds;
- one symbol only;
- selected state/time/episode subsets;
- endpoints/horizons/ridge/bootstrap family;
- removal of the equal-complexity H control.

Any future memory research would need a genuinely different causal mechanism hypothesis frozen independently, not a rescue of this result.

No D5 field is added. V19 remains frozen. D3/D4/M3/cross-index decisions remain unchanged. `validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `production_authority=false`; `v20_started=false`; `d6_started=false`.
