# HighVol Router V1 — stability qualification

Historical status: **PRIMARY-COST EDGE POSITIVE WITH MATERIAL STABILITY FRAGILITY**.

Dedicated audit run `34346275786`; artifact `10101828676`; ZIP SHA256 `730af4ad3667698ae106b1c49795ae664b07558de96ff73ab1a290ac46acca5a`.

Frozen trade identity was preserved: Development 104 trades, Validation 129 trades. Candidate/routing changes: none. BlackBox queried: false.

Main historical findings:

- Validation mean net at 1 bp/leg: `+0.546255 bp/trade`.
- one-way break-even: `1.273128 bp/leg`.
- at 1.5 bp/leg: `-0.453745 bp/trade`.
- day-block bootstrap 95% interval: `[-1.985521,+3.058996] bp/trade`; P(mean>0) `67.04%`.
- removing top 3 positive days: `-0.283332 bp/trade`; top 5: `-0.750981`.
- leave-one-year-out estimates remained positive, while 2026 through 08-21 was slightly negative.

Interpretation at the time: reusable Validation PASS retained, but production-quality stability not established.

## Scope-repair status

This audit is now archived payoff evidence. It does not authorize new payoff tuning in STAR50 Filter after the 2026-09-09 bucket scope repair.

`production_authority=false`.
