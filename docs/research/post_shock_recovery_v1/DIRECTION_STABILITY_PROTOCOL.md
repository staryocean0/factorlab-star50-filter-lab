# Shock-direction stability protocol

Date: 2026-09-07. Consumed-history diagnostic; no state tuning.

Question: after a first shock has occurred, does the sign of that shock (up/down) add stable predictive information about the next five-minute Unsafe outcome beyond the current recovery ratio?

Fixed checkpoints: +5/+10/+15/+20 minutes. Current score remains trailing completed-5m RMS / fixed pre-shock sigma. Outcome remains next-five-minute ratio >=1.5.

Fixed models, no search:
- M0 `ratio_only`: log(current recovery ratio)
- M1 `plus_direction`: M0 + event direction (+1 up, -1 down)
- M2 `plus_interaction`: M1 + log(current ratio) * direction

Fit pooled STAR50+CSI1000 2024 only; evaluate once on 2025. Replay 2026 descriptively only. StandardScaler + logistic regression, C=1, no class weights, max_iter=2000, seed 20260907. Primary comparison is paired event-cluster bootstrap delta log-loss versus M0, 5000 repeats.

If direction does not improve 2025 stably, keep the state machine direction-agnostic. If it does, record a candidate only; no threshold/state change without new independent data.

No Clean promotion, no event/window/threshold search, no trading conclusion.
