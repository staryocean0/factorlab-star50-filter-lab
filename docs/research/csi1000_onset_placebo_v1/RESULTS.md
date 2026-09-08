# CSI1000 HighVol onset-specificity placebo V1 — reviewed result

## Status

**Matching-limited / not promoted.**

The frozen run completed successfully and reproduced the frozen candidate identity exactly:

- Development candidate rows: 104.
- Validation candidate rows: 129.
- BlackBox-V1 queried: **false**.
- Future 3m outcome used in matching: **false**.

Actions run: `34217527606`.

## Raw paired result

Primary controls were already-ongoing HighVol minutes satisfying the same slow-aligned acceleration structure.

Development:

- 104 candidates, 48 matched (46.15% coverage).
- matched candidate mean gross: +1.7223 bp/trade.
- matched control mean gross: +0.4410 bp/trade.
- mean paired difference: +1.2813 bp/trade.
- trading-day bootstrap 95% interval: [-1.8179, +4.2926] bp; fraction > 0 = 0.7962.

Validation:

- 129 candidates, 74 matched (57.36% coverage).
- matched candidate mean gross: +3.2314 bp/trade.
- matched control mean gross: -1.6708 bp/trade.
- mean paired difference: +4.9022 bp/trade.
- trading-day bootstrap 95% interval: [+1.1325, +8.7570] bp; fraction > 0 = 0.9937.

## Why this is not accepted as onset-specific evidence

Matching quality is not adequate for a causal-style interpretation.

On the matched Validation sample, standardized candidate-control imbalances were approximately:

- preceding 30m net: +0.29 SD;
- recent 5m net: -0.05 SD;
- tail2 share: -0.13 SD;
- **tail1 share: +2.51 SD**;
- **continuous volatility ratio: -0.64 SD**.

The main overlap problem is structural rather than merely an optimizer issue:

- Validation candidate `tail1_share` median is about 0.455; eligible ongoing-HighVol controls median about 0.163.
- Validation candidate recovery-ratio median is about 1.653; controls median about 1.881.

A fresh `NormalVol -> HighVol` transition therefore naturally has a different last-minute composition from an already-ongoing HighVol minute. The placebo does not isolate the transition while holding the relevant path state sufficiently fixed.

There is also matching-selection drift:

- matched Validation candidates mean +3.2314 bp;
- unmatched Validation candidates mean about +1.6244 bp.

Although future outcomes were never used by the matcher, match availability changes the candidate subset enough that the raw +4.90 bp paired result cannot be treated as an onset increment.

## Conclusion

The direction of the result is compatible with onset-specific information, but **V1 does not establish it** because common support and covariate balance are inadequate.

Do not retune calipers after this result inside V1.

The next falsification should avoid cross-event matching entirely. Use the exact same frozen candidate events and compare the 3-minute return obtained by entering immediately versus delaying entry by fixed 1/2/3/5 minutes. This within-event delay-decay design directly tests whether the opportunity is concentrated near the HighVol transition.
