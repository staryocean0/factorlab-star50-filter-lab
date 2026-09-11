# V19 residual failure audit — results

## Decision

**`NO_V20_FROM_V19_RESIDUALS`.**

The validated V19 state machine remains unchanged. The residual audit finds no distinct missing E-15 causal mechanism that justifies a V20 model/state-machine revision.

The remaining errors are overwhelmingly and symmetrically explained by **finite-checkpoint timing around the already-frozen 3σ shock boundary during the final 15 seconds of a 5m bar**:

- false negatives are shocks that are still below 3σ at E-15 and cross above 3σ later;
- false positives are transient E-15 shocks just above 3σ that fall back below 3σ before final close;
- remaining `UNSAFE` versus `RECOVERING` disagreements are rare transition-timing disagreements while the binary risk status is already correct.

Trying to eliminate these residuals would require moving the validated threshold, selecting a later checkpoint, or fitting extra features/persistence on already-consumed data. None is a new causal mechanism, and each would contaminate the clean V19 authority.

## Execution authority

Scientific protocol and taxonomy were frozen before inspection in:

- `research/v19_residual_failure_audit/PROTOCOL.md`.

The first diagnostic run failed for an implementation-only pandas dtype error after all governance, boundary, frozen-identity and contract-test guards had passed:

- failed run: `34613545773`;
- failed job: `103309736742`;
- failure: assigning boolean diagnostic values into a float-typed temporary column;
- no scientific output was produced by the failed run.

A dtype-only wrapper repaired the temporary diagnostic column types without changing the protocol, taxonomy, thresholds, later diagnostic checkpoints, or decision rule.

Successful audit:

- branch: `research/v19-residual-failure-audit-20260911`;
- execution commit: `a066a64ee22cf6e23911f5bccc1a90eafe2de9e4`;
- run: `34614008432`;
- job: `103311278481`;
- artifact: `10270156874`;
- artifact SHA256: `b49c61d8b2345e0441c69fa7d94d25bf9425d572d13953e40e83aede72f4d0fb`;
- artifact size: `50,379` bytes.

Frozen identities remained exact:

