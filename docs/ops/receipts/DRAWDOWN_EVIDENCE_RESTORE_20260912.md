# Drawdown evidence restore receipt — 2026-09-12

The generic `execution-audit` surfaced a pre-existing current-tree integrity defect: `artifacts/drawdown_conditions/bundle_manifest.json` referenced six sealed documents under `docs/research/drawdown_conditions/`, but that directory was absent from the current tree.

The six documents were restored **byte-for-byte by reusing their existing Git blobs** from branch `research/drawdown-conditions-20260905`; they were not regenerated or edited:

- `attribution_review.md` — blob `feae35d1ab2917cb3bfa0a37457f7ec63dccf894`
- `data_usage.json` — blob `5a6cbe8440ac06273ce7cb191b4cfb4e76f0ecb2`
- `report.md` — blob `14432a0d4e5d3d93bfd024495f95757d32a3d14a`
- `risk_preregistration.json` — blob `6cb78030596baf96af90e3631788edd6b981d315`
- `whitepaper.md` — blob `513ca7bb7b26ca71dcb6c308dfe9a8fff9138ac6`
- `workflow.md` — blob `a5ffb7ed4b9f54e2415cd81f3d1a657a458250b2`

Restore commit: `b511b0e1bea13fa963989046962713919593557d`.

Reason: preserve historical evidence and satisfy the existing sealed manifest rather than weakening or deleting manifest checks. No scientific result, model, parameter, dataset role, or production authority is changed.
