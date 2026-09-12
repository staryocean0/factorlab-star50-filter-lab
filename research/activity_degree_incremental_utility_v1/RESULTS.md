# Activity-degree incremental utility V1 — results

Date: 2026-09-12  
Formal decision: **`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**

## Question answered

This study tested whether the **current** strictly causal fine-activity surprise coordinate `M3` adds practically material future-risk information after a D4-style current E15 information set is already known, and whether that current refresh also beats an equal-complexity model that receives the **previous** same-half-session M3 instead.

The answer is **no under the frozen joint gate**. This is not the same as saying M3 contains no risk information.

## Frozen comparison

Three ridge information probes were fit on the same M3-admissible low-amplitude surface (`pre5m_range < 30bp`):

- **C**: completed-history controls + previous confirmed risk state / shock-age + current E15 shock intensity `I_t` and volatility ratio `V_t`;
- **A**: C + the fixed current-M3 nonlinear/state-interaction block;
- **N**: C + the exact same-size block using immediately prior same-half-session M3.

An endpoint/horizon could be promoted only if **both `A vs C` and `A vs N`** passed all preregistered practical, uncertainty, support, coverage and 2023-forward gates. The 1% relative loss gate was never relaxed.

Targets were the D4 endpoint family at 15/30/60 minutes: log future RMS and future-tail event. Current bar was excluded; future windows could not cross lunch/overnight. No 2026, BlackBox, PnL, direction or trading field was used.

## Decisive execution

GitHub Actions run `34670357953` completed both phases successfully:

- Development fit/freeze job `103490442493`;
- reusable 2024–2025 Validation job `103490604669`;
- decisive head `5fa76723d5142b96d53822343faad6bd046f9df6`;
- in-run frozen model SHA256 `89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`;
- frozen-model artifact id `10290482080`, ZIP SHA256 `0c71f4d1c9605819ca92d742cbeabf36d1aaa4bbdb6e08e2c29e708796087965`;
- Validation artifact id `10290917834`, ZIP SHA256 `a734a0083c9d197188591fa548668cdbc3f2a86df00b783f68f41acfecf69940`.

The complete Action artifact was subsequently copied byte-for-byte into `evidence/`; its original `SHA256SUMS.txt`, frozen model, block sums, comparison table, descriptive grids and `VALIDATION_RESULTS.json` are retained.

## Main result: future volatility intensity

### A versus C

Current M3 carries additional information relative to the D4-style C information set on this selected surface:

| Horizon | Validation n | Relative squared-loss gain | Main interpretation |
| --- | ---: | ---: | --- |
| 15m | 28,984 | **+2.1750%** | all individual `A vs C` gates pass |
| 30m | 24,134 | **+2.8055%** | positive, but Development n=19,365 < 20,000 |
| 60m | 14,485 | **+3.6193%** | positive, but Development n=11,779 < 20,000 and Validation coverage <95% |

At 15m the adjusted five-day-block interval for absolute squared-loss gain is fully positive (`0.0043589` to `0.0084886`), and 2024/2025 plus STAR50/CSI1000 signs are all positive. Therefore the statement “M3 adds no information beyond I/V” would be wrong.

### A versus equal-complexity lagged-M3 N

The stronger question fails the practical gate:

| Horizon | Relative squared-loss gain | 2023 forward sign | Main failure |
| --- | ---: | --- | --- |
| 15m | **+0.4330%** | negative | below 1%; forward gate fails |
| 30m | **+0.5793%** | negative | below 1%; Development sample gate also fails |
| 60m | **+0.1832%** | positive | below 1%; sample/coverage gates fail; some slice signs and primary interval also fail |

Thus much of the useful fine-activity information is persistent enough that the immediately previous M3 absorbs most of the apparent incremental value. The data do not support promoting the *current M3 refresh* as a practically material new risk coordinate beyond an equal-complexity lagged fine-activity control.

## Tail endpoints

No 15/30/60m tail comparison is promoted. Relative gains remain below the 1% gate, and absolute Brier gains remain below the required `0.0005`; additional forward/sample/interval failures occur in several comparisons. Tail results cannot be rescued by the positive log-RMS findings.

## Coverage and support

Validation strict-cohort coverage after the frozen low-amplitude/future-feasible surface is:

- 15m: `28,984 / 30,222 = 95.9036%` — coverage gate passes;
- 30m: `24,134 / 25,355 = 95.1844%` — coverage gate passes;
- 60m: `14,485 / 15,670 = 92.4378%` — coverage gate fails.

Development final probe counts are 23,233 / 19,365 / 11,779 for 15/30/60m. Therefore the 30m and 60m comparisons fail the frozen Development `n >= 20,000` requirement regardless of positive Validation point estimates.

No missing M3 value was filled, no older row was substituted, and no boundary row was deleted to improve coverage.

## Numerical reproducibility

An earlier successful Development fit on the same code/specification produced a different JSON SHA because linear-algebra floating results were not byte-identical across runs. The dedicated numerical audit compared the two frozen model objects and found exact structural/input identity and only floating last-bit differences:

- max feature-mean difference: `8.8818e-16`;
- max feature-scale difference: `1.1102e-16`;
- max coefficient difference: `8.1619e-15`;
- max 2023 forward-metric difference: `7.4593e-16`;
- coverage difference: `0`.

All audited numeric differences are < `1e-10`. More importantly, the decisive Validation consumed the exact model bytes frozen by the **same** run before Validation, so the freeze-before-Validation chain is intact.

See `NUMERICAL_REPRODUCIBILITY.json`.

## Interpretation

The supported narrow reading is:

> On the inherited low-amplitude surface, current fine-scale activity surprise contains additional short-horizon volatility-intensity information beyond the D4-style I/V baseline, but the incremental value of refreshing M3 *now* rather than using the immediately prior M3 is too small and insufficiently supported to clear the frozen practical promotion gate.

Therefore:

- do **not** add current M3 to the D5 consumer contract;
- do **not** make M3 a new V19 state threshold or state machine input;
- do **not** tune M3 bands, the 30bp surface, ridge penalty, horizon, bootstrap blocks or sample gates to rescue this result;
- do **not** infer first-shock forecasting, direction, PnL or trading utility;
- keep D3, D4, D5 and V19 decisions unchanged.

This study is adaptive reusable Validation because earlier M3 and D4 2024–2025 findings were already known. It is **not fresh OOS**.

`validation_reused=true`; `fresh_oos=false`; `read_2026=false`; `blackbox_queried=false`; `pnl_computed=false`; `candidate_nominated=false`; `v20_started=false`; `d6_started=false`; `production_authority=false`.
