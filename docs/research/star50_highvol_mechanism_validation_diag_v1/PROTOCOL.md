# STAR50 HighVol mechanism — reusable Validation diagnostic V1

This diagnostic is allowed under the repository three-pool policy because Validation is reusable and inspectable. It does not query BlackBox.

Purpose: explain why the frozen STAR50 downside regime-break candidate failed Validation and identify **structural relationships**, not select a new Validation-optimized trading rule.

Validation horizon: 2024-01-01 through 2026-08-21.

Use exactly the same HighVol-onset event construction and feature definitions as `star50_highvol_mechanism_dev_v1`:

- direction of recent 5m net;
- preceding non-overlapping 30m trend alignment;
- `tail2_share >= 0.60` acceleration flag;
- `efficiency5 >= 0.60` directional-efficiency flag;
- horizons 1/2/3/5/10 minutes from next-minute open.

Report the same mechanism tables by year and full feature cube. Also produce a direct Development-vs-Validation comparison for each full-cube cell at 3m and 5m, including counts and mean signed continuation.

No parameter is changed in this diagnostic. No candidate is nominated here. Any new candidate hypothesis must return to Development and be frozen separately before another Validation pass.
