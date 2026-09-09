# STAR50 HighVol sign-flip program closeout — 2026-09-09

## Status

**CLOSED — NO EMPIRICAL CANDIDATE.**

This closeout covers the bounded Development/Validation sequence V10–V17. It does not grant production authority, does not modify any production strategy, and does not query BlackBox-V1.

- `production_authority=false`
- BlackBox-V1 query count: `0`
- BlackBox ledger: unchanged
- No V18 is authorized by this closeout.

## Governance boundary used

The work followed `docs/governance/DATA_USAGE_POLICY_V2.md` and `docs/governance/data_usage_declaration.json`:

- Development: 2021-01-01 through 2023-12-31.
- Validation: 2024-01-01 through 2026-08-21.
- BlackBox-V1: not queried.

Candidates were invented/fitted only on Development, frozen before Validation, and then evaluated unchanged. Validation details were used only after a formal evaluation, as permitted by the reusable-Validation policy. No Validation-conditioned rule was allowed to validate itself.

## Development mechanism search before nomination

### V10 — cross-state volatility matrix

STAR50/CSI1000 joint volatility states were evaluated on 9,455 Development state-entry events. Four joint cells and same/opposite recent-direction subviews produced no cost-surviving three-year mechanism. `mechanism_promising_views=[]`.

### V11 — turnover activity

The pre-specified activity field was `amount`, with a fixed recent-5 / prior-non-overlap-30 ratio threshold of 1.5. Of 2,151 evaluable events, only 45 were ElevatedActivity. The pooled continuation result was positive after the 1 bp/leg proxy, but 2021 and 2023 failed. A Development-only monotonicity diagnostic did not support rescuing the threshold.

### V12 — turnover-weighted directional support

The sign of recent price movement was compared with the sign of `sum(return × amount)` without a fitted threshold. TurnoverSupported dominated the sample and did not cover cost by year; TurnoverOpposed was sparse and changed direction across years. No nomination.

### V13 — price-impact liquidity

A fixed price-impact ratio boundary of 1.0 was tested. 2,126 of 2,151 events were ImpactAmplified, so the state had little discriminating power. The 25 ImpactDamped events were unstable by year. No nomination.

### V14 — fixed intraday phase

HighVol onsets were split only by fixed half-session phase (early/middle/late and AM/PM). No view covered the 2 bp round-trip proxy in all Development years. The closest broad subview, `AM_late`, had gross continuation of about 1.64 / 1.06 / 1.49 bp in 2021/2022/2023, still below cost in every year. No nomination.

## Frozen candidates and formal Validation

### V15 — HighVol internal Up→Down recent-5 sign flip

Event definition moved away from HighVol onset. While HighVol persisted, a recent-five-minute net-return sign change from positive to negative was treated as a new-down-direction event, entered at the next eligible open and evaluated at a fixed three-minute exit.

Development evidence for `UpToDown → continuation`:

| Year | n | Gross continuation bp | Net after 1 bp/leg |
|---|---:|---:|---:|
| 2021 | 52 | 3.3411 | 1.3411 |
| 2022 | 59 | 2.5579 | 0.5579 |
| 2023 | 90 | 2.1944 | 0.1944 |
| pooled | 201 | 2.5978 | 0.5978 |

The candidate was frozen as `star50_v15_up_to_down_continuation_3m` before Validation.

Formal Validation result:

| Year | n | Gross continuation bp | Acceptance |
|---|---:|---:|---|
| 2024 | 113 | 0.5317 | fail |
| 2025 | 90 | 1.8761 | fail |
| 2026 through 2026-08-21 | 40 | 5.8821 | pass |
| pooled | 243 | 1.9104 | — |

**Verdict: VALIDATION_REJECT.**

The 2026 parquet footer was checked before candidate execution and contained no row after 2026-08-21.

### V16 — V15 sign flip conditioned on CSI1000 NormalVol

The V15 event was crossed with the already-defined CSI1000 volatility state. No new numerical threshold was fitted.

Development evidence for `STAR50 UpToDown + CSI1000 NormalVol → continuation`:

