# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md`
3. `research/highvol_risk_episode_state_machine_v19_validation/DECISIVE_RECEIPT.json`
4. `research/highvol_risk_episode_state_machine_v19_validation/FROZEN_VALIDATION_CONTRACT.json`
5. `research/highvol_risk_episode_state_machine_v19/DEVELOPMENT_RESULTS.md`
6. `research/highvol_risk_episode_state_machine_v19/DECISIVE_RECEIPT.json`
7. `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md`
8. `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`
9. `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
10. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
11. `docs/governance/DATA_USAGE_POLICY_V2.md`
12. `docs/governance/data_usage_declaration.json`
13. `docs/governance/blackbox_query_ledger.json`
14. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

V19 causal realtime risk-episode state machine has completed Development and reusable Validation.

Current decisive state:

`V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_REUSABLE_VALIDATION_SUPPORTED_2024_2025`

Frozen V19 primary rule at exactly E-15s:

1. frozen V9 partial `UNSAFE` or `RECOVERING` is emitted immediately;
2. if partial state is `NORMAL` while the previous completed 5m state remains `UNSAFE` or `RECOVERING`, retain that previous risk state until the bar closes;
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
- queried 3s years `[2024, 2025]` only;
- E-15s evaluable checkpoints `45,590`;
- pooled risk precision `0.9945937090`;
- pooled risk recall `0.9892455597`;
- pooled FPR `0.0008364383`;
- exact three-state agreement `0.9963149814`;
- `full_validation_supported=true`.

Raw frozen V9 E-15s partial-state comparator had risk recall `0.9023953072`. The close-confirmed rule remains the validated continuity mechanism.

Episode-level Validation:

- reference episodes `542`;
- machine episodes `570`;
- capture `541 / 542 = 0.9981549815`;
- fragmented reference episodes `1`;
- fragmentation rate `0.0018450185`;
- false machine-episode rate `0.0491228070`;
- same-checkpoint onset rate `0.8800738007`;
- onset-lag median `0` checkpoints;
- maximum onset lag among captured episodes `1` checkpoint.

Transition continuity at E-15s:

- `NORMAL -> UNSAFE`: recall `0.880000`;
- `RECOVERING -> UNSAFE`: recall `0.907692`;
- `UNSAFE -> RECOVERING`: recall `0.962236`;
- close-confirmed exit rows `520`;
- V19 premature `NORMAL`: `0 / 520`;
- raw partial state was already `NORMAL` on `514 / 520` exit rows.

Frozen V16/V17 recovery attachment remains intact: `4,944` probability rows were scored, every curve obeyed `p15 <= p30 <= p60`, and the 60m age-only anchor matched exactly (`max_abs_diff=0.0`).

## Existing validated component authorities

V18 remains the validated entry-side switch-on component on 2024-2025 3s coverage:

- E-15s precision `0.9511228534`;
- recall `0.8888888889`;
- FPR `0.0008608054`;
- `full_validation_supported=true`.

V17 remains the validated E-15s realtime recovery component on 2024-2025 3s coverage, transferring frozen V16 without refit.

V16 remains the validated final-5m recovery authority through `2026-08-21`:

- 15m/30m = state + recent-shock age;
- 60m = recent-shock age only.

## Do not reopen

Do not rerun/refit V11-V19 merely to reconfirm them. Do not alter V19's E-15s checkpoint, close-confirmed-exit semantics, upstream V9 thresholds, V18 switch-on rule, or V16/V17 probability surface after Validation.

Do not replace V19 with raw partial state, choose E-6s/E-3s post hoc, or introduce a tuned persistence length.

Do not synthesize/fabricate 2026 3s coverage, inspect protected post-2026-08-21 data, or query BlackBox merely to reconfirm current authority.

## Current research question

This bucket studies **when K-line conditions causally justify entering, staying in, or leaving a risk state**. The output is a risk-state annotation/state machine, not a directional payoff strategy.

## Data-use regime

- Development: 2021-01-01 through 2023-12-31;
- reusable 5m Validation: 2024-01-01 through 2026-08-21 under frozen protocols;
- realtime 3s reusable Validation coverage: 2024-2025 only;
- BlackBox-V1: protected post-cutoff aggregate-only regime under its frozen protocol.

No V20 protocol has been started.

`v19_validation_queried=true`.
`queried_3s_years_for_v19=[2024,2025]`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
