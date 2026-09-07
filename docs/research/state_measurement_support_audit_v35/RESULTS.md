# State / measurement support audit v3.5

Date: 2026-09-08  
Branch: `research/state-measurement-support-audit-v35-20260908`  
Preregistered protocol commit: `3af16c0bcbe43349511ca9f9752a635f57c1784f`  
Frozen scientific implementation/test ref: `d4c55741eb19684d86b2c771945acba17c842462`  
Successful Actions run: `34144712706`  
Workflow commit: `3209a25da4588105f0801ab51ababd3248f48cd7`  
Artifact: `10027285202`, digest `sha256:b48d198098f30abc5412433517b8f9c444801f6037b9b6b6f6d07a04dbe0239a`  
Tests: **6 passed**. The runner did not create or consume any future shock target, risk-gate metric, returns/P&L, 2026 data or production state.

## Why this audit exists

The frozen STAR50 V3.2 scale-score route was stopped after V3.3 failed as a raw full-universe gate and V3.4 failed again after historical `(log_sigma_pre, log_rv480)` conditioning. V3.5 does **not** try to rescue that score. It asks whether the growing historical-support mismatch is primarily:

1. a common volatility-state transport problem;
2. a STAR50-specific state transport problem; or
3. a fine-measurement-support artifact.

The state reference is 2022–2023. For each exact morning/afternoon × minute group, the audit uses the same fixed 100-neighbor geometry and leave-one-out 99th-percentile support limit, but no future label. Measurement support is described with the already-frozen 15s endpoint-grid diagnostics; snapshot rows are never interpreted as trade intensity.

## 1. State transport: 2024 is largely common; 2025 is STAR50-specific

### All clock-scope rows, minute 31–105

| symbol | year | rows | state extrapolated | median 100th-NN distance | sigma outside historical 1–99% | rv480 outside historical 1–99% |
|---|---:|---:|---:|---:|---:|---:|
| STAR50 | 2024 | 35,376 | **10.52%** | 0.817 | 8.38% | 12.62% |
| STAR50 | 2025 | 35,964 | **15.18%** | 1.020 | 13.07% | 21.82% |
| CSI1000 | 2024 | 35,816 | **9.95%** | 0.976 | 9.01% | 8.62% |
| CSI1000 | 2025 | 35,964 | **2.07%** | 0.755 | 2.67% | 2.02% |

In 2024 both indices move outside the 2022–2023 historical state surface at similar annual rates. This is consistent with a market-wide transport problem rather than a STAR50-only phenomenon.

In 2025 the paths diverge sharply: STAR50 historical-state extrapolation rises further to 15.18%, while CSI1000 falls to only 2.07%. Thus the 2025 STAR50 support problem cannot be described as a generic common-market state shift.

### Month concentration

The annual averages hide episodic and two-sided state changes.

- 2024 October: STAR50 66.51% extrapolated; CSI1000 57.13%.
- 2024 February: STAR50 28.78%; CSI1000 51.17%.
- 2025 September: STAR50 **61.49%**; CSI1000 **2.30%**.
- 2025 August: STAR50 27.61%; CSI1000 0.77%.
- 2025 June: STAR50 20.07%; CSI1000 0.24%.

For STAR50, 2025 June/July have strongly negative signed historical-state z scores, while September/October are strongly positive. Therefore the relatively modest annual signed mean is not evidence of stability; opposite state excursions cancel in the mean while nearest-neighbor distance and historical-envelope exceedance remain high.

The drift is not confined to one half-session or one fixed minute band. STAR50 2025 extrapolation is approximately 14–16% in the all-clock three fixed bands and 14–16% across morning/afternoon. This is not merely an opening or closing clock artifact.

## 2. The exact V3.4 STAR50 quiet-decision route shows the same transport problem

Using the same causal quiet universe as V3.4, but without reading any future target:

| year | rows | state extrapolated | sigma outside 1–99% | rv480 outside 1–99% |
|---:|---:|---:|---:|---:|
| 2024 | 20,110 | **5.74%** | 4.82% | 7.31% |
| 2025 | 21,559 | **12.57%** | 13.01% | 17.94% |

The route-level result exactly reproduces the state-support fractions observed in V3.4. Hence the V3.4 support failure is not an artifact of the future-label evaluation code.

Route-level 2025 concentration is even more episodic: September is 73.45% extrapolated and October 39.38%, while December is 0%. Again, a single stationary historical support surface is a poor description of this year.

## 3. Fine measurement support does not explain the 2025 failure

### Frozen primary scale-score availability

| symbol | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| STAR50 | 65.07% | 99.82% | 99.68% | **100.00%** |
| CSI1000 | 65.07% | 99.82% | 99.83% | **100.00%** |

The low 2022 fraction is consistent with the already-known historical 3s support gap before mid-May 2022. From 2023 onward the strict fine measurement surface is essentially complete, and 2025 is the cleanest year in this diagnostic.

For both indices in 2025:

- mean `fine_gap3_fraction5 = 0`;
- p95 `fine_gap3_fraction5 = 0`;
- mean/p95 `fine_max_age5 = 0`;
- primary score availability = 100%.

Within the STAR50 V3.4-like route, 2025 in-support and extrapolated state rows both have `fine_gap3_fraction5 = 0` and `fine_max_age5 = 0`; repeat fractions are also nearly identical. Therefore state extrapolation is not co-located with a degraded fine-data support surface.

## Scientific interpretation

V3.5 supports the following narrow conclusion:

> The stopped V3.2/V3.3/V3.4 STAR50 precursor route failed in a period where STAR50's own common-volatility state distribution was increasingly outside the 2022–2023 historical support surface, especially in 2025, while the contemporaneous CSI1000 state was mostly in-support and the fine 3s/15s measurement surface was fully available.

This is evidence for **state transport / nonstationarity**, not for a missing-data explanation. It does not make V3.2 valid again and does not establish a causal source of STAR50's state shift.

A useful consequence for the next research stage is methodological: a fixed historical-state calibration can silently become the wrong comparison set even when the high-frequency measurement itself is excellent. Future work on “common environment beyond which one index becomes anomalous” should therefore represent **contemporaneous cross-index common state and time-varying state support explicitly**, rather than only matching STAR50 to a fixed 2022–2023 self-history.

## What remains forbidden

- No retuning of V3.2/V3.3/V3.4 score, K, match dimensions or percentile threshold.
- No claim that 2025 negative results were caused by data quality.
- No snapshot-row-count proxy for trade intensity.
- No 2026 read or fresh-OOS claim.
- No trading/position/production inference.