| Year | n | Gross continuation bp | Net after 1 bp/leg |
|---|---:|---:|---:|
| 2021 | 38 | 2.4777 | 0.4777 |
| 2022 | 41 | 3.2740 | 1.2740 |
| 2023 | 64 | 2.5308 | 0.5308 |
| pooled | 143 | 2.7298 | 0.7298 |

The candidate was frozen as `star50_v16_up_to_down_csi_normal_continuation_3m` before Validation.

Formal Validation result:

| Year | n | Gross continuation bp | Acceptance |
|---|---:|---:|---|
| 2024 | 64 | 0.5409 | fail |
| 2025 | 50 | -0.6857 | fail |
| 2026 through 2026-08-21 | 21 | 10.7731 | pass |
| pooled | 135 | 1.6783 | — |

**Verdict: VALIDATION_REJECT.**

Both STAR50 and CSI1000 2026 parquet footers were checked before candidate execution and contained no row after 2026-08-21.

### V17 — first Up→Down flip within a HighVol episode

The event was split by ordinal occurrence within a continuous HighVol episode. Of 234 evaluable Development events, 232 were the first Up→Down flip, so ordinal status was nearly degenerate and was not a strong explanatory partition. Nevertheless, the frozen first-flip candidate met the pre-registered Development gate:

| Year | n | Gross continuation bp | Net after 1 bp/leg |
|---|---:|---:|---:|
| 2021 | 64 | 2.6968 | 0.6968 |
| 2022 | 71 | 2.0122 | 0.0122 |
| 2023 | 97 | 2.3164 | 0.3164 |
| pooled | 232 | 2.3282 | 0.3282 |

The candidate was frozen as `star50_v17_first_up_to_down_highvol_episode_continuation_3m` before Validation.

The first Validation workflow attempt failed technically before producing research evidence because it reused a Development-only minute-grid constructor. The candidate definition and freeze were not changed. The evaluator was repaired to construct the Validation grid directly, then rerun under the same freeze.

Formal Validation rerun:

| Year | n | Gross continuation bp | Acceptance |
|---|---:|---:|---|
| 2024 | 123 | 0.2972 | fail |
| 2025 | 105 | 1.6776 | fail |
| 2026 through 2026-08-21 | 43 | 2.7523 | pass |
| pooled | 271 | 1.2216 | — |

**Verdict: VALIDATION_REJECT.**

The 2026 parquet footer guard passed before the formal rerun.

## Adjudication

The Development data repeatedly supported a short-horizon directional mechanism after a HighVol-internal Up→Down sign flip. Three separately frozen formulations passed the same Development gate. None survived the reusable Validation pool across 2024, 2025, and 2026-through-2026-08-21.

The repeated pattern is important:

1. Development evidence is real enough to retain as mechanism evidence.
2. The directional payoff is not stable enough to promote as an empirical trading candidate.
3. Strong 2026 Validation performance does not rescue failures in 2024 and/or 2025.
4. Additional slicing of the already-opened Validation pool to manufacture V18 would materially increase data-mining risk and is not justified by the evidence.

Therefore the program state is:

```text
HighVol state: retained as certified/diagnostic market-state evidence
HighVol directional sign-flip route: CLOSED
V15: Development pass -> Validation reject
V16: Development pass -> Validation reject
V17: Development pass -> Validation reject
empirical_candidate: none
production_authority: false
BlackBox-V1 queries: 0
```

## Research implication

The work continues to support HighVol as a meaningful causal risk/state annotation, but not as a validated directional trade route. The evidence is more compatible with defensive treatment—neutralization, exclusion, reduced trust in short-horizon directional signals, or further theory work on a genuinely new payoff object—than with promoting the tested sign-flip continuation rules.

Any future reopening must begin with a genuinely new, pre-specified mechanism hypothesis in Development. It must not be a retrospective threshold/time/cross-state refinement chosen from the V15–V17 Validation failures. BlackBox-V1 remains reserved for a future frozen candidate that first earns that right under governance.
