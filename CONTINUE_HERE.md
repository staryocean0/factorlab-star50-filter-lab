# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `research/v19_residual_failure_audit/RESULTS.md`
3. `research/v19_residual_failure_audit/DECISIVE_RECEIPT.json`
4. `research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md`
5. `research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json`
6. `research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json`
7. `research/highvol_risk_episode_state_machine_v19/DEVELOPMENT_RESULTS.md`
8. `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md`
9. `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`
10. `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
11. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
12. `docs/governance/DATA_USAGE_POLICY_V2.md`
13. `docs/governance/data_usage_declaration.json`
14. `docs/governance/blackbox_query_ledger.json`
15. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

The integrated V19 causal realtime risk-episode state machine is reusable-Validation supported on existing 2024-2025 3s coverage, and its residual failure path has now been audited and closed.

Current decisive state:

`V19_VALIDATED_RESIDUAL_PATH_CLOSED_NO_V20`

Frozen V19 primary rule at exactly E-15s:

1. frozen V9 partial `UNSAFE` or `RECOVERING` is emitted immediately;
2. if partial state is `NORMAL` while the previous completed 5m state remains `UNSAFE` or `RECOVERING`, retain that previous risk state until bar close;
3. otherwise emit `NORMAL`.

There is no fitted persistence length and no post-hoc checkpoint selection.

## V19 reusable Validation authority

- execution commit `b4527e2f431f5dfb2ef801f262d39f509253820f`;
- run `34612330970`;
- job `103305638445`;
- artifact `10268853374`;
- artifact SHA256 `5989514df544ffc26c0559a185829f5c027df954a311dd9a43f3f0c9912238af`;
- frozen V19 runner blob `ee2fce299d5ee21abf1ab2c2c5183bac101ae822`;
- Validation years `2024-2025` only;
- E-15s evaluable checkpoints `45,590`;
- pooled precision `0.9945937090`;
- pooled recall `0.9892455597`;
- pooled FPR `0.0008364383`;
- exact three-state agreement `0.9963149814`;
- reference episodes `542`;
- episode capture `0.9981549815`;
- fragmentation `0.0018450185`;
- `full_validation_supported=true`.

## Residual audit closure

Diagnostic audit authority:

- successful execution commit `a066a64ee22cf6e23911f5bccc1a90eafe2de9e4`;
- run `34614008432`;
- job `103311278481`;
- artifact `10270156874`;
- artifact SHA256 `b49c61d8b2345e0441c69fa7d94d25bf9425d572d13953e40e83aede72f4d0fb`.

The first audit run `34613545773` produced no scientific output because of an implementation-only pandas dtype error. The rerun changed only temporary column dtype handling; the scientific protocol and decision rule were unchanged.

The audit found:

- 66 Validation risk FNs: all final `NORMAL -> UNSAFE` shocks still below 3σ at E-15; 48 form by E-6, 16 by E-3, 2 later/by close;
- 33 Validation risk FPs: all transient E-15 partial shocks that finish `NORMAL`; 27 resolve by E-6, 6 by E-3;
- all 99 binary risk errors are exhausted by these mirror-image threshold-timing effects;
- 69 `UNSAFE/RECOVERING` mismatches are only `0.00151349` of Validation checkpoints, and 62/69 converge by E-3;
- the single uncaptured episode and single fragmented episode are tied to FN timing;
- all 28 false machine episodes are one-checkpoint transients, resolving by E-6 or E-3;
- Development 2021-2023 reproduces the same residual structure.

Mathematical decision:

`NO_V20_FROM_V19_RESIDUALS`

Do **not** start V20 to optimize these errors. Such an attempt would require moving the validated 3σ threshold, moving the product checkpoint after inspection, or fitting new features/persistence rules on already-consumed Validation data. There is also no fresh authorized realtime 3s holdout after 2025 for clean validation of such a model.

A future version requires a qualitatively new causal question or genuinely new independent realtime data.

## Existing validated component authorities

V18 remains the validated E-15s entry-side switch-on component on 2024-2025 3s coverage.

V17 remains the validated E-15s realtime recovery component on 2024-2025 3s coverage, transferring frozen V16 without refit.

V16 remains the validated final-5m recovery authority through `2026-08-21`:

- 15m/30m = state + recent-shock age;
- 60m = recent-shock age only.

## Do not reopen

Do not rerun/refit V11-V19 merely to reconfirm them. Do not alter V19 E-15s, V9 thresholds, V18 switch-on, V16/V17 recovery probabilities, or close-confirmed-exit semantics.

Do not choose E-6s/E-3s post hoc, introduce a tuned persistence length, or use 2024-2025 again as a fresh realtime holdout.

Do not synthesize 2026 3s coverage or query BlackBox merely to improve current metrics.

## Data-use regime

- Development: 2021-2023;
- reusable 5m Validation: through 2026-08-21 under frozen protocols;
- realtime 3s reusable Validation: 2024-2025 only;
- BlackBox-V1: separate protected aggregate-only regime.

`v19_validation_queried=true`.
`v19_residual_audit_completed=true`.
`v20_started=false`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
