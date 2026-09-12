# Risk-coordinate Validation v1 — formal closeout

## Decision

**RISK_COORDINATE_VALIDATION_NOT_FULLY_REPLICATED_NO_THRESHOLD_RETUNE**

The already-frozen reusable Validation diagnostic does **not** satisfy its preregistered full-replication rule across both indices and both 2024/2025 years. This result is not rescued by pooling years, lowering cell-count gates, moving M3 bands, changing the 1.5 current-volatility-ratio threshold, or changing the 30bp support condition.

The evidence is more specific than a generic failure:

- the state-persistence axis passed in all four index×year pools;
- the M3 amplitude effect-size criterion (`M3>2` / `M3<=0` median future-15m RMS ratio >= 1.10) passed in every state/index/year comparison;
- full amplitude-axis promotion nevertheless failed in three Unsafe slices because the **frozen minimum support gate** was not met.

Therefore the two-coordinate decomposition remains descriptively useful, but the M3 amplitude axis is **not promoted as a fully replicated validated coordinate** under the frozen protocol.

## Execution history recovered

This study was not actually unexecuted. Repository history showed a successful original Action that had never been written back into the authority tree:

- original frozen run: `34303912251`
- original job: `102316502560`
- original execution SHA: `ac17e766e5d17b7d37cd90e83253c4874c33f44e`
- original artifact id: `10086030669`
- original artifact bytes: `3158`
- original artifact ZIP SHA256: `bf92728fed46f4db34ea45e5ce932c2d8f7557d48e7a5fa5290a1be43a5d36ed`

To close the missing authority/evidence link, the exact frozen scientific blobs were restored and rerun without modification:

- reproduction run: `34667783528`
- reproduction job: `103483115374`
- reproduction execution SHA: `08e70cbfa6b097435afabb9f228a71a771d50797`
- reproduction artifact id: `10289539266`
- reproduction artifact bytes: `3472`
- reproduction artifact ZIP SHA256: `a374ed5daa4f34b5d2f4720d67dc668872b2412ff921bd1822b4a7fe038fb4b8`

The reproduced output matches the original run on the scientific result, 110,911-row population, all cell counts/metrics, and all pass/fail checks.

## Frozen protocol identity

No scientific setting was changed for the reproduction:

- `FROZEN_PROTOCOL.md` Git blob: `18e330b3ea9067a27ba2ec5351f5f8136b5fcc89`
- `run_validation.py` Git blob: `669930a56f80249b63d55973219185eb83f55f42`
- parent fine-activity runner blob: `2a5f607db1451a2e4576a9bc0940b67ac02f0d2e`
- parent fine-activity protocol blob: `d43f5b4a2c0395d1d022a3fb5e10c58dce08de0c`
- decomposition protocol blob: `9672291188dc92ade1046de603d7b178fba783c8`
- decomposition result blob: `832f632b882dcdd0fc51aa3ff83c9b814940e5cd`

## Population and governance

- reusable Validation years: 2024, 2025
- Validation rows: **110,911**
- 2026 read: false
- BlackBox queried: false
- fresh OOS: false
- returns/PnL evaluated: false
- candidate nominated: false
- production authority: false

The run uses 2022–2023 only for the protocol-defined causal warmup/reference construction and evaluates the frozen diagnostic on 2024–2025.

## Frozen pass/fail checks

### 000688.SH — 2024

Full pass.

- NonUnsafe M3 `<=0`: n=12,848, median future RMS15=5.111674bp
- NonUnsafe M3 `>2`: n=524, median=10.086794bp; top/bottom ratio ≈ **1.9733**
- Unsafe M3 `<=0`: n=190, median=3.936734bp
- Unsafe M3 `>2`: n=46, median=7.463317bp; ratio ≈ **1.8958**
- state-persistence gap: Unsafe minus NonUnsafe future-Unsafe probability = **+50.4886pp**

All support and effect gates passed.

### 000688.SH — 2025

State-persistence axis passed; full amplitude axis failed only on top-cell support.

- NonUnsafe `<=0`: n=14,098, median=4.207095bp
- NonUnsafe `>2`: n=192, median=9.659727bp; ratio ≈ **2.2961**
- Unsafe `<=0`: n=377, median=3.310256bp
- Unsafe `>2`: **n=19 < frozen n>=30 gate**, median=8.773213bp; effect ratio ≈ **2.6503**
- state-persistence gap: **+51.6869pp**

The effect-size gate passed; the support gate did not.

### 000852.SH — 2024

State-persistence axis passed; full amplitude axis failed only on bottom-cell support.

- NonUnsafe `<=0`: n=7,476, median=4.281605bp
- NonUnsafe `>2`: n=709, median=8.592016bp; ratio ≈ **2.0067**
- Unsafe `<=0`: **n=48 < frozen n>=100 gate**, median=3.395545bp
- Unsafe `>2`: n=150, median=6.201491bp; effect ratio ≈ **1.8264**
- state-persistence gap: **+47.8773pp**

The effect-size gate passed; the support gate did not.

### 000852.SH — 2025

State-persistence axis passed; full amplitude axis failed only on top-cell support.

- NonUnsafe `<=0`: n=16,852, median=3.463698bp
- NonUnsafe `>2`: n=74, median=9.376840bp; ratio ≈ **2.7072**
- Unsafe `<=0`: n=390, median=2.746829bp
- Unsafe `>2`: **n=20 < frozen n>=30 gate**, median=7.152262bp; effect ratio ≈ **2.6038**
- state-persistence gap: **+48.7915pp**

The effect-size gate passed; the support gate did not.

## Reproduction evidence hashes

The reproduction Action emitted:

- `validation_risk_coordinate_cube.csv`: `192e011c7aa873b451a0363bb6392296b6a88f9f637f256dfbc9842b740aeb3b`
- `validation_pooled_state_summary.csv`: `cfcb671deb2ab978c46f034e91e19e347af9fa0c81903f7588d1f99b286dff63`
- `summary.json`: `d6c306c6a06dba470f218bb1c19156c4b503abd398d706620775359dd9774ad8`

## Interpretation

The robust part of the prior decomposition is the **state-persistence coordinate**: across both indices and both years, current Unsafe status separates future-Unsafe probability by roughly +48 to +52 percentage points.

M3 also continues to rank future movement amplitude strongly in every frozen extreme-band comparison, including the three under-supported Unsafe extremes. However, the protocol explicitly required minimum support in every cell. Three such cells do not meet that requirement, so the correct formal verdict remains failure of full replication.

This is not evidence to retune M3. The post-result path is closed to threshold/sample-gate rescue. Any future fine-activity study would need a scientifically distinct, separately preregistered question; it cannot relabel this failed full-replication test as a pass.

## Final state

`validation_diagnostic_does_not_fully_replicate`

`state_persistence_axis_replicated=true`

`m3_effect_size_gate_passed_all_extreme_comparisons=true`

`m3_full_amplitude_axis_replicated=false`

`post_result_threshold_retune_allowed=false`

`candidate_nominated=false`

`blackbox_queried=false`

`production_authority=false`
