# STAR50 directional shock strength Development study V5

Role: Development only, 2021-2023. Validation and BlackBox are not queried.

Base onset condition remains structural rather than V2-specific: prior 30m net >0, recent 5m net <0, recent 5m path efficiency >=0.60 at `NormalVol -> HighVol`.

For the same non-overlapping prior 30 one-minute returns define background RMS `sigma_bg = sqrt(mean(r^2))` and:

`directional_shock_z = -net5_bp / (sigma_bg * sqrt(5))`.

This measures the signed five-minute downside impulse in units of the background standard deviation of a five-minute sum. It is causal and scale-normalized.

Frozen natural thresholds for nomination: `z >= 1.0`, `>=1.5`, `>=2.0`, `>=3.0`. Also report HighVol onset `vol_ratio` bands `<2`, `2-3`, `>=3` as a secondary diagnostic only.

Execution: short next-minute open, hold 3 minutes, same half-session, complete path, non-overlapping. Primary cost 1bp/leg.

Nomination gates are unchanged: pooled >=60 trades; every year >=15; every year net @1bp/leg >0; pooled net >0; pooled one-way break-even >1bp. If none pass, no V5 candidate.

Workflow must physically contain only 2020 warm-up and 2021-2023 STAR50 files.
