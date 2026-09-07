# 2026 post-shock recovery validation protocol

Date: 2026-09-07. Base research: `research/first-shock-seconds-v2-20260907` at `b37775a9be3d1d188bce15fc6f5014866b92070a`.

Owner authorization: user explicitly replied `授权` to permit 2026 data for independent validation of the post-shock recovery-state research. This authorization applies only to historical/research validation in this topic; it does not grant trading, account, live-order, production, or registry mutation authority.

## Validation role

2026 is a held-out validation period for this branch. Do not refit, recalibrate, tune thresholds, choose features, or select event definitions using 2026 outcomes.

Frozen objects from prior work:
- first-shock operational event definition;
- post-shock `Unsafe / Recovering` state definitions;
- current trailing-5m volatility ratio as the primary recovery score;
- previously registered simple release rules and richer recovery/release models only as fixed comparators;
- no online `Clean` transition is assumed valid before this evaluation.

## Primary 2026 tests

1. Recompute the first-shock event universe on 2026 minute data using the frozen definition.
2. Recompute post-shock risk decay and censor-adjusted release duration using the frozen V1 definitions.
3. Evaluate the primary recovery score: current trailing-5m RMS / pre-shock sigma against next-5m realized risk.
4. Evaluate all previously frozen release rules/models without refitting and report whether any reaches the preregistered high-confidence release thresholds.
5. If 3s data are available, repeat the fixed post-shock path-feature evaluation without feature selection or threshold search.
6. Report STAR50 and CSI1000 separately, then pooled only as a secondary view.

## Required 2026 input support

Minimal period: 2026-01-01 through the latest fully completed trading day available at export time, capped at 2026-09-07 for this validation snapshot.

Symbols/frequencies:
- `000688.SH`: native 1m and 3s source observations;
- `000852.SH`: native 1m and 3s source observations.

1m must retain the existing source/quality semantics used by the repository, including at least: `symbol`, `timestamp`, `trading_day`, OHLC/close fields used by the current loader, `causal_flat_fill`, `source_minute_count`, `high_frequency_analysis_eligible`, and source/version identity fields.

3s must retain the existing source semantics used by V2, including at least: `symbol`, `observation_datetime`, `trading_day`, `price`, `row_index`, and source/version identity. Same-second rows must not be silently deduplicated. No interpolation is permitted.

An authoritative manifest/receipt must include row counts, first/last day, file hashes, timezone semantics, dataset/source version, and confirmation that the export contains no post-snapshot dates.

## Acceptance

A 2026 conclusion is valid only if the above files are available under a new bounded 2026 research export/manifest or an equivalent authoritative DataHub receipt. Do not append 2026 bytes to the sealed 2021-2025 manifests or rewrite their hashes.

If the 2026 export is partial, evaluate only the completed support and report exact coverage/censoring. Missing data are Unknown, never Clean.
