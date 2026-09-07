# Recovery-duration censoring correction

Date: 2026-09-07.

The first descriptive pass computed medians only among events with an observed release-start. That is biased downward because events near the end of a half-session, or events that never meet the release rule before the boundary, are right-censored.

Before promoting any duration number, recompute the release-start distribution with a Kaplan-Meier estimator. For observed releases, event time is the release-start lag. For unreleased cases, censor at the largest lag for which two future 5-minute blocks could still have been evaluated. Report KM median when estimable, KM release probability by 5/10/15/30 minutes, and the raw censor fraction. Keep the naive uncensored median only as an audit field, not the main duration estimate.

This correction does not change the event universe, thresholds, release rule, or any causal release-model result.
