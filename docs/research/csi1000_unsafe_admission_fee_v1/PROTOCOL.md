# CSI1000 Unsafe admission-gate fee study — frozen protocol

Frozen: 2026-09-08, before this Phase-3 market output is opened.

Status: post-selection exploratory follow-up to the registered Phase-2 full frequency surface. This study cannot convert the Phase-2 3-minute candidate into fresh OOS evidence. It does not authorize trading or production.

## Frozen candidate

Do not search frequency or signal parameters in this study.

- symbol: `000852.SH` CSI1000 only;
- state: the already-frozen post-shock `Unsafe` state;
- sampling / decision cadence: 3 minutes;
- signal family: Phase-2 `fixed_physical` only;
- causal first-order Butterworth physical cutoff: approximately 60 minutes (`period_bars=20` on 3m bars);
- volatility / hysteresis memory: approximately 240 minutes (`rolling std window=80` 3m bars, ddof=0);
- hysteresis k=1;
- decision at completed bar close;
- same two-bar delayed execution convention as Phase 2;
- every half-session starts and ends flat;
- no lunch or overnight position bridge.

The Phase-2 3m candidate was selected after inspecting the complete frozen Phase-2 surface. Therefore all 2021-2025 evidence here is consumed exploratory history and the already-opened 2026-01-05..2026-08-21 pack is consistency replay only.

## Policies

Compare exactly two policies.

### P0 `hard_gate`

Phase-2 baseline. At each decision bar:

- target the frozen signal only if the current state is `Unsafe` and the bar is quality-valid;
- otherwise target flat.

Thus `Unsafe -> Recovering` itself generates a flatten target, subject to the same two-bar execution latency.

### P1 `admission_gate`

`Unsafe` controls entry and re-entry, not continued holding.

Decision-target recursion within each half-session:

- start flat;
- if flat, open the current nonzero signal only when the current state is `Unsafe`;
- if already long/short and the frozen signal remains the same direction, retain the position even if state becomes Recovering;
- if the frozen signal flips:
  - close the current direction;
  - open the opposite direction only if the current state is `Unsafe`;
  - otherwise remain flat;
- if the frozen signal is unavailable/zero because the strategy input is invalid, target flat;
- half-session end is forced flat.

No minimum holding period, extra hysteresis, dwell-time rule, recovery threshold or result-driven exception is allowed.

## Execution and fee floor

The price PnL remains the same index-open log-return research abstraction as Phase 2. This is **not** a futures fill simulation.

Apply a current-fee stress model using the China Financial Futures Exchange fee table available at protocol freeze:

`https://www.cffex.com.cn/cn/zjssf/20240701/39212.html`

The table is labelled updated July 2024 and states equity-index futures transaction fees of:

- ordinary/open transaction: 0.23 bp of transaction notional;
- same-day close transaction: 2.30 bp of transaction notional.

Apply these rates uniformly as a current economic fee-floor stress model to all historical years. Do **not** claim these were the actual historical fees in every year.

Because this research account is intraday and flat by half-session end:

- `0 -> +/-1`: one open leg, 0.23 bp;
- `+/-1 -> 0`: one same-day close leg, 2.30 bp;
- `+1 -> -1` or `-1 -> +1`: one same-day close plus one new open, 2.53 bp total exchange fee;
- forced half-session flatten: same-day close fee.

On top of the exchange fee floor, report fixed extra-friction sensitivities per execution leg:

- 0.00 bp;
- 0.25 bp;
- 0.50 bp.

The extra friction represents an abstract allowance for broker surcharge / spread / slippage / queue effects. It is not calibrated from market quotes.

## Primary outputs

For each policy and calendar year, and pooled 2021-2025:

- gross index PnL bp;
- exposure minutes;
- gross bp / exposure minute;
- open legs;
- same-day close legs;
- reversal decisions/executions;
- exchange fee floor bp;
- net bp after exchange fee floor;
- net bp / exposure minute after exchange fee floor;
- net results under +0.25 and +0.50 bp extra friction per execution leg;
- remaining break-even extra friction per execution leg after exchange fees:
  `(gross_bp - exchange_fee_bp) / total_execution_legs`;
- symmetric gross break-even one-way turnover cost, for exact comparability with Phase 2.

Also retain half-session-level aggregates so concentration can be inspected without inventing new filters.

## Required anchors

Before interpreting P1, verify P0 `hard_gate` reproduces the accepted Phase-2 CSI1000 fixed-physical 3m gross path/turnover within numerical tolerance for every year available in both outputs.

The engineering test suite must separately verify:

- two-bar delayed execution;
- asymmetric open vs same-day-close fee accounting;
- reversal fee = close + open;
- forced half-session close fee;
- admission gate does not exit merely because state becomes Recovering;
- admission gate closes on signal flip outside Unsafe but does not reverse until Unsafe;
- no cross-lunch return is booked.

## Interpretation policy

Do not choose another frequency or modify the candidate after seeing Phase-3 results.

Possible conclusions are limited to:

1. `admission_gate` materially reduces fee burden while retaining enough gross edge to remain positive under the fee-floor stress;
2. turnover reduction helps but leaves insufficient friction headroom;
3. the Phase-2 candidate is economically fragile even before real spread/slippage, so the route should be stopped pending materially different execution information.

A positive result remains exploratory because the routing policy is evaluated on consumed history after candidate selection. The next independent same-semantics data after 2026-08-21 must be used without retuning.

Real economic promotion requires actual IM futures point-in-time contract selection and bid/ask/trade execution data plus effective-dated fees.
