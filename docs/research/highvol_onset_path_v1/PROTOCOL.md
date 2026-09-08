# HighVol onset path-efficiency V1 — frozen protocol

Date: 2026-09-08
Status: development/validation research only; no BlackBox-V1 query; no production authority.

Governance follows repository data-use policy V2:
- Development: 2021-2023;
- Validation: 2024-2026-08-21;
- BlackBox-V1: not queried.

## Question

The continuous HighVol studies found substantial raw movement but minute-by-minute strategies paid too much turnover. Test whether an **eventized, one-trade-per-HighVol-episode** construction can exploit short-horizon continuation or reversal economically.

## Frozen state

Reuse the exact continuous state from `docs/research/continuous_vol_regime_v1/PROTOCOL.md`:

- `fast5 = RMS` of most recent 5 complete 1m returns;
- `background30 = RMS` of preceding non-overlapping 30 complete 1m returns;
- `vol_ratio = fast5 / max(background30, 1bp)`;
- HighVol iff `vol_ratio >= 1.5`;
- NormalVol iff known and `<1.5`;
- Unknown otherwise;
- never bridge gaps, repairs, lunch or overnight.

## Episode onset

A tradable onset occurs at minute close `t` only when:

- state at `t` is `HighVol`;
- state at `t-1` is `NormalVol`;
- all required recent prices/returns are valid;
- there is enough same-half-session future clock time to execute and close the trade.

Transition from `Unknown -> HighVol` is not a tradable onset.

Each HighVol episode can create at most one trade. No re-entry occurs until the state has returned to NormalVol and a new NormalVol->HighVol transition occurs.

## Causal path descriptor at onset

From the same most-recent five 1m returns `r[t-4..t]`:

- `net5 = sum(r)`;
- `tv5 = sum(abs(r))`;
- `eff5 = abs(net5) / tv5` when `tv5 > 0`, else unknown;
- direction sign = `sign(net5)`.

`eff5` is bounded in [0,1] and is known at decision time.

## Frozen strategy menu

Execution: decision at close `t`, enter at the next minute open. Exit after a fixed number of 1m open-to-open intervals. Every trade is confined to one half-session. No overlap; if a position is active, any later onset is ignored.

Hold horizons: `H = 1, 2, 3, 5, 10` minutes.

Momentum family:
- position = `sign(net5)`;
- minimum efficiency gate `eff5 >= E`;
- `E in {0.0, 0.4, 0.6, 0.8}`.

Reversal family:
- position = `-sign(net5)`;
- maximum efficiency gate `eff5 <= E`;
- `E in {1.0, 0.6, 0.4, 0.2}`.

Total menu: 40 identities per symbol.

No other threshold or hold search is allowed in V1.

## Cost model

Each completed trade has exactly one opening leg and one closing leg, so one-way turnover = 2 units.

Report:
- gross bp;
- abstract one-way costs `0.5, 1, 2 bp` per leg;
- net bp/trade;
- net bp/exposure-minute;
- hit rate;
- break-even one-way cost = gross / (2 * trades).

This remains index-research economics, not realized ETF/futures execution.

## Development-only nomination

For each symbol separately, use only 2021-2023.

An identity is eligible iff:

1. at least 10 completed trades in each development year;
2. at least 50 completed trades pooled Development;
3. net after 1bp one-way cost is positive in at least 2 of 3 development years;
4. pooled Development break-even one-way cost >1bp;
5. pooled Development net bp/trade >0.

Among eligible identities, nominate the highest pooled Development **net bp/exposure-minute after 1bp one-way cost**.

Tie-breakers:
1. larger pooled trade count;
2. shorter hold horizon;
3. less restrictive efficiency gate (`0.0` for momentum / `1.0` for reversal closer to unrestricted);
4. momentum before reversal only as a deterministic final tie-break.

If none is eligible, nominate `NONE`.

## Frozen Validation evaluation

Apply the Development nomination unchanged to 2024, 2025 and 2026-through-08-21.

Primary diagnostics:
1. pooled Validation net after 1bp one-way cost >0;
2. at least 2 validation slices have positive net bp/trade after 1bp;
3. pooled Validation break-even one-way cost >1bp;
4. pooled Validation trade count >=30;
5. pooled Validation net bp/exposure-minute >0.

After the primary evaluation is recorded, Validation may be opened for detailed diagnostics. Any new variant discovered there must return to Development under a new protocol.

## Guardrails

- No BlackBox-V1 access.
- No validation-driven changes to this V1 candidate.
- No claim that HighVol itself is predictably known before it is observed.
- No live/production authority.
