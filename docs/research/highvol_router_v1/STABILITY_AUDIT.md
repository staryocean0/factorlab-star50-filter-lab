# HighVol Router V1 — stability qualification

Status: **PRIMARY-COST EDGE POSITIVE WITH MATERIAL STABILITY FRAGILITY**.

This diagnostic does not reverse the frozen reusable Validation PASS. It limits the strength of the claim: Router V1 is Validation-supported as a research candidate at the primary 1 bp/leg cost, but current evidence is not sufficient for a production-quality stability claim.

Dedicated audit run `34346275786` succeeded; artifact `10101828676`, ZIP SHA256 `730af4ad3667698ae106b1c49795ae664b07558de96ff73ab1a290ac46acca5a`. Exact frozen trade identity was preserved: Development 104 trades, Validation 129 trades. Candidate/routing changes: none. BlackBox queried: false.

## Main findings

- Validation mean net at 1 bp/leg: **+0.546255 bp/trade**.
- Validation one-way break-even: **1.273128 bp/leg**.
- At 1.5 bp/leg, Validation mean net becomes **-0.453745 bp/trade**.
- Day-block bootstrap, 10,000 draws, seed 20260909: mean +0.553690; 95% percentile interval **[-1.985521, +3.058996] bp/trade**; P(mean net > 0) = **67.04%**.
- Removing the single strongest positive day leaves +0.239567 bp/trade, but removing the top 3 positive days leaves **-0.283332**, and removing the top 5 leaves **-0.750981**.
- Leave-one-year-out Validation estimates remain positive: exclude 2024 +0.812310; exclude 2025 +0.120677; exclude 2026 +0.687904 bp/trade.
- 2026 through 2026-08-21 remains slightly negative at -0.142671 bp/trade.

All four pre-fixed fragility flags triggered: bootstrap interval crosses zero; 1.5 bp/leg stress is negative; top-5-day removal is negative; 2026 slice is negative.

Interpretation: the realized edge is not merely a single-year artifact, but its economic margin is narrow and its pooled profitability is materially dependent on episodic strong days. Do not rescue or improve Router V1 by changing thresholds, hold, confirmation, stops, sizing, or censoring dates. Any materially different payoff rule is a new candidate and must return to Development.

`production_authority=false`. BlackBox query count remains zero.
