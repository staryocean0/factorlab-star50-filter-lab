# State-conditioned frequency economics V1 — Phase 1 results

Date: 2026-09-08. Frozen protocol: `PROTOCOL.md`.

## Bottom line

The user's economic premise is **partially supported, strongly at the market-opportunity layer but not yet at the strategy layer**.

When the post-shock state is `Unsafe`, short-horizon realized movement is materially larger than in `Recovering`, so a high-turnover strategy has a much larger gross movement budget with which to pay friction. However, simply increasing frequency with a primitive continuation/reversal rule is not a stable trading solution. The state appears to create **more economic room for short-horizon trading**, not an automatic short-horizon edge.

This distinction is important for the next phase: test a fixed physical-scale family of the existing causal filter/hysteresis strategy rather than conclude `Unsafe = trade faster` from volatility alone.

## Execution

Isolated Actions run `34182726764` completed successfully on `research/state-conditioned-frequency-actions-20260908`, head `0acb7abe5eb3b39ccb726bebd54d6c74f448f881`.

The frozen five engineering tests passed. The run used the fixed frequency menu `1,2,3,5,10,15,30` minutes, both continuation and reversal primitives, both state gates, and all registered one-way friction scenarios `0.5,1,2,3,5 bp`.

The first implementation used a slow episode-by-episode bootstrap. Before reading market outputs, the bootstrap was replaced by a multinomial-count vectorization with the same event-resampling law, same 2,000 draws and same seed family. No state, signal, turnover, cost or market metric changed.

Artifact `10039465116`, digest `sha256:caf94e0218409cb9250d131cbe575ac6379826a46314ce01a6ed0b3ed01bb3f8`. The cloud session independently checked all 13 manifest-listed files for exact byte size and SHA256, with zero mismatches.

2021-2025 is consumed exploratory history. The already-opened 2026-01-05..2026-08-21 snapshot is consistency replay only and was not used to choose frequencies or rules.

## 1. Unsafe creates much more short-horizon movement

The next one-minute absolute movement is larger in Unsafe in essentially every available symbol/year cell.

Examples from the main development years:

| Symbol/year | Recovering mean abs next 1m | Unsafe mean abs next 1m |
|---|---:|---:|
| STAR50 2024 | 6.54 bp | **11.63 bp** |
| STAR50 2025 | 7.09 bp | **11.91 bp** |
| CSI1000 2024 | 5.30 bp | **10.10 bp** |
| CSI1000 2025 | 6.80 bp | **10.25 bp** |
| STAR50 2026 replay | 7.51 bp | **13.71 bp** |
| CSI1000 2026 replay | 6.30 bp | **9.53 bp** |

So the high-risk state is not only “more likely to remain risky”; it is also a state in which one-minute price movement is materially larger.

## 2. Perfect-direction friction capacity supports the user's fee-feasibility premise

The perfect-direction opportunity calculation is **not a tradable strategy**. It asks only how much constant one-way friction a perfectly directed non-overlapping trade could theoretically pay before its gross movement is exhausted.

Pooled 2021-2025:

### STAR50

| Horizon | Recovering break-even friction | Unsafe break-even friction | Unsafe/Recovering |
|---|---:|---:|---:|
| 1m | 3.10 bp | **5.50 bp** | 1.78x |
| 2m | 4.73 | **7.76** | 1.64x |
| 3m | 5.92 | **10.22** | 1.73x |
| 5m | 7.80 | **13.18** | 1.69x |
| 10m | 11.01 | **18.31** | 1.66x |

### CSI1000

| Horizon | Recovering break-even friction | Unsafe break-even friction | Unsafe/Recovering |
|---|---:|---:|---:|
| 1m | 2.71 bp | **4.77 bp** | 1.76x |
| 2m | 4.28 | **7.47** | 1.74x |
| 3m | 5.85 | **9.05** | 1.55x |
| 5m | 7.66 | **12.27** | 1.60x |
| 10m | 11.79 | **17.47** | 1.48x |

This is the cleanest support for the user's prior intuition: the same short frequency that may be uneconomic in a lower-volatility state can have much more room to absorb fees/spread/slippage once the state turns Unsafe.

The per-minute opportunity still falls as the holding horizon grows. For example, STAR50's perfect-direction gross movement per minute is about 11.0 bp/min at 1m in Unsafe versus 6.2 in Recovering; CSI1000 is about 9.5 versus 5.4. Thus Unsafe simultaneously raises total movement and makes the shortest scales economically less absurd.

## 3. But “trade faster” does not itself create edge

The fixed primitive continuation rule does **not** show a robust universal shift to shorter frequencies.

Pooled 2021-2025 one-way break-even friction for continuation:

### STAR50

| Lookback | Recovering | Unsafe |
|---|---:|---:|
| 1m | 0.74 bp | 0.46 bp |
| 2m | 0.92 | 0.71 |
| 3m | 1.18 | 0.53 |
| 5m | 1.37 | -0.06 |
| 10m | 0.78 | 0.97 |
| 15m | 1.18 | 1.28 |
| 30m | 1.59 | 0.28 |

STAR50 therefore gives no evidence that the primitive short-horizon continuation rule suddenly becomes fee-robust in Unsafe. At 2 bp one-way friction, none of the pooled Unsafe continuation horizons is positive.

### CSI1000

| Lookback | Recovering | Unsafe |
|---|---:|---:|
| 1m | 1.36 bp | **1.86 bp** |
| 2m | 1.84 | **1.99** |
| 3m | **2.60** | 1.77 |
| 5m | 2.27 | **3.02** |
| 10m | 1.45 | **2.08** |
| 15m | **3.05** | 1.40 |
| 30m | **1.56** | 1.31 |

CSI1000 has encouraging point estimates at 1/2/5/10m, especially 5m, but the episode-cluster bootstrap intervals for Unsafe-minus-Recovering break-even friction all include zero. Year-by-year results are unstable, and the already-opened 2026 replay is gross-negative for CSI1000 Unsafe continuation at every fixed lookback. Therefore this is not a validated state-routed trading rule.

The reversal primitive is the exact opposite gross signal and likewise does not provide a stable rescue.

## 4. What the result means

The evidence separates two propositions that should not be conflated:

1. **Economic capacity proposition — supported:** Unsafe has much more short-horizon price movement, so higher turnover/frequency has substantially more gross movement available to pay friction.
2. **Trading-edge proposition — not established:** shortening the lookback or increasing turnover does not by itself manufacture a profitable rule. Directional logic still matters.

So `Unsafe` should not mechanically mean “switch to 1-minute trading”. A better architecture is:

`state -> permitted strategy family / scale -> state-specific risk budget`

The state tells us when short scales become economically plausible; a separate fixed strategy family must demonstrate that it can actually harvest that movement after turnover.

## 5. Next phase

Proceed to a preregistered physical-scale family of the repository's existing causal Butterworth + volatility-scaled hysteresis strategy. The next study must:

- preserve one algorithmic family across scales;
- freeze the scale menu and resampling/session semantics before results;
- report the full scale surface, not select the best point;
- compare state-gated Unsafe vs Recovering economics and break-even friction;
- keep 2026 as already-opened replay only;
- remain an index-return research abstraction until a specific tradable carrier and real spread/slippage contract are separately frozen.

This Phase 2 is a mechanism-discrimination test: does a real strategy family exploit the additional Unsafe movement budget, or is the larger movement mostly non-harvestable churn?
