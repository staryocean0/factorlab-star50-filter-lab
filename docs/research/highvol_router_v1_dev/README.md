# HighVol Router V1 — Development execution audit

## Fixed direction

This stage does not search for a new strategy.

- `000852.SH`: the already frozen **CSI1000 long slow-aligned HighVol acceleration V1** is the only active directional route.
- `000688.SH`: `NO_TRADE` for the directional HighVol module.
- every other HighVol context: `NO_TRADE`.
- `production_authority=false`.

The CSI1000 rule is copied from the frozen Development receipt, not re-fit here: `NormalVol->HighVol`, recent5 positive, preceding non-overlapping slow30 positive, `tail2_share>=0.60`, `tail1_share<0.60`, next-open long, fixed 3m hold, same half-session, complete path, non-overlap, 1bp/leg primary friction. The original continuous-state implementation includes a 1bp floor in the background RMS denominator; Router V1 preserves that implementation detail for exact reproduction.

## Development-only question

Using only 2021–2023 (plus 2020 warm-up), does the complete router reproduce the frozen CSI1000 receipt and remain mechanically coherent at portfolio level?

The audit reports:

- raw positive HighVol onsets, frozen qualifying events, accepted non-overlap trades and overlap rejects;
- annual and pooled gross/net economics and one-way break-even;
- active days, maximum trades/day, daily volatility proxy and cumulative-log-bp drawdown;
- positive-day concentration, top-five contribution, and absolute daily-PnL HHI;
- maximum concurrent positions;
- explicit STAR50 trade count, which must be zero.

No tail threshold, hold, cost, stop, confirmation, exit, or state threshold can be changed in this stage.

## Pass semantics

Development audit passes only when the historical frozen receipt reproduces within 0.01bp mean-gross tolerance, annual trade counts remain exactly 37/31/36 (104 pooled), all three annual 1bp/leg net means remain positive, pooled one-way break-even remains above 1bp, non-overlap is intact, maximum concurrency is at most one, and STAR50 produces zero trades.

A pass means **eligible to freeze the Router V1 identity and replay it in reusable Validation**. It does not grant production authority and does not authorize BlackBox access.
