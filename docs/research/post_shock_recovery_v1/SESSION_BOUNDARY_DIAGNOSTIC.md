# Session-boundary recovery diagnostic

Date: 2026-09-07. Exploratory consumed-history diagnostic. It does not change the frozen same-half-session state machine.

## Question

The supported post-shock episode terminates at lunch, close or overnight. Does that boundary mean risk has actually normalized, or is it merely a research truncation because the current score deliberately does not bridge session gaps?

## Cross-lunch check

For morning first shocks in 2024-2025, compare the first 15 valid afternoon minute returns with matched non-event mornings at the same minute and similar event-time background sigma. Each afternoon RMS is normalized by its corresponding morning anchor sigma.

23 morning first-shock events have usable matched comparisons.

Average afternoon-first-15m normalized RMS:

- first-shock days: about **1.08x** anchor sigma;
- matched control days: about **0.89x**;
- mean paired difference: about **+0.19x sigma**;
- median paired difference is only about +0.03x sigma.

The annual/index cells are heterogeneous:

- STAR50 2024: +0.12;
- STAR50 2025: +0.63;
- CSI1000 2024: +0.01;
- CSI1000 2025: one event, -0.06.

Events closer to the lunch boundary show larger residual afternoon differences in this consumed sample, which is plausible because there is less in-session time to recover, but this is a result-after exploratory observation rather than a frozen causal rule.

## Overnight check

For afternoon first shocks, compare the next trading day's first 15 valid morning returns with same-minute/similar-sigma non-event controls.

54 events have usable comparisons.

The pooled mean difference is about +0.16x sigma, but the median is approximately zero and the annual/index direction changes:

- STAR50 2024 positive;
- STAR50 2025 negative;
- CSI1000 2024 near zero;
- CSI1000 2025 positive on only four events.

Overnight market information, opening mechanics and the long time gap make this especially unsuitable for silently carrying the same episode score across the boundary.

## Decision

Keep the frozen state machine bounded to one half-session.

However, `ENDED` or boundary termination means:

**episode censored / outside the current state model**, not `Clean` and not proof that risk disappeared.

Do not bridge lunch or overnight by filling missing returns, carrying the five-minute window across the gap, or treating the boundary as a safe release.

A future cross-boundary risk model must be a separate protocol with boundary-specific normalization and genuinely new validation data. The present evidence is insufficient to add cross-lunch or overnight continuation to the stable state machine.
