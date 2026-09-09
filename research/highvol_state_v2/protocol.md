# HighVol / Unsafe recovery dynamics v2 — frozen diagnostic protocol

Date: 2026-09-09

## Authority and purpose

This diagnostic continues the repository's current cross-index K-line risk-state research. It does **not** promote the migrated reversal / mean-reversion program to current authority and does not create a trading strategy.

The input state definitions are inherited unchanged from `research/highvol_state_v1/run_analysis.py`:

- 5m intraday log returns; overnight returns excluded;
- `RV_WINDOW=12`;
- `BG_WINDOW=48` preceding valid intraday 5m returns;
- `HIGHVOL_RATIO=1.50`;
- `EXTREME_RATIO=2.25`;
- `RECOVERY_NORMAL_RATIO=1.10`;
- `SHOCK_SIGMA=3.00`;
- risk state resets each trading day.

No threshold is selected or retuned in v2.

## Data boundary

Use only the existing bounded 5m annual shards for `000688.SH` and `000852.SH`, restricted to common trading days from 2020 through 2025. No 2026 data, BLACKBOX allocation, ETF/option data, PnL, position sizing, or production action is permitted. All evidence is consumed historical development evidence (`fresh_oos=false`).

## Episode unit

A shock-triggered Unsafe episode begins at a bar satisfying:

1. `shock == True` under the inherited 3-sigma rule; and
2. the immediately preceding bar in the same trading day is not `UNSAFE`.

Once started, the episode continues within the same trading day until the first subsequent `NORMAL` risk-state bar. If no `NORMAL` bar occurs before the session ends, the episode is right-censored at the session boundary. Additional shock bars before recovery are recurrences within the same episode, not new independent episodes.

This event unit prevents overlapping 5m shock bars from being counted as independent recovery episodes.

## Frozen measurements

For every episode record:

- bars until leaving `UNSAFE` for the first time;
- bars until first `NORMAL`, if observed;
- same-session Normal recovery indicator;
- right-censor indicator;
- any recurrent shock before Normal;
- recurrent-shock count before Normal;
- maximum inherited `vol_ratio` before Normal/session end;
- maximum inherited `shock_intensity` before Normal/session end.

For each symbol, pooled and by calendar year, report:

- episode count;
- same-session Normal recovery fraction;
- recurrence-before-Normal fraction;
- median and p90 bars-to-Normal among observed recoveries;
- median bars to leave Unsafe;
- censor fraction;
- median episode peak vol-ratio and shock-intensity.

Also publish a pooled discrete survival curve for horizons 1..12 bars (5..60 minutes): fraction of episodes that have **not yet reached Normal** by each horizon. Censored sessions remain not-recovered through the available session horizon and are not extrapolated beyond observed bars.

## Cross-index interpretation

No new pass/fail threshold is introduced. The report must show pooled differences and annual direction counts for the main recovery measures. A pooled difference is not called structurally stable unless its direction is also visible across calendar-year rows; even then it is historical mechanism evidence, not a trading-module authorization.

The migrated RMR evidence is used only as a methodological constraint: mechanism/state evidence must remain separate from economic payoff mapping. Therefore v2 contains no signed-return optimization, horizon selection for profit, stop/target search, or instrument mapping.

## Outputs

- `outputs/episode_ledger.csv`
- `outputs/annual_episode_metrics.csv`
- `outputs/unsafe_survival_curve.csv`
- `outputs/cross_index_direction_summary.csv`
- `outputs/report.md`

`production_authority=false` remains unchanged.
