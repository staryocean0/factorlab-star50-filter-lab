# HighVol / Unsafe recovery dynamics v2 — retained risk-state anchor

Date restored to current risk-state authority: 2026-09-10.

This is bottom-layer K-line risk-state evidence and is in scope for `factorlab-star50-filter-lab`. It is not a payoff strategy, router, holding-period rule, or production policy.

## Historical identity and provenance

The original frozen diagnostic protocol was created at commit `b61d26e707bc41bbfefeb7f6fe15a70c856267bf` (`research/highvol_state_v2/protocol.md`, blob `c8ac14b81dc1750d9e78cfa04c5439e7dffa0564`).

The frozen runner was added at commit `ed3431b6c69553d842cd5cefb4e7eca79a8673a0` (`research/highvol_state_v2/run_episode_diagnostics.py`, blob `4df7cbe08f150efb04427d741a377c101d74e9aa`).

The decisive historical outputs were recorded at commit `8fc209c12f37143f2307c80142f9fabb855c71af`. They remain recoverable from Git history even though the one-off runner/output surface is not kept active in the current tree.

## Frozen inherited state definition

Inherited unchanged from historical `research/highvol_state_v1/run_analysis.py`:

- 5-minute same-day log returns; overnight returns excluded;
- recent realized-volatility window: 12 bars;
- preceding background-volatility window: 48 bars;
- `HIGHVOL_RATIO = 1.50`;
- `EXTREME_RATIO = 2.25`;
- `RECOVERY_NORMAL_RATIO = 1.10`;
- shock threshold: absolute 5-minute return / background volatility `>= 3.00`;
- risk state resets each trading day.

State machine: shock enters `UNSAFE`; after shock, `vol_ratio >= 1.50` stays `UNSAFE`, `1.10 < vol_ratio < 1.50` is `RECOVERING`, and `vol_ratio <= 1.10` returns to `NORMAL`.

## Episode definition

A shock-triggered episode begins when `shock=True` and the immediately preceding same-day bar is not `UNSAFE`. It ends at the first subsequent `NORMAL` bar or is right-censored at the session/day boundary. Recurrent shocks before Normal remain inside the same episode.

## Historical pooled findings, common days 2020-2025

| metric | STAR50 `000688.SH` | CSI1000 `000852.SH` |
|---|---:|---:|
| shock-triggered Unsafe episodes | 790 | 766 |
| same-session Normal recovery | 96.08% | 95.30% |
| recurrent shock before Normal | 16.71% | 16.19% |
| median bars to Normal | 12 | 12 |
| p90 bars to Normal | 17 | 16 |
| median bars to leave Unsafe | 1 | 1 |
| session censor fraction | 3.92% | 4.70% |
| not Normal by 60m | 35.42% | 29.89% |
| median episode peak vol-ratio | 1.512 | 1.477 |

The central retained finding is therefore a **risk process**, not a trade: shock-level `UNSAFE` often ends quickly, while full return to `NORMAL` commonly takes about an hour and recurrent shocks occur in roughly one-sixth of episodes.

Cross-index pooled differences were not structurally strong or annually one-directional enough to justify separate state machines. The two indices therefore remain comparable under the common state definition unless a future frozen risk-state study establishes otherwise.

## Forward use

This anchor is the starting point for the next in-scope question: conditional recovery and recurrence hazard during an active shock episode. New work must use the current three-pool governance and may not convert these state results into a directional trading rule.

`production_authority=false`. No BlackBox authority is inherited from this historical result.
