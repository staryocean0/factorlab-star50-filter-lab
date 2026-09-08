# State-conditioned physical-scale strategy V2 protocol

Date: 2026-09-08. Frozen after Phase-1 market-opportunity results were sealed and **before Phase-2 strategy-family market outputs are opened**.

Purpose: test whether the extra short-horizon movement budget observed in post-shock `Unsafe` can actually be harvested by the repository's existing causal Butterworth + volatility-scaled hysteresis strategy family, and distinguish a true strategy-clock contraction from merely sampling the same physical strategy more finely.

This remains consumed-history strategy research. It does not authorize live trading, production routing or product-level execution claims.

## Inputs and state

Symbols:
- `000688.SH` STAR50
- `000852.SH` CSI1000

Data:
- native bounded 1m official index bars;
- 2021-2025 = consumed exploratory history;
- 2026-01-05..2026-08-21 = already-opened consistency replay only.

Use the frozen first-shock / post-shock state definition. For operational routing in this study, each half-session has one causal state label per completed minute:

- before the first eligible first-shock in that half-session: `NoEpisode`;
- at a first shock and until five completed post-shock minutes are available: `Unsafe`;
- afterwards `Unsafe` if trailing post-shock 5m RMS / the latest shock's frozen `sigma_pre` >= 1.5, otherwise `Recovering`;
- if another eligible first shock occurs in the same half-session, it **resets** the routing episode to Unsafe and replaces the sigma anchor with that latest shock's `sigma_pre`;
- missing/quality-ineligible inputs => `Unknown`;
- lunch/close terminates the episode and all routed positions are forced flat.

`NoEpisode` is a causal pre-trigger reference state, **not a validated Clean state**.

## Fixed bar-scale menu

Session-aligned bar sizes, all divisors of a 120-minute half-session:

`1, 2, 3, 5, 10, 15 minutes`

Bars are built only from native 1m rows inside the same half-session:
- open = first source open;
- high = max source high;
- low = min source low;
- close = last source close;
- bar is invalid if any required component minute is missing, repaired/flat-filled, quality-ineligible or non-finite;
- no interpolation;
- bar close state = causal state at the final source minute of the bar.

Do not add/remove scales after results.

## Strategy family

Reuse the historical baseline algorithm exactly in structure:

1. first-order causal Butterworth lowpass on log close;
2. volatility threshold = rolling population std (`ddof=0`) of bar-level log-close differences;
3. hysteresis `k=1`;
4. close-t signal; next-bar-open fill; first PnL booking over the following open-to-open interval, matching `execute_next_open`'s two-index shift convention;
5. position set is `{-1,0,+1}`.

No parameter search.

### Family A — scaled strategy clock

For every bar size:
- lowpass period = `12 bars`;
- sigma window = `48 bars`;
- full 48-bar sigma warmup.

Thus the physical strategy clock scales with the bar size. Examples:
- 1m bars -> 12m lowpass / 48m sigma memory;
- 5m bars -> original 60m / 240m;
- 15m bars -> 180m / 720m.

This family directly tests the user's hypothesis that an Unsafe market may require a materially shorter operating frequency.

### Family B — fixed physical clock control

Preserve the original physical durations while changing only sampling resolution:
- lowpass physical period = 60 minutes;
- sigma memory = 240 minutes.

Therefore for bar size `s`:
- lowpass period bars = `60 / s`;
- sigma bars = `240 / s`.

All registered scales divide these durations exactly. At 5m, Family A and Family B are identical (12 / 48), providing an implementation anchor.

If higher sampling alone is enough, Family B may improve at smaller bars. Evidence for a **true faster strategy clock** requires Family A to show an Unsafe-specific advantage beyond Family B at the same small scale.

## Routing/gates

For each strategy family and scale, retain the same base signal path and create four separate causal research policies:

- `Ungated`: strategy allowed throughout every valid half-session;
- `NoEpisode`: signal allowed only when no post-shock episode is active;
- `Unsafe`: signal allowed only when current routing state is Unsafe;
- `Recovering`: signal allowed only when current routing state is Recovering.

Outside the allowed gate, desired signal is flat. Each half-session starts and ends flat. Late signals that cannot complete the registered next-open accounting before the boundary earn no cross-boundary return.

The gate is evaluated at the strategy bar close when the signal is known. Later state changes do not retroactively alter that decision; normal execution latency remains part of the experiment.

## Friction accounting

For each policy:
- one-way turnover = absolute position change; +1 to -1 counts 2;
- forced flat at half-session end is charged;
- primary economic capacity = `gross_log_pnl_bp / one_way_turnover`;
- fixed one-way friction scenarios = `0.5, 1, 2, 3, 5 bp`.

These scenarios are abstract all-in friction stress tests, not a claim about a particular ETF/futures product.

## Primary questions

Report the **full surface**, not a selected optimum.

### Q1 — Does Unsafe favor a shorter strategy clock?

For Family A, compare the scale surface of:
- gross bp per exposure minute;
- break-even one-way friction;
- net bp at each fixed friction;
- turnover and exposure.

Support for frequency contraction requires the small scales (1/2/3m) to improve materially in Unsafe relative to their own `NoEpisode`/Recovering behavior, with reasonable year-to-year consistency. Do not define success by the single best cell.

### Q2 — Is the effect really a faster clock rather than finer sampling?

At each scale compare Family A vs Family B within the same state. A true strategy-clock contraction requires an Unsafe-specific advantage for Family A at short scales that is not reproduced by the fixed-physical control.

### Q3 — Does the original 5m scale remain a useful anchor?

At 5m the two families must be numerically identical before state gating. Any mismatch is an engineering failure and invalidates the run.

## Reporting and uncertainty

Always report:
- STAR50 and CSI1000 separately;
- each calendar year 2021-2025;
- pooled 2021-2025 only as a summary;
- 2026 separately as already-opened replay;
- all six scales and all four gates;
- both families.

The study is too post-hoc for a fresh-OOS profitability claim. Year-direction consistency and 2026 replay are falsification diagnostics, not parameter selectors.

## Interpretation gates

Possible conclusions:

1. **Clock contraction supported:** Unsafe shows a coherent short-scale Family-A improvement, beyond Family B, and it remains economically plausible after nontrivial friction.
2. **Movement only / not harvestable:** Phase 1 movement capacity rises, but neither strategy family can harvest it stably.
3. **Sampling effect only:** smaller bars help Family B similarly; no evidence that the strategy's physical clock itself should shrink.
4. **Index-specific:** STAR50 and CSI1000 differ; routing must not be universalized.

No result may be promoted directly to live trading. A later product-specific phase would need a frozen tradable carrier and real spread/slippage/fee contract.
