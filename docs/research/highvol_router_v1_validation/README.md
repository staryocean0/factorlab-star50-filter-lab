# HighVol Router V1 — reusable Validation replay

Router V1 was frozen only after the 2021–2023 Development execution audit reproduced the original CSI1000 candidate exactly: 37/31/36 trades, 104 pooled, no overlap rejects, STAR50 route count zero, and no parameter drift.

This stage replays that exact router on reusable Validation (`2024-01-01` through `2026-08-21`). It is not fresh OOS and performs no fitting.

Acceptance is the already frozen CSI1000 candidate gate, plus router mechanics:

- pooled completed trades >= 30;
- pooled mean net after 1bp per leg > 0;
- at least two of 2024 / 2025 / 2026-through-2026-08-21 have positive mean net after 1bp per leg;
- pooled one-way break-even > 1bp;
- STAR50 route count remains zero;
- non-overlap remains intact and concurrency <= 1;
- candidate parameters are unchanged.

Daily volatility, cumulative net drawdown, best/worst day and contribution concentration are diagnostic only. They may determine whether the router is economically attractive enough for later work, but they are not used to change this Validation gate or rescue the candidate.

The 2026 file is fetched from the previously used Validation evidence branch and must match blob `8de5cd3caab99dbacae229a2c87f15c4ff2f8558`. Before strategy execution, the workflow verifies its maximum trading day is no later than `2026-08-21`. BlackBox data are not queried.
