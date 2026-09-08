# CSI1000 frozen candidate three-minute holding-path diagnostic V1

Diagnostic only. No candidate parameter is changed and no BlackBox data is queried.

## Frozen candidate

Reconstruct exactly the validated CSI1000 candidate:

- `000852.SH`;
- `NormalVol -> HighVol`;
- recent 5m net > 0;
- preceding non-overlapping 30m net > 0;
- `tail2_share >= 0.60`;
- `tail1_share < 0.60`;
- enter at the next minute open;
- hold exactly 3 minutes;
- same half-session, complete valid path;
- frozen non-overlap rule.

Candidate counts must reproduce 104 Development trades and 129 reusable Validation trades.

## Path decomposition

For every selected long trade, with entry open `P0` and exit open after 3 minutes `P3`, report:

- minute-1 open-to-open contribution: `log(P1/P0)*1e4`;
- minute-2 contribution: `log(P2/P1)*1e4`;
- minute-3 contribution: `log(P3/P2)*1e4`;
- cumulative +1m, +2m, +3m return from entry;
- state at the closes after +1m and +2m (descriptive only);
- maximum favorable excursion (MFE) across the highs of the three held 1m bars versus entry open;
- maximum adverse excursion (MAE) across the lows of the three held 1m bars versus entry open.

High/low fields are used only as ex-post path diagnostics, never to define or select a candidate.

## Outputs

Report Development and Validation separately, plus yearly slices:

- mean/median minute-1, minute-2 and minute-3 contributions;
- share of total mean +3m return attributable to each minute;
- cumulative +1/+2/+3m mean and hit rate;
- MFE/MAE quantiles (10/25/50/75/90%);
- fraction still HighVol after +1m and +2m;
- fraction of trades that were profitable at +1m but unprofitable by +3m, and vice versa.

Also use 10,000 trading-day block-bootstrap draws for the mean incremental contributions of minute 2 and minute 3. This is diagnostic inference, not a new trading rule.

## Interpretation

- If minute 2/3 contributions are near zero or negative across both pools, fixed 3m holding likely contains unnecessary exposure and can motivate a new Development-only exit study.
- If minute 2/3 remain positive, the 3m hold has path-level support.
- Large MAE relative to final gross return motivates a separate Development-only risk-control study; this V1 does not choose any stop/take-profit threshold.
