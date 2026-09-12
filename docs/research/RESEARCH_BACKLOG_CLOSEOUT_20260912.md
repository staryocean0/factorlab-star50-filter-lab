# Research backlog closeout — 2026-09-12

## Decision

The 12 branches flagged by the 112-branch research-backlog audit are now **closed as current executable backlog**.

This does **not** mean all twelve studies were scientific successes. It means each ambiguous branch now has an authoritative disposition supported by its original Action evidence or by a strict historical identity audit. Historical branches are preserved unchanged.

Machine authority: `RESEARCH_BACKLOG_CLOSEOUT_20260912.json`.

Current scientific breakpoint remains **`CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED`**. This closeout creates no new candidate and changes no V19/D3/D4/D5 decision.

## Why the heuristic audit found 12 “unfinished” branches

The branch scanner intentionally used simple signals: frozen-protocol markers, runner/workflow markers, result-file markers and successful Action runs. That is useful for recall but cannot distinguish:

- an experiment that ran successfully but left its result only in an Action artifact;
- a Development predecessor whose successor Validation already exists;
- a duplicate protocol frozen after the same question had already been executed elsewhere;
- a coordinator/takeover branch rather than a standalone experiment;
- a frozen experiment that correctly failed closed before scientific replay;
- a historical trading/router experiment that is no longer within this repository's current scope.

The closeout ledger resolves those semantic cases instead of blindly rerunning everything.

## Disposition summary

| Historical branch | Current disposition | Why no rerun |
| --- | --- | --- |
| `first-shock-actions-20260907` | completed Development, no general promotion, superseded | minute-level first-shock evidence was weak/unstable; later seconds/support/state chain is authoritative |
| `highvol-realtime-detection-v7-20260910` | Development not Validation-eligible | 60s UNSAFE recall 77.21% failed frozen 90% gate; V8+ superseded it |
| `highvol-realtime-detection-v8-3s-20260910` | Development eligible, successor Validation exists | V8 2024–25 subset Validation passed; V9/V17/V19 later became the active chain |
| `highvol-realtime-risk-object-v9-20260910` | Development eligible, superseded | V9/V17/V19 successors preserve the relevant realtime state/probability mechanism |
| `highvol-realtime-probability-lead-v10-20260910` | Development eligible, successor Validation exists | 15s lead moved directly into a dedicated Validation branch and later V17/V19 work |
| `highvol-realtime-probability-lead-v10-validation-20260910` | 2024–25 subset passed; full originally planned 2026-inclusive Validation not executed | 2026 3s was not queried; later V17 validated the available E15 transfer and V19 is current authority |
| `rmr-activity-pressure-reversal-v1-20260909` | broad signal source not established | 5,851 Development events still failed high-activity support/stability/severity gates; reversal mining is outside current scope |
| `rmr-lunch-boundary-normalization-v1-20260909` | broad signal source not established | extremely sparse material-day support and failed annual/directional gates; reversal mining is outside current scope |
| `session-aware-information-set-bounds-v0617-20260907` | permanently blocked under frozen protocol | required pre-v0.6.17 source and leg-universe identities never existed in recoverable Git history; backfilling hashes would violate preregistration |
| `highvol-recovery-survival-v11-20260911` | duplicate frozen design superseded | completed V11 on 2026-09-10 already failed Validation eligibility; V12 tested and rejected simple shock-expiry explanation |
| `risk-gate-takeover-20260907` | coordination/handoff branch superseded | later V16–V19 and D2–D5 authority chain executed the actual risk-state program |
| `highvol-router-v1-dev-20260909` | historical router audit retired/out of current scope | it contains long route, hold, costs, PnL, Sharpe and drawdown economics; those are explicitly outside current risk-attribute scope |

## Important recovered historical facts

### V7 → V10 realtime ancestry

The apparent missing result markers do not imply an interrupted scientific chain.

- V7 run `34425687318`: 60-second primary detector failed the frozen pooled recall gate (`0.7721 < 0.90`).
- V8 Development run `34426934097`: 3-second detector became Validation-eligible (pooled UNSAFE precision `0.99969`, recall `0.99783`). Its successor Validation run `34438385207` passed the available 2024–25 subset and froze V8 as a validated component without claiming full 2024–26 Validation.
- V9 Development run `34443013548`: unified realtime state/probability object was Validation-eligible, with probability MAE about `6.34e-06` on Development.
- V10 Development run `34445913929`: E-15 probability lead was Validation-eligible; successor Validation run `34446224846` passed the available 2024–25 subset with pooled coverage `0.99465`, probability MAE `0.000807`, and no 2026 query.

These are historical ancestry facts. Current authority remains V17/V19, not the old Development branches.

### v0.6.17 is not a “missing run to finish”

Strict audit run `34670259559` searched all recoverable Git history strictly before the first v0.6.17 implementation commit:

- 70 commits;
- 4,412 text blobs;
- 0 qualifying 349,923-row authoritative-source identity receipts;
- 0 qualifying v0.6.15 frozen leg-universe identity receipts;
- independent pickaxe found no defining pre-v0.6.17 identity terms;
- unreachable-object census was empty.

Therefore the only valid historical conclusion is:

`V0617_PRIOR_IDENTITY_IRRECOVERABLE_REPLAY_PERMANENTLY_BLOCKED_UNDER_FROZEN_PROTOCOL`.

This is not a negative market-science result. It is a preregistration/identity result: the scientific replay cannot be reconstructed without violating its own anti-backfill rule.

### Duplicate V11 was already answered

Completed V11 run `34450053409` had 7,327 Development rows and good Brier/monotonic support, but failed the fixed ordinal requirement because at 60m RECOVERING recovery probability fell below UNSAFE in all four shock-age buckets. Thus `validation_eligible=false`.

V12 run `34450670358` then tested whether a simple shock-expiry discontinuity explained the crossover and found `shock_expiry_mechanism_supported=false`.

The 2026-09-11 duplicate V11 protocol therefore has no scientific reason to rerun.

## What this closeout does not do

It does not:

- promote any historical candidate;
- reopen old router/PnL/direction work;
- query Validation that was intentionally not queried at the time;
- query 2026/BlackBox rows;
- fabricate missing v0.6.17 identities;
- reinterpret an old Development pass as current production authority;
- delete branches or historical evidence.

## Program state after closeout

The historical branch queue is no longer a reason to keep rerunning old designs. `remaining_executable_backlog_count=0` for the exact twelve branches identified by the audit.

Future science should open only when there is a **distinct causal risk mechanism** not already answered by the current V19/D4/M3 evidence and not merely a rescue of a failed threshold/model.

`blackbox_queried=false`; `pnl_newly_computed=false`; `production_authority=false`.
