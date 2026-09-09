# HighVol recovery clock v6 — frozen Development protocol

Purpose: determine whether recovery risk is better indexed by **time since the most recent shock** than by **time since the episode-start shock**. This is risk-state measurement only; no trading/PnL.

## Data and inherited state

Use the unchanged v3 state engine and de-overlapped shock episodes. Development only: 2020 warm-up; 2021–2023 measured rows; STAR50 and CSI1000 common days; physical exclusion of 2024+ and BlackBox.

## Observation rows

For each active episode, consider each non-shock bar after the start shock and before first `NORMAL`. Require a fully observed next-15-minute recovery target (or an earlier observed Normal).

For each row calculate two causal clocks:

- `episode_age`: bars since the episode-start shock;
- `recent_shock_age`: bars since the most recent shock in the same active episode.

A new shock resets `recent_shock_age` to zero; the shock bar itself is not a scored row.

## Frozen age buckets

Use the same four coarse risk horizons for both clocks:

- bars 1–2: `<15m`;
- bars 3–5: `15–25m`;
- bars 6–8: `30–40m`;
- bars >=9: `>=45m`.

Each model is an 8-cell Laplace-smoothed table: `current state {UNSAFE, RECOVERING} × age bucket`, probability `(successes+1)/(n+2)` for `NORMAL within next15m`.

## Development comparison

Use leave-one-year-out evaluation:

- fit both tables on two Development years pooled across both indices;
- score the held-out third year;
- repeat for 2021, 2022 and 2023.

Report Brier and LogLoss overall and by symbol for each held-out year.

Then fit a final recent-shock-clock 8-cell table on all 2021–2023 rows only for possible later freeze.

## Frozen evidence rule

A recent-shock clock is supported for further validation only if:

1. its Brier score is lower than the episode-age clock in **all 3** held-out years;
2. its LogLoss is lower in at least **2 of 3** held-out years;
3. all 8 final recent-shock cells have at least 100 rows;
4. final `RECOVERING` probability exceeds `UNSAFE` probability in all 4 age buckets;
5. state thresholds/episode rules are unchanged; no Validation/BlackBox data is read.

Failure means keep episode-age calibration as current supported object and treat shock reset as descriptive only. Passing allows a separate frozen recent-shock-clock Validation study; it does not modify production or trading behavior.

`production_authority=false`.
