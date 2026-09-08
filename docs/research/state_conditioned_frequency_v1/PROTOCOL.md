# State-conditioned frequency economics V1 protocol

Date: 2026-09-08. This study is exploratory on already-consumed 2021-2025 history; 2026 is an already-opened descriptive replay only. It does not change the frozen first-shock or Unsafe/Recovering definitions and does not authorize production trading.

## Question

Test the user hypothesis that when the post-shock state is `Unsafe`, shorter trading/information scales may become economically viable because realized movement rises enough to overcome the higher turnover/friction burden that makes the same short scales unattractive in lower-volatility states.

This is deliberately separated from the unresolved question of whether Unsafe can be warned in advance. Here the observed causal state is taken as given.

## Frozen state input

Use the existing operational first-shock definition and post-shock state machine:

- episode starts at the observed first-shock minute close;
- before five post-shock completed minutes are available, state is Unsafe;
- afterwards `recovery_ratio = RMS(last 5 completed 1m returns) / sigma_pre`;
- Unsafe if ratio >= 1.5, Recovering otherwise;
- same half-session only; missing/quality-ineligible data are Unknown;
- no Clean state.

## Phase 1: strategy-agnostic economic screen

Symbols:
- `000688.SH` STAR50
- `000852.SH` CSI1000

Years:
- 2021-2025: consumed exploratory pool, report each year and pooled;
- 2026-01-05..2026-08-21: already-opened consistency replay only; never use it to choose a frequency or rule.

Fixed information lookbacks in minutes:

`1, 2, 3, 5, 10, 15, 30`

No frequency is added or removed after market results are seen.

For each post-shock episode and each completed decision minute, compute two primitive causal positions for the *next* one-minute return:

- `continuation_h = sign(sum of last h completed 1m log returns)`;
- `reversal_h = -continuation_h`.

A zero/unknown signal is flat. The position is applied only to the next completed valid one-minute return.

Evaluate two state-gated policies separately:

- trade only while current state is Unsafe, flat otherwise;
- trade only while current state is Recovering, flat otherwise.

A change `0 -> +/-1` is one one-way turnover unit; `+1 -> -1` is two; state exit/session end forces flat and charges the corresponding turnover. This produces an executable index-return accounting abstraction, not an ETF/futures fill simulation.

## Friction economics

Primary strategy metric for each symbol/year/state/rule/lookback:

`break_even_one_way_cost_bp = gross_log_pnl_bp / one_way_turnover`

This is the maximum constant one-way friction that would reduce this abstract policy's aggregate log PnL to zero. Negative values mean the primitive rule is gross-negative before costs.

Also report net log PnL under fixed one-way friction scenarios:

`0.5, 1, 2, 3, 5 bp`

These are common stress scenarios, not claims about a specific CSI1000 or STAR50 product's true all-in cost. Existing STAR50 ETF work used a 2bp-per-side explicit fee assumption but also showed that spread and execution matter; therefore no tradability claim may be based on the scenario table alone.

## Opportunity ceiling

For each state and horizon h, also compute a non-tradable perfect-direction upper bound using non-overlapping h-minute forward blocks anchored by event-relative h grids:

- absolute h-minute future log move;
- perfect-direction break-even one-way cost = mean(abs future move) / 2;
- net opportunity per minute after the same friction scenarios.

This upper bound answers whether enough movement exists to pay higher turnover even with perfect directional knowledge. It must never be presented as an achievable strategy return.

## Primary hypothesis

The user's hypothesis is supported at the *market-mechanics* level only if shorter horizons become materially more economically feasible in Unsafe than Recovering. Evidence should include both:

1. a clear Unsafe uplift in the short-horizon opportunity ceiling / friction capacity; and
2. at least one fixed primitive rule (continuation or reversal, reported without selecting after the fact) showing improved short-horizon break-even friction or net economics in Unsafe.

Do not define success as “the best of seven frequencies is profitable”. The full frequency surface must be retained.

## Dependence / uncertainty

Repeated minutes within one first-shock episode are dependent. Aggregate uncertainty by resampling complete first-shock episodes, not individual minutes. For the pooled 2021-2025 comparison, report event-cluster bootstrap intervals for the Unsafe-minus-Recovering break-even friction difference for each fixed rule/lookback when both states have support.

## Phase 2 gate

Only after Phase 1 results are sealed may the existing original 5m causal Butterworth/hysteresis strategy be mapped into a fixed physical-scale family. Phase 2 must preserve one algorithmic family across frequencies and must not choose parameters from Phase 1 outcomes.

Phase 1 does **not** answer whether to switch a production strategy to higher frequency. It only tests whether the economic premise behind that routing idea is plausible.
