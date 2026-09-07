# V3.3 frozen protocol — STAR50 e-2 single-score risk-budget gate

Date: 2026-09-07  
Status: **frozen before V3.3 gate outcomes**  
Parent evidence: V3.2 archived at `e638ed1b92f5e5e8e2816c31d851b1604f64e5bc`; V3.2 scientific code/tests are `5574f862068295a2b00a8e2bcc545ceb713216bd` / `3fd0a038f2f93827011e8f53cc92a94241243f00`.

## Question

Does the one V3.2 signal that survived model-free precursor-existence diagnostics have enough practical time concentration to act as a **strictly pre-event risk gate** for STAR50 quiet-first shocks?

This is not a new morphology search and not a classifier fit. It converts the already-fixed V3.2 score into three precommitted market-time budgets and measures event coverage.

## Fixed scope

- Symbol: **000688.SH only**. CSI1000 is excluded because V3.2 did not support this score route.
- Data: bounded historical 1m + 3s inputs already used by V3.2, through 2025 only.
- No 2026 data, no returns/P&L, no trading, no OOS or production claim.
- 2024 and 2025 remain consumed historical evaluation, not fresh OOS.
- Quiet-first event taxonomy is inherited unchanged from V3/V3.2.
- Event feature time is exactly `e-2`; no e-1 or event-minute feature may enter this test.

## Frozen score

For every causally eligible feature minute `t`:

`S_t = 0.5 * [(logE30_t - logE240_t) + (logE60_t - logE240_t)]`

This is exactly V3.2 `primary_scale_score`. No refit, rescaling, seasonal normalization, feature addition, sign flip, transformation, or threshold search is allowed.

## Opportunity universe

A risk-time opportunity is a STAR50 minute for which:

1. V3.2 can construct the frozen score from bounded historical inputs without carry-forward;
2. the score is finite;
3. `minute >= 31` within the half-session;
4. minute `t+2` exists in the same half-session, so the nominal event decision has a full two-minute index separation and at least one complete minute of lead.

No future event label, `quiet_pre`, or `near_first_tail` flag may be used to select the opportunity universe. Missing score/support is Unknown, not imputed.

Because the score itself needs a 30-minute scale, V3.3 **does not claim coverage of the first 30 minutes after a session opens**.

## Unsupervised calibration and fixed budgets

Threshold calibration uses **all eligible STAR50 opportunity scores from 2022–2023**, with no event labels involved.

Nominal flagged-time budgets are fixed at:

- 10%: calibration threshold = empirical 90th percentile of `S`;
- 20% (**primary budget**): empirical 80th percentile;
- 30%: empirical 70th percentile.

Use NumPy empirical quantiles with `method="higher"`; flag when `S >= threshold`. Ties may make realized coverage differ from the nominal budget, so realized coverage must always be reported.

The three thresholds are frozen once from 2022–2023 and applied unchanged to 2024 and 2025 separately and combined. No retuning between 2024 and 2025 is allowed.

## Event denominator

For each 2024/2025 STAR50 first-tail event satisfying the inherited V3 quiet-first definition and `event_minute >= 33`:

- feature minute is exactly `event_minute - 2` in the same session;
- if the frozen score is finite, the event is `evaluable`;
- otherwise it is `unknown`.

For every budget report both:

- `recall_evaluable = flagged_evaluable_events / evaluable_events`;
- `recall_conservative = flagged_events / all_in_scope_quiet_first_events`, where Unknown counts as not flagged.

Unknown events may not be deleted from the conservative denominator.

## Primary and secondary metrics

For each budget and each of 2024, 2025, and 2024–2025 combined report:

- nominal budget;
- frozen threshold;
- eligible risk-time opportunities;
- realized flagged-time share;
- all in-scope quiet-first events;
- evaluable / unknown event counts;
- flagged event counts;
- evaluable and conservative recall;
- `lift = recall_conservative / realized_flagged_time_share` when coverage is positive;
- Clean time share = `1 - realized_flagged_time_share`;
- Clean event leakage = `1 - recall_conservative`.

Also report the same metrics for two fixed time strata:

- `early_post_warmup`: event minutes 33–60 (feature minutes 31–58);
- `ordinary`: event minutes >60 (feature minutes >58).

This split is descriptive and cannot change the primary combined decision.

## Interpretation rule frozen before outcomes

The primary budget is 20%.

- If combined 2024–2025 conservative recall is no better than realized flagged-time share (`lift <= 1`), the single-score gate route is **not supported**.
- If lift is >1 but either conservative recall <40% or lift <2, evidence is **weak/descriptive only**.
- If conservative recall >=40% and lift >=2, the route **survives only as a candidate for future prospective confirmation**. It is still not an accepted risk gate because 2024–2025 are consumed history and the event count is small.

The 10% and 30% budgets are sensitivity points, not alternate primaries. No budget may be selected after seeing outcomes.

## Required integrity outputs

The runner must emit:

- `calibration_thresholds_v33.json`;
- `opportunity_coverage_v33.csv`;
- `quiet_first_event_gate_v33.csv`;
- `budget_summary_v33.csv`;
- `summary_v33.json`;
- `run_receipt_v33.json`.

The receipt must record source audits inherited from V3.2, code commit/ref, input year scope, threshold method, score formula, and flags `fresh_oos=false`, `results_blind_gate_thresholds=true`, `returns_or_pnl_evaluated=false`, `production_authority=false`.

## Still frozen

This experiment does not unlock morphology replication acceptance, direction labels, third-wave labels, returns/P&L, fresh OOS, trading, position sizing, or production. It also does not modify the separate v0.6.17 identity-blocked replay protocol.
