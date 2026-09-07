# State sufficiency diagnostic protocol

Date: 2026-09-07. This is a consumed-history diagnostic. It must not change the frozen post-shock state score or reopen Clean.

Question: once a first shock has occurred, does the current five-minute recovery ratio already contain the useful short-horizon state information, or is there stable incremental information in elapsed time / recovery dwell history?

Frozen checkpoint set: +5/+10/+15/+20 minutes after each frozen first-shock event, same half-session only. Current ratio is trailing five completed 1m RMS divided by the event's fixed pre-shock sigma. Outcome is whether the following five-minute ratio is >=1.5 (next Unsafe).

Fixed models, no search:
- M0 `ratio_only`: log(current recovery ratio)
- M1 `plus_elapsed`: M0 + elapsed minutes since the event / 10
- M2 `plus_recovery_age`: M1 + minutes since the latest post-shock Unsafe reading / 10. If no post-shock Unsafe reading occurred after lag 5, the observed first shock at lag 0 is the last Unsafe anchor.

Fit pooled STAR50+CSI1000 2024 only. Evaluate once on pooled 2025 and separately by index as available. Replaying the already-opened 2026-01-05..2026-08-21 snapshot is descriptive consistency only, not another independent confirmation and never a basis for retuning.

Estimation: StandardScaler + logistic regression, C=1, no class weights, max_iter=2000, random_state=20260907. Primary comparison is paired event-cluster bootstrap delta log-loss (challenger minus M0), resampling whole first-shock episodes, 5000 repeats. Also report AUC/Brier/log-loss and within-state early (+5/+10) vs late (+15/+20) next-Unsafe rates.

Interpretation:
- If elapsed/dwell variables do not improve 2025 in a stable direction, retain the simple current recovery ratio as the sufficient operational state score.
- If they do improve, record a duration-dependence candidate only; do not change the frozen state machine until genuinely new data validate it.
- No Clean state, no new thresholds, no window-length change, no trading conclusion.
