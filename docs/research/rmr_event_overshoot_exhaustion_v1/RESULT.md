# RMR event-time overshoot exhaustion V1 — RESULT

Run: `34325962578`

Verdict: **`broad_signal_source_not_established`**.

Development-only 2021–2023; 34,558 confirmation/overshoot event rows across two indices and two predeclared 20/40 bp scales. Validation and BlackBox were not queried.

At every symbol/scale cell, the one-full-threshold overshoot failed to become a stable 5-minute reversal source. Pooled examples:

- STAR50 20bp: confirmation median signed F5 `+0.5968 bp`; overshoot `+1.3435 bp`; reversal probability `48.64% -> 47.00%`.
- STAR50 40bp: confirmation `+1.5961`; overshoot `+1.4427`; reversal probability `46.80% -> 46.56%`.
- CSI1000 20bp: confirmation `+1.8728`; overshoot `+2.1554`; reversal probability `43.99% -> 43.81%`.
- CSI1000 40bp: confirmation `+2.3569`; overshoot `+3.2673`; reversal probability `43.02% -> 41.52%`.

Thus naked directional-change overshoot is not an exhaustion / mean-reversion source under this V1 identity. Do not rescue by changing scales, overshoot multiples, clocks, parent-state or HighVol filters inside V1.

`production_authority=false`.
