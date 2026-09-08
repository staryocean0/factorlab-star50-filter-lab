# Continuous volatility regime V1 — reviewed results

Date: 2026-09-08
Status: completed under three-pool governance; no BlackBox-V1 query; no candidate promotion.

## Governance

- Development: 2021-2023 only for nomination.
- Validation: 2024-2026-08-21 reusable detailed validation pool.
- Black box: not touched.
- Frozen protocol: `PROTOCOL.md`.

## Execution

Primary run: GitHub Actions `34211182672`, all frozen tests and market steps succeeded.

Exact-equivalent single-pass rerun: `34211376734`, with the Phase-2 single-pass/reference equivalence guard also passing. The two market outputs agree numerically; the largest observed numeric difference from floating summation order was below `4.4e-11 bp`. Development nominations and validation status were identical.

## Continuous state coverage

Across the currently available chronology used by the runner:

- STAR50: 15,307 `HighVol` minutes, 230,950 `NormalVol`, 107,983 `Unknown`.
- CSI1000: 18,050 `HighVol` minutes, 250,414 `NormalVol`, 117,696 `Unknown`.

This is materially denser than the earlier first-shock-triggered `Unsafe` state and removes the rare-event support bottleneck for frequency research.

## Development result: no candidate

The frozen nomination rule required a menu item to have positive 1bp-cost net PnL per exposure minute in at least 2 of the 3 development years, then rank eligible items using pooled 2021-2023 only.

Result:

- STAR50: `NONE`.
- CSI1000: `NONE`.

Therefore no primary validation candidate was opened or promoted.

### STAR50 development examples

Best pooled HighVol menu item by the frozen 1bp-cost score was the 5-minute anchor (`fixed_physical` and `scaled_clock` are identical at 5m):

- HighVol gross: `+255.06 bp`;
- one-way turnover: `1,334`;
- exposure: `3,585 min`;
- break-even one-way cost: only `0.191 bp`;
- net after 1bp one-way cost: `-0.301 bp / exposure min`.

The annual net-per-minute values were negative in 2021, 2022 and 2023.

The shorter 1/2/3m variants had still lower break-even cost or worse net scores.

### CSI1000 development examples

The best pooled HighVol score was `fixed_physical` 10m, but it was still negative after 1bp cost:

- break-even one-way cost: `0.013 bp`;
- net after 1bp one-way cost: `-0.196 bp / exposure min`.

The 1m fixed-physical variant had larger gross movement and a `0.423 bp` break-even one-way cost, but still lost `-0.412 bp / exposure min` after the 1bp stress. It was negative in every development year.

## Validation-pool diagnostic (allowed after development result)

Because Validation is reusable and detail-open under repository policy V2, the full surface was inspected diagnostically after the development nomination was fixed.

The same qualitative issue remained: the existing Butterworth/hysteresis trend family performs worse in continuous HighVol than in NormalVol.

Examples:

- STAR50 fixed-physical 5m, validation pooled:
  - HighVol net1/min `-0.373`;
  - NormalVol net1/min `-0.051`.
- CSI1000 fixed-physical 1m, validation pooled:
  - HighVol net1/min `-0.678`;
  - NormalVol net1/min `+0.054`.

Thus a broader high-volatility state does not rescue the old low-pass/trend logic by merely changing sampling frequency.

## Interpretation

The owner's economic premise and the strategy question must be separated:

1. Higher volatility can enlarge the raw price-movement budget available to pay transaction costs.
2. That does **not** imply the existing Butterworth/hysteresis trend strategy can capture that movement.
3. Under the continuous HighVol regime, this particular strategy family is systematically weak after a 1bp one-way abstract cost stress.
4. The next research question should therefore be **strategy type**, not another frequency tweak: do short-horizon returns in HighVol exhibit continuation or reversal structure?

## Decision

- Do not promote any scale/family from this V1.
- Keep the continuous HighVol state as the denser research regime for trading-frequency work.
- Next development iteration: test short-horizon momentum versus reversal using 2021-2023 only for selection, then validate frozen candidates on 2024-2026-08-21.
- BlackBox-V1 remains untouched.
