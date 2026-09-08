# Original-5m Unsafe risk/admission routing — frozen protocol

Frozen: 2026-09-08, before Phase-4 market outputs are opened.

Status: consumed-history mechanism study. It does not authorize production/trading and does not create fresh OOS evidence.

## Question

Given the already-frozen post-shock state abstraction, should the original 5-minute Butterworth+hysteresis strategy:

1. run normally through Unsafe;
2. be forced flat while Unsafe;
3. merely stop adding/reversing risk while Unsafe, while allowing an existing same-direction position to continue?

This study deliberately does **not** search another frequency, filter period, sigma window, hysteresis threshold, hold time or Clean rule.

## Symbols

Report separately:

- STAR50 `000688.SH`;
- CSI1000 `000852.SH`.

## Frozen 5m strategy anchor

Use the exact Phase-2 common 5-minute anchor:

- 5-minute session-local bars;
- first-order causal Butterworth, `period_bars=12` (~60 physical minutes);
- rolling 48-bar population sigma (~240 physical minutes), `ddof=0`;
- hysteresis k=1;
- completed-bar decision;
- same two-bar delayed execution convention;
- half-session starts flat and ends flat;
- no lunch/overnight bridge.

`baseline_ungated` must reproduce the accepted Phase-2 5m Ungated annual gross, turnover, exposure and booked-return fingerprints exactly before any routing result is interpreted.

## Frozen state semantics

Use the existing post-shock route state without retuning:

- `NoEpisode`: no qualifying first shock currently active in the half-session;
- `Unsafe`: frozen post-shock Unsafe state;
- `Recovering`: frozen post-shock Recovering state;
- `Unknown`: state cannot be safely determined from required quality-valid inputs.

`Clean` remains disabled.

For **new risk admission**, only `NoEpisode` and `Recovering` are admitted states.

`Unsafe` and `Unknown` are not admitted states. Unknown must never be silently treated as safe.

## Policies

Compare exactly three policies.

### P0 `baseline_ungated`

Use the frozen signal whenever the strategy bar is quality-valid. State does not affect the target.

### P1 `unsafe_hard_off`

At each decision bar:

- target the frozen signal only when state is `NoEpisode` or `Recovering`;
- target flat when state is `Unsafe` or `Unknown`, or strategy input is invalid.

Thus entering Unsafe creates a flatten target, subject to the same two-bar execution latency.

### P2 `unsafe_entry_block`

State controls **admission/reversal**, not automatic exit from an existing same-direction position.

Within each half-session:

- start flat;
- if flat, enter the current nonzero frozen signal only in `NoEpisode` or `Recovering`;
- if already positioned and the frozen signal remains the same direction, retain it through `Unsafe`;
- if the frozen signal flips while state is `Unsafe`, close the current side but do not reverse until an admitted state;
- if state is `Unknown`, target flat regardless of prior position;
- if the strategy input itself is invalid/zero, target flat;
- force flat at half-session end.

No minimum hold, extra hysteresis, delayed release, state dwell rule, or result-driven exception is allowed.

## Costs

This is an index-return abstraction for both indices, not a carrier-specific fill study.

Report symmetric one-way friction stress at:

- 0.5 bp;
- 1.0 bp;
- 2.0 bp.

Do not import the IM asymmetric fee model into STAR50. Real carrier economics are a later mapping step.

## Primary outputs

For each symbol × year × policy and pooled 2021-2025:

- gross bp;
- exposure minutes;
- one-way turnover;
- break-even symmetric one-way cost bp;
- net bp under 0.5/1/2bp one-way friction;
- completed return count and hit rate;
- number of half-sessions with exposure.

Also report policy deltas versus baseline on **affected half-sessions only**, where an Unsafe decision state is observed:

- total/mean gross delta;
- total/mean turnover delta;
- net delta at 0.5/1/2bp;
- worst affected-session gross PnL;
- 5% affected-session gross-PnL quantile;
- paired trading-day bootstrap interval for mean policy-minus-baseline gross and 1bp-net PnL, resampling days, seed `20260908`, 10,000 draws.

The full session-level table must be retained; do not report only favorable years.

## Data roles

- 2021-2025: consumed exploratory history;
- 2026-01-05..2026-08-21: already-opened consistency replay only;
- data after 2026-08-21: untouched for this task and reserved for the next independent snapshot protocol.

## Interpretation policy

No single year or symbol can select another policy after outputs are opened.

Permitted conclusions:

1. Unsafe is useful as a hard-off admission/risk gate for this original strategy family;
2. Unsafe is useful only as an entry/reversal block but not a forced exit;
3. neither overlay is robust enough, so Unsafe should remain a risk-information state rather than directly controlling this strategy.

A routing policy is not promoted merely because pooled PnL rises. Direction should be coherent enough across years, tail behavior should not obviously deteriorate, and cost sensitivity must be shown.

Any future production or carrier mapping requires a separate protocol and actual execution semantics.