- V19 runner blob: `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`;
- V9 runner blob: `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- V18 runner blob: `62c207badff1c3e37cbb1a8e17ef89feeea611d8`;
- V17 runner blob: `397d80037806ba11cadf7f77717d36d55fbafc91`;
- V16 surface blob: `1f88966cf5dd3fb102f0d75746d5d00434555647`.

## Validation residuals — 2024–2025 already-consumed pool

This section is diagnostic only; 2024–2025 is not a fresh holdout for any future model.

### Binary risk false negatives

There are **66** V19 risk false negatives. Every one has the same structural form:

- previous completed state = `NORMAL`: `66 / 66`;
- final state = `UNSAFE`: `66 / 66`;
- final 5m shock = true: `66 / 66`;
- E-15 partial shock = false: `66 / 66`.

So every FN is a final shock that had **not yet crossed the frozen 3σ boundary at E-15**.

Later diagnostic-only frozen V9 checkpoints show:

- becomes risk by E-6: `48`;
- not risk at E-6 but becomes risk by E-3: `16`;
- forms only after E-3 / by close: `2`.

E-15 shock intensity:

- p10 `2.684637`;
- median `2.883948`;
- p90 `2.988088`;
- maximum `2.995024`;
- `62 / 66` lie in the fixed `2.5–3.0` band.

Final shock intensity:

- minimum `3.008403`;
- median `3.115521`;
- p90 `3.487692`;
- `59 / 66` lie in `3.0–3.5`.

This is a textbook late threshold-crossing phenomenon, not evidence of a missing E-15 feature.

### Binary risk false positives

There are **33** V19 risk false positives. Every one has the mirror-image structural form:

- previous completed state = `NORMAL`: `33 / 33`;
- final state = `NORMAL`: `33 / 33`;
- E-15 partial shock = true: `33 / 33`;
- final 5m shock = false: `33 / 33`.

Thus every FP is a **transient E-15 partial shock** that subsequently falls back below the same frozen 3σ threshold.

Later diagnostics:

- resolved by E-6: `27`;
- still risk at E-6 but resolved by E-3: `6`;
- persisted through E-3 and only resolved at close: `0`.

E-15 shock intensity:

- minimum `3.000352`;
- median `3.067496`;
- p90 `3.248110`;
- `32 / 33` lie in `3.0–3.5`.

Final intensity:

- median `2.841366`;
- p90 `2.977505`;
- maximum `2.999623`;
- `30 / 33` lie in `2.5–3.0`.

The FNs and FPs therefore sit on opposite sides of the same immutable threshold and exchange as the bar evolves. Moving the threshold would trade one error class against the other rather than reveal a new state mechanism.

### Exact `UNSAFE` / `RECOVERING` state disagreements

There are **69** Validation rows where both reference and V19 agree that the market is in a risk state but disagree on `UNSAFE` versus `RECOVERING`:

- reference `RECOVERING`, machine `UNSAFE`: `29`;
- reference `UNSAFE`, machine `RECOVERING`: `40`.

They are only `0.00151349` of the 45,590 Validation checkpoints.

Convergence using later diagnostic-only checkpoints:

- converge to reference state by E-6: `46 / 69`;
- converge by E-3: `62 / 69`.

These rows do not represent binary risk misses. They are short transition-timing differences and are too rare to justify a new integrated state-machine version.

## Episode residuals

Validation has 542 reference episodes and 570 V19 machine episodes.

Residual episode failures are directly explained by the row-level timing mechanisms:

- uncaptured reference episodes: **1**, caused by a `risk_fn`;
- fragmented reference episodes: **1**, containing a `risk_fn` on a `SWITCH_ON` transition;
- false machine episodes: **28**;
- every false machine episode lasts exactly **one checkpoint/bar**;
- among the 28 false episodes, `23` resolve by E-6 and `5` by E-3.

There is no persistent false-episode regime hiding in the aggregate metrics.

## Cross-period replication

The same structure is present in Development (2021–2023), before the reusable Validation period:

- 82 FNs: all `NORMAL -> UNSAFE` final shocks, all below 3σ at E-15; `47` become risk by E-6, `29` by E-3, `6` after E-3/at close;
- 30 FPs: all transient E-15 partial shocks from `NORMAL` that finish `NORMAL`; `24` resolve by E-6 and `6` by E-3;
- 58 within-risk `UNSAFE/RECOVERING` timing mismatches; `53 / 58` converge by E-3;
- 6 uncaptured episodes, all explained by FN timing;
- 29 false machine episodes, all one checkpoint long.

The residual mechanism therefore replicates across Development and already-consumed Validation periods rather than appearing as a new Validation-only pathology.

## Mathematical conclusion

V19 has reached the sensible stopping point for this data contract.

A V20 intended to repair these residuals would have to do at least one of the following:

1. move the frozen 3σ shock threshold, exchanging late FNs for transient FPs;
2. choose E-6/E-3 instead of the validated E-15 product checkpoint;
3. fit a new feature, classifier, persistence window, or exception rule using already-consumed 2024–2025 Validation data.

All three are methodologically inferior to preserving the validated V19 object. In addition, the repository has no authorized fresh realtime 3s holdout after 2025 on which a newly fitted V20 could receive clean reusable validation.

Therefore the decisive mathematical state is:

`NO_V20_FROM_V19_RESIDUALS`

V19 remains the current integrated realtime risk-state authority. A future version should be opened only for a **qualitatively new causal question or genuinely new independent realtime data**, not to optimize these boundary residuals.

## Governance

- diagnostic only: true;
- V20 started: false;
- threshold search: false;
- lead-time selection: false;
- persistence-length search: false;
- feature search: false;
- probability fit: false;
- post-hoc subgroup optimization: false;
- 2026 3s queried: false;
- BlackBox queried: false;
- PnL computed: false;
- trading rule created: false;
- `production_authority=false`.
