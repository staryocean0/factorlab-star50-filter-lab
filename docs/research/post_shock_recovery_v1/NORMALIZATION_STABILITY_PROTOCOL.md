# Recovery-ratio normalization stability protocol

Date: 2026-09-07. Consumed-history diagnostic; no change to the frozen 1.5 state boundary.

Question: after dividing post-shock activity by the fixed pre-shock `sigma_pre`, does background volatility still add stable predictive information about the next five-minute Unsafe outcome?

Fixed checkpoints: +5/+10/+15/+20 minutes after frozen first-shock events. Current score remains trailing completed-5m RMS / sigma_pre. Outcome remains next-five-minute ratio >=1.5.

Fixed models, no search:
- M0 `ratio_only`: log(current recovery ratio)
- M1 `plus_background`: M0 + log(sigma_pre)
- M2 `plus_interaction`: M1 + log(current ratio) * log(sigma_pre)

Fit pooled STAR50+CSI1000 2024 only; evaluate once on 2025. Replay the already-opened 2026 snapshot descriptively only. Estimation is StandardScaler + logistic regression, C=1, no class weights, max_iter=2000, seed 20260907.

Primary comparison: paired first-shock-event cluster bootstrap delta log-loss versus M0, 5000 repeats. For interpretation only, define background-volatility tertiles from 2024 log(sigma_pre) and apply the frozen cuts to 2025/2026 state-band summaries.

If M1/M2 do not improve 2025 stably, retain the simple normalized ratio and do not add background-regime state. If they do improve, record an incomplete-normalization candidate only; do not retune thresholds without new independent data.

No Clean promotion, no threshold/window/event search, no trading conclusion.
