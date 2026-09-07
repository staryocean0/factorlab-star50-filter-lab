# Post-shock causal release rule protocol

Date: 2026-09-07. Written after the descriptive duration curve was computed, but before evaluating any causal release rule on future stability.

Goal: define simple online-observable candidates for leaving `Unsafe/Recovering` after a first shock. No model or threshold search.

At each minute close starting 5 minutes after the first-shock minute, using only returns observed since the shock and the pre-shock `sigma_pre`:

- `trail5 = RMS(last 5 completed post-shock minute returns) / sigma_pre`
- `max5 = max(abs(last 5 completed post-shock minute returns)) / sigma_pre`
- `trail2 = RMS(last 2 completed post-shock minute returns) / sigma_pre`

Fixed candidates:

1. **R1 background-only**: release when `trail5 < 1.0`.
2. **R2 no-spike**: release when `trail5 < 1.0 AND max5 < 1.5`.
3. **R3 strict-cooling**: release when `trail5 < 1.0 AND max5 < 1.5 AND trail2 < 0.8`.

The first qualifying minute is the candidate release time. Missing returns or session truncation cannot trigger release.

Primary safety outcome: after a candidate release, the next two non-overlapping 5-minute blocks must each have RMS / `sigma_pre < 1.0`. This is the same stable-background outcome used in the descriptive release label.

Report for every rule without selecting the best: trigger coverage, median trigger time, false-release share, stable-release precision, and delay relative to the descriptive oracle release-start. Report both indices, 2024 and 2025, plus pooled-by-year. Also compare fixed-time release at +10, +15, +20, +30 minutes using the same future-stability outcome.

Interpretation: a useful release rule needs both acceptable release coverage and low false-release leakage. A rule that almost never releases is not considered successful merely because precision is high. These are consumed-history diagnostics, not production acceptance.
