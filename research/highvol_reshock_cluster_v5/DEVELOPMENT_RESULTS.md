# HighVol re-shock cluster v5 — Development result

Status: **RECURRENT SHOCK RESETS RECOVERY CLOCK; GENERIC SELF-EXCITING CLUSTER NOT ESTABLISHED**.

Risk-state research only; no PnL, trade rule, Validation or BlackBox data.

Run `34415064379`, artifact `10128736040`, ZIP SHA256 `82b5423bdfaa2af5398ccccfbc28bce43a6a25770e3a11c715320dbf0ad679b4`.

Development episode anchors:

- STAR50: 459 initial shocks; 72 episodes with a first recurrent shock. Median first recurrence age 2 bars = 10m; p90 10 bars = 50m.
- CSI1000: 417 initial shocks; 67 first recurrent shocks. Median first recurrence age 3 bars = 15m; p90 10 bars = 50m.

## Robust reset-clock finding

After the first recurrent shock, near-term Normalization probability collapses relative to the initial shock, in both indices and in every Development year.

| symbol | anchor | P(Normal <=15m) | P(Normal <=30m) | median bars to Normal |
|---|---|---:|---:|---:|
| STAR50 | initial | 25.83% | 26.89% | 12 |
| STAR50 | first recurrent | 2.78% | 4.17% | 12 |
| CSI1000 | initial | 28.54% | 32.37% | 12 |
| CSI1000 | first recurrent | 2.99% | 7.46% | 12 |

The median remaining recovery time after a recurrent shock is again 12 five-minute bars (60m), the same scale as after an initial shock. This supports a **clock-reset interpretation**: a fresh shock restarts the recovery process even when it occurs inside an already active episode.

## No common self-excitation rule for further shocks

The probability of yet another shock after the first recurrence is not uniformly higher across the two indices:

- STAR50: next-shock probability after recurrence is slightly lower than after initial shock (15m: 8.33% vs 9.49%; 30m: 8.33% vs 12.44%), with the same sign in each Development year.
- CSI1000: pooled probability is higher after recurrence (15m: 16.42% vs 8.87%; 30m: 17.91% vs 12.80%), but 2021 reverses that ordering while 2022/2023 support it.

Therefore a universal `CLUSTERED` branch is not yet justified by recurrence probability alone.

## Forward implication

The more defensible next step is to replace or augment **episode age since the first shock** with **time since the most recent shock** in recovery calibration. That is a risk-process measurement change, not a trading rule.

`production_authority=false`; `validation_queried=false`; `blackbox_queried=false`.
