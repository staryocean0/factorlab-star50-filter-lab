# Current research entry

## 2026-09-09 scope-repaired authority

**Current task: STAR50 / CSI1000 bottom-layer K-line risk-state research only.**

The research product of this bucket is a causal risk annotation/gate answering questions such as:

- is recent volatility normal, expanding, clustered or shock-like?
- should the current state switch into `Unsafe` / `HighVol`?
- if already risky, is the evidence persistent enough to stay risky?
- when is recovery evidence strong enough to move toward `Recovering` / normal risk?
- which cross-scale K-line attributes explain false switches and missed danger?

The current task is **not** to optimize a directional trading strategy.

## Correct neighboring buckets

- `factorlab-two-wave-strategy-lab`: causal parent-structure classification into range / uptrend / downtrend from completed same-scale waves.
- `factorlab-trend-reversion-regime-lab`: concrete reversal / mean-reversion strategy research including R1/R2.

## Historical material retained but no longer current authority

This repository contains extensive historical strategy/payoff research, including:

- HighVol Router V1;
- STAR50 V10-V17 directional sign-flip research;
- half-day slope and earlier filter/payoff variants;
- drawdown/account/payoff diagnostics;
- previously misplaced R1/R2 material (already migrated out).

These files are **not deleted**. The complete pre-repair current snapshot remains in Git at commit:

`4232d20b143a9c532e14a39761370bf1eca8d084`

They may be consulted for historical evidence. Any reusable conclusion must be separated into either:

1. bottom-layer risk-state evidence that legitimately belongs here, or
2. payoff/strategy evidence that does not regain current authority in this bucket.

HighVol Router V1 and sign-flip results therefore remain historical evidence, not the next research task.

## Current valid risk-research anchors

Examples of in-scope historical material include:

- `docs/handoff/cloud_risk_gate_20260907/`
- `docs/research/causal_volatility_tool_v1/`
- tail distribution / resolution-transfer / cross-scale root-cause material where the result is a K-line risk property rather than a payoff rule;
- HighVol/Unsafe causal state definitions and state-analysis diagnostics, after payoff-specific conclusions are separated.

## Governance

Read `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md` and `docs/governance/DATA_USAGE_POLICY_V2.md` before new work.

Forward data roles remain:

- Development: 2021-2023;
- reusable Validation: 2024 through 2026-08-21;
- protected BlackBox-V1 after the cutoff under its existing aggregate-only protocol.

No previous payoff Validation pass authorizes a future BlackBox risk-state query. New risk-state work must freeze its own protocol first.

`production_authority=false`.
