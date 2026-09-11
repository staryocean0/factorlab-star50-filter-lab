# Continue here — STAR50 / CSI1000 K-line risk-state bucket

## Read first

1. `CURRENT_RESEARCH.md`
2. `research/highvol_risk_episode_state_machine_v19/DEVELOPMENT_RESULTS.md`
3. `research/highvol_risk_episode_state_machine_v19/DECISIVE_RECEIPT.json`
4. `research/highvol_risk_episode_state_machine_v19/PROTOCOL.md`
5. `research/highvol_risk_episode_state_machine_v19/FROZEN_DEVELOPMENT_CONTRACT.json`
6. `research/highvol_unsafe_switch_on_v18_validation/VALIDATION_RESULTS.md`
7. `research/highvol_unsafe_switch_on_v18_validation/DECISIVE_RECEIPT.json`
8. `research/highvol_realtime_horizon_adaptive_v17_validation/VALIDATION_RESULTS.md`
9. `research/highvol_realtime_horizon_adaptive_v17_validation/DECISIVE_RECEIPT.json`
10. `research/highvol_horizon_adaptive_v16/FROZEN_HORIZON_ADAPTIVE_SURFACE.json`
11. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`
12. `docs/governance/DATA_USAGE_POLICY_V2.md`
13. `docs/governance/data_usage_declaration.json`
14. `docs/governance/blackbox_query_ledger.json`
15. `AGENTS.md`

Then run:

`python scripts/validate_data_usage_policy.py`

## Current breakpoint

V19 causal realtime risk-episode state machine has completed **Development only** and passed every preregistered gate.

Current decisive state:

`V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_DEVELOPMENT_SUPPORTED_VALIDATION_NOT_AUTHORIZED`

Frozen V19 primary rule at exactly E-15s:

1. frozen V9 partial `UNSAFE` or `RECOVERING` is emitted immediately;
2. if partial state is `NORMAL` while the previous completed 5m state is still `UNSAFE` or `RECOVERING`, retain that previous risk state until the bar closes;
3. otherwise emit `NORMAL`.

There is no fitted persistence length. The rule is the deterministic close-confirmed-exit semantics already implied by V17's frozen `provisional_normal = unavailable` gating.

Development authority:

- branch `research/highvol-risk-episode-state-machine-v19-20260911`;
- execution commit `6fad49e5dc674d9a48b5c1719e060eceabc166d2`;
- run `34611126345`;
- job `103301597623`;
- artifact `10267923594`;
- artifact SHA256 `3d64999976ca5ad001e7924aa4d6e668e412411e58e1bb10daebb747f4ee5aea`;
- Development 3s years `2021-2023` only;
- E-15s evaluable checkpoints `68,338`;
- pooled risk precision `0.9968622529`;
- pooled risk recall `0.9914698845`;
- pooled FPR `0.0005108557`;
- exact three-state agreement `0.9975123650`.

Raw frozen V9 partial-state diagnostic comparator had risk recall `0.9027358785`. The close-confirmed rule therefore removes the dominant premature-safe discontinuity without tuning a new threshold or persistence window.

Episode-level Development:

- reference episodes `867`;
- machine episodes `890`;
- capture `861 / 867 = 0.9930795848`;
- fragmented reference episodes `0`;
- false machine-episode rate `0.0325842697`;
- same-checkpoint onset rate `0.9054209919`;
- onset-lag median `0` checkpoints;
- maximum onset lag among captured episodes `1` checkpoint.

Transition continuity at E-15s:

- `NORMAL -> UNSAFE`: recall `0.9063926941`;
- `RECOVERING -> UNSAFE`: recall `0.9546391753`;
- `UNSAFE -> RECOVERING`: recall `0.9872379216`;
- close-confirmed exit rows: `853`;
- V19 premature `NORMAL`: `0 / 853`;
- raw partial state was already `NORMAL` on `844 / 853` of those exit rows.

Frozen V16/V17 recovery attachment remains intact: `7,716` probability rows were scored, every curve obeyed `p15 <= p30 <= p60`, and the 60m age-only anchor matched exactly (`max_abs_diff=0.0`).

Exact upstream identities are frozen:

- V9 runner blob `ae2a7e095df58692ef9df0dfee5856cac727ca44`;
- V18 runner blob `62c207badff1c3e37cbb1a8e17ef89feeea611d8`;
- V17 runner blob `397d80037806ba11cadf7f77717d36d55fbafc91`;
- V16 surface blob `1f88966cf5dd3fb102f0d75746d5d00434555647`.

The decisive receipt says:

`FREEZE_V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_AND_STOP_BEFORE_VALIDATION`

Therefore **do not run V19 reusable Validation without separate authorization**. `v19_validation_queried=false`.

## Existing validated component authorities

V18 remains the validated entry-side switch-on component on 2024-2025 3s coverage:

- E-15s precision `0.9511228534`;
- recall `0.8888888889`;
- FPR `0.0008608054`;
- `full_validation_supported=true`.

V17 remains the validated E-15s realtime recovery component on 2024-2025 3s coverage, transferring the frozen V16 multi-horizon recovery surface without refit.

V16 remains the validated final-5m recovery authority through `2026-08-21`:

- 15m/30m = state + recent-shock age;
- 60m = recent-shock age only.

The integrated V19 state machine itself has **Development support only** until a separately authorized reusable Validation is completed.

## Do not reopen

Do not rerun/refit V11-V18 merely to reconfirm them. Do not alter V19's E-15s checkpoint, close-confirmed-exit semantics, upstream V9 thresholds, V18 switch-on rule, or V16/V17 probability surface after seeing Development.

Do not switch to raw partial state as the primary V19 object after seeing the comparison. Do not choose E-6s/E-3s post hoc. Do not introduce a tuned persistence length.

Do not query 2024+ 3s for V19 until reusable Validation is separately authorized. Do not synthesize/fabricate 2026 3s coverage, inspect protected post-2026-08-21 data, or query BlackBox.

## Current research question

This bucket studies **when K-line conditions causally justify entering, staying in, or leaving a risk state**. The output is a risk-state annotation/state machine, not a directional payoff strategy.

## Data-use regime

- Development: 2021-01-01 through 2023-12-31;
- reusable 5m Validation: 2024-01-01 through 2026-08-21 when separately authorized;
- realtime 3s Validation coverage: 2024-2025 only when separately authorized;
- BlackBox-V1: protected post-cutoff aggregate-only regime under its frozen protocol.

`v19_validation_queried=false`.
`queried_post_2023_3s_for_v19=false`.
`queried_2026_3s=false`.
`blackbox_queried=false`.
`pnl_computed=false`.
`production_authority=false`.
