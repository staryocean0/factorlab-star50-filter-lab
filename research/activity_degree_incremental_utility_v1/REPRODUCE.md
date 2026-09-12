# Reproduce Activity-degree incremental utility V1

The completed scientific run is already sealed. Normal repository use should **not** rerun reusable Validation merely because documentation changed.

The workflow `.github/workflows/activity-degree-incremental-utility-v1.yml` is therefore `workflow_dispatch` only.

## Decisive frozen execution

- run: `34670357953`
- Development fit/freeze job: `103490442493`
- reusable Validation job: `103490604669`
- head: `5fa76723d5142b96d53822343faad6bd046f9df6`
- frozen model SHA256: `89660f0825373b5afd8d1d9c51642424fe79fae925f44d0f25a6f2f96ca78d8d`
- Validation artifact: `10290917834`

Exact outputs from that artifact are preserved in `evidence/` and protected by its original `SHA256SUMS.txt`.

## If explicit re-execution is scientifically justified

Dispatch the workflow manually from a commit that keeps the frozen protocol and runner unchanged. The workflow enforces:

1. fit workspace contains only 2020 warm-up and 2021–2023 Development inputs;
2. repository V2 data-usage validator passes;
3. protocol Git blob is `1972c0c5ab832e4b6e04e911cc7cebdfa21b1689`;
4. unit/causal invariants pass;
5. C/A/N probes are fit and written to a frozen artifact before Validation starts;
6. Validation job verifies the exact frozen-model SHA from the preceding job;
7. Validation workspace contains 2024–2025 but no 2026/BlackBox carrier;
8. final receipt must state reusable Validation, not fresh OOS.

A rerun is a reproducibility check, not a new independent Validation claim. Do not use reruns to change thresholds, M3 bands, the 30bp surface, ridge penalty, horizon, lagged control, sample gates or bootstrap family.

No PnL, router, BlackBox detail or production authorization is part of reproduction.
