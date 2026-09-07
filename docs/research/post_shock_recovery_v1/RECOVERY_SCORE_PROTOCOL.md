# Continuous post-shock recovery score protocol

Date: 2026-09-07. Purpose: after hard release rules failed, test a continuous `Recovering` risk score instead of tuning another Clean threshold.

Fit pooled 2024 checkpoint rows (+5/+10/+15/+20m), evaluate pooled 2025. Target is `log(next-5-minute RMS / pre-shock sigma)`. Features are exactly the already-registered minute release-model features: checkpoint, trailing5 RMS ratio, trailing5 max ratio, trailing2 RMS ratio, event z, log sigma, quiet-first, index, event-minute 3s top3 share and path efficiency.

Estimator: `StandardScaler + Ridge(alpha=1)`, no tuning.

Baselines:
1. persistence: predict next-5m ratio by current trailing5 ratio;
2. unconditional 2024 training mean log-ratio.

Evaluation on 2025: RMSE in log-ratio, Pearson/Spearman correlation, and tercile monotonicity of realized next-5m ratio. Report both indices descriptively. Do not derive a new hard Clean threshold from 2025.

Consumed-history diagnostic only; no trading or production acceptance.
