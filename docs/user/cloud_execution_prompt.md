# STAR50 filter lab — cloud research prompt

> Superseded by the user's 2026-09-07 scope expansion. Read
> [`../handoff/cloud_risk_gate_20260907/HANDOFF.md`](../handoff/cloud_risk_gate_20260907/HANDOFF.md)
> and validate the new bounded package. The content below is immutable historical
> context only; do not execute its trading tasks or use its working-clock restriction.

Private bounded theme. Do not write to or merge with
`factorlab-two-wave-strategy-lab`, `factorlab-overnight-open-lab`, or
`factorlab-multifactor-stock-lab`.

Instrument: `000688.SH` 科创50. Working chart: **5-minute +0**, not 1-minute.
Filters are causal IIR (Butterworth). 1st-order is already IIR; 2nd-order is
steeper IIR, not a new family.

Data roles: 2020 H2 warmup; 2021-2025 development; 2026 consumed, not for
selection. Index point, zero cost, always-in long/short. No production authority.

## Current findings (already in docs/research)

- STAR50 path-efficiency is stably low across frequencies. 5m is the working
  chart. Physical slow component is about 10-20 trading days; 1-hour is the
  current experimental operating period (12 five-minute bars).
- Strategy: sign of lowpass slope, next-open reverse. Vol-scaled hysteresis
  (k=1 × 1-day 5m sigma) beat slope-only on 2021-2025 (CAGR ~87%, MDD ~-14%).
- Remaining grind is **working-band vs slower band**, not high-frequency leak.
  本频 has oscillation without completed waves; 低频 has the net direction.
  Simple “never fade 20-day slope” is not a switch: 本频 vs 20d agreement is
  ~50% in both losing and winning periods.
- 2nd-order + same vol gate did not beat 1st-order + vol gate. Steeper filter
  delayed exits on fake shorts in slow uptrends.

## Allowed next work

- Amplitude/stability-conditioned slower-band veto (not mere sign agreement).
- Keep 2026 out of ranking.
- Report MDD, top-10 DD types, CAGR on 2021-2025.
- Do not grant production or mix Layer 4 options.
