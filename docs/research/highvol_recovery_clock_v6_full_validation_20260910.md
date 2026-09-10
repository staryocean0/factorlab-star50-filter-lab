# HighVol recovery clock V6 — full reusable Validation

Date: 2026-09-10

## Decision

**SUPPORTED on the full reusable Validation window through 2026-08-21.**

The frozen risk object is:

`current_state {UNSAFE, RECOVERING} × time since most recent shock -> P(Normal within next 15 minutes)`

No PnL, holding period, position rule, payoff filter, or trading authority is part of this object.

## Authorized 1m -> 5m construction

The user explicitly confirmed on 2026-09-10 that the available 5m data are themselves constructed from 1m data and authorized deterministic 1m->5m construction for the missing 2026 Validation segment.

The construction was not assumed. Before 2026 scoring it was checked against existing 2023 5m data for both indices:

- `000688.SH`: 242 days / 11,616 bars / max absolute close difference = `0.0`;
- `000852.SH`: 242 days / 11,616 bars / max absolute close difference = `0.0`.

2026 source support:

- 154 complete trading days;
- 2026-01-05 through 2026-08-21;
- 36,960 source 1m rows per symbol;
- 7,392 synthesized 5m rows per symbol.

Source blobs were locked to:

- STAR50: `4626fb307bbcae1c417ddcd69ac694cf322c8bbc`;
- CSI1000: `8de5cd3caab99dbacae229a2c87f15c4ff2f8558`.

## Frozen Validation result

Scored rows: **6,334**.

| metric | V6 frozen model | frozen global-rate baseline |
|---|---:|---:|
| Brier | 0.084193 | 0.187392 |
| LogLoss | 0.291098 | 0.562103 |

Annual Brier:

- 2024: `0.085337` vs baseline `0.179974`;
- 2025: `0.077266` vs baseline `0.193192`;
- 2026 through 08-21: `0.093275` vs baseline `0.190877`.

Observed recovery ordering remained correct in all four fixed recent-shock-age buckets for both indices:

`P(Normal next15 | RECOVERING) > P(Normal next15 | UNSAFE)`.

Thus every preregistered Validation condition passed.

## Evidence

- Development run: `34415326314`;
- Development artifact: `10128833197`;
- Development artifact SHA256: `b4d3a1c7dabf9b52c8c13e28355c9fa3fe2e7934768312ab7a13ec8efc326150`;
- full Validation run: `34421316655`;
- full Validation artifact: `10130997291`;
- full Validation artifact SHA256: `62e46478cec42658bb7d756f9537ba817c1465bb8c24a8dd4ff96a89cdffb61c`.

## Interpretation

The most recent shock, not merely the first shock of the episode, is the better causal recovery clock. A recurrent shock resets the recovery process for practical risk-state measurement.

This supports a risk annotation object, not a trading strategy.

`blackbox_queried=false`

`production_authority=false`
