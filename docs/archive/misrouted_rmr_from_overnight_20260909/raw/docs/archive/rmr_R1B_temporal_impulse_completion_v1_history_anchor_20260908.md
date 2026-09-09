# R1_B temporal impulse completion v1 history anchor — 2026-09-08

Identity: `rmr_R1B_temporal_impulse_completion_v1`

Status: **closed on DEV; VALIDATION never opened**.

## Scientific contract

The candidate treated a certified R1_B event as the start of a new parent-aligned S2 restoration impulse and exited only when that subsequent S2 wave was causally confirmed, unless the original S3 structural failure boundary was crossed first. Entry remained the next observed 1m close; S2/S3 thresholds, 10bp cost and 1200-bar safety horizon were inherited without search.

The preregistered DEV gate required positive pooled mean net, improvement over the original structural-first-passage baseline, positive pooled median net, and positive annual mean net in at least 4 of 6 DEV years.

## Reproducibility anchor

Full implementation tree and exact one-time workflow are preserved at commit:

`a0801a7905f96b8bf7f075fe60a4a4d20052ef53`

That tree contains:

- `docs/research/rmr_R1B_temporal_execution_theory_program_review_20260908.md`;
- `docs/governance/reversal_mean_reversion_R1B_temporal_impulse_completion_dev_protocol_v1.json`;
- `scripts/run_rmr_R1B_temporal_impulse_completion_dev_v1.py`;
- `tests/test_rmr_R1B_temporal_impulse_completion_dev_v1.py`;
- `.github/workflows/r1b-temporal-impulse-dev-v1.yml`.

GitHub Actions execution:

- run: `34229441615`;
- job: `102071584287`;
- conclusion: `success`;
- tests: `7 passed`;
- artifact ID: `10057144842`;
- artifact ZIP SHA256: `523d566b4ec2e8565fb4a6a7b4cacaa5ffe6c1fd8330886ed197c9a85415fa7c`.

## Decisive result

The candidate produced positive pooled mean net (`+10.59bp`) and positive mean net in 5 of 6 DEV years, but pooled median net was `-32.11bp` with a `37.10%` win rate. The frozen median gate failed, so the identity closed before VALIDATION.

Current decisive evidence:

- `docs/research/rmr_R1B_temporal_impulse_completion_DEV_decisive_receipt_20260908.json`;
- `docs/research/rmr_R1B_temporal_impulse_completion_DEV_adjudication_20260908.md`.

No VALIDATION or BLACKBOX detail exists for this identity.
