# Execution-audit evidence restore receipt — 2026-09-12

The generic `execution-audit` validator exposed a second pre-existing current-tree integrity defect: sealed execution-audit receipts require `docs/research/execution_counterexamples/`, but that historical evidence directory was absent from the current tree.

Seven documents were restored byte-for-byte by reusing their existing Git blobs from completed execution-audit commit `75cf370e12f8bc1521d917fb6e8f55afa5c13d1f` / later preserved commit `0983ea4be9dcbb521f9f07be010039e1de021e10`:

- `clock_amendment.json` — blob `5ebaa01323b2d219107bd1a7bf0fed10da0950ff`
- `preregistration.json` — blob `68711919d12df16e676c440d0d59cf2a00b62e1b`
- `repair_amendment.json` — blob `2355f4701d3f7721aab30278989bacf84187c6e1`
- `report.md` — blob `37ed7b0265e6a155658210b74f87ef85ba49959a`
- `review_erratum.json` — blob `e7d49985b46b94138fb2872e5de71858766c2419`
- `whitepaper.md` — blob `8e79e922951a7b8aaae7da3d180d34f2232711f3`
- `workflow.md` — blob `c5358233003c76b3c016ebde98c01d8ab8385fe8`

Restore commit: `44e7ccdd3b68caaddeaf56184667aa8761a26036`.

This restores immutable historical evidence instead of weakening the validator. No policy, scientific result, model, data role, BlackBox status, PnL result, or production authority is changed.
