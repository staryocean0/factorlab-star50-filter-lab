# Repository data-use policy V2

Effective date: 2026-09-08
Owner directive: replace the one-shot/"consumed data" habit with a stable three-pool research regime.

This document is repository-level governance for future research in this repository. Historical sealed reports remain historical evidence and are not rewritten. Where an older document calls a period "consumed" or says it cannot be reused, this V2 policy supersedes that wording for **future work**. Reuse does not make old results fresh OOS.

## Core principle

Data are not disposable. Every observation belongs to one of three durable roles:

1. **Development pool** — open workbench.
2. **Validation pool** — reusable tuning/diagnostic holdout whose details may be inspected after a candidate is trained.
3. **Black-box validation pool** — reusable blinded holdout queried only through a fixed aggregate interface; its details are never inspected.

A dataset is not "burned" by use. If detailed inspection changes its scientific role, it is reclassified rather than discarded.

## Current assignment

### Warm-up only

- STAR50 pre-2021 history used only where needed to initialize causal filters/rolling state.
- It is not scored as a research evaluation period unless a future protocol explicitly changes that role before analysis.

### Development pool

- `2021-01-01` through `2023-12-31`
- subjects: `000688.SH` and `000852.SH`, subject to actual source coverage.

Allowed:

- feature/target construction;
- model fitting and parameter search;
- strategy design;
- plots and event/path inspection;
- per-day/per-event/per-session attribution;
- falsification and counterexample search;
- repeated reuse without any claim that the period is OOS.

### Validation pool

- `2024-01-01` through `2026-08-21`
- subjects: `000688.SH` and `000852.SH`, subject to actual source coverage.

This pool is **reusable**. It is not a one-shot holdout.

Rules:

- do not include these rows in estimator fitting or parameter estimation for the candidate currently being tested;
- after training/freeze on the development pool, the candidate may be evaluated here;
- after evaluation, detailed inspection is allowed: year/day/event/session/path breakdowns, failure analysis, counterexamples and diagnostics are all permitted;
- findings may guide the next development iteration;
- the same validation data may then be used again for the next candidate;
- once validation results have influenced model/feature/routing design, results on this pool are labelled `validation/tuning evidence`, not fresh OOS.

This role intentionally matches the owner's desired workflow: train on development, validate, open the validation details, learn, iterate, and reuse.

### Black-box validation pool V1

Definition:

- the **first 60 complete trading days strictly after `2026-08-21`** for both research subjects;
- the exact first/last date is frozen by manifest when all 60 complete days are available;
- until that fixed snapshot exists, BlackBox-V1 status is `pending_data`.

The same fixed BlackBox-V1 is intended to be **reused for many candidates**. Repeated use does not by itself reclassify the data as long as detailed contents are never exposed.

## Black-box interface

A black-box candidate must be frozen before query. At minimum record:

- candidate ID;
- research question / primary endpoint;
- code commit SHA;
- parameter/config hash;
- data snapshot/manifest hash;
- pre-registered metrics and acceptance rule.

The black-box evaluator may return only:

- candidate ID and hashes;
- total eligible sample/event count;
- pre-registered aggregate metric(s);
- pre-registered per-symbol metric(s) only if per-symbol evaluation was registered before the first query;
- pass/fail or promote/do-not-promote verdict under the registered rule.

It must **not** return:

- dates or timestamps;
- year/month/week/day breakdowns;
- event/session/half-session rows;
- path charts;
- best/worst examples;
- top contributors;
- error cases;
- feature distributions conditional on outcome;
- threshold sweeps;
- post-hoc metrics not registered before the query;
- any artifact from which the hidden rows can be reconstructed.

## Repeated black-box use

Repeated queries are allowed, with safeguards:

1. Every query is appended to a black-box query ledger with candidate/config/code/data hashes.
2. A candidate must be developed and validation-inspected **without using black-box internals**.
3. Black-box failure may reject a candidate, but it may not tell the researcher how to repair it.
4. After a failure, diagnosis returns to Development + Validation pools. The black-box details remain closed.
5. The next candidate may query the same BlackBox-V1 again after a new freeze.
6. Do not run unregistered threshold/parameter sweeps against the black box.
7. Do not rank a large candidate grid directly on the black box.

Scientific wording:

- the first-ever query of a never-opened black-box snapshot may be described as a one-shot blind OOS check if all other requirements hold;
- subsequent queries against the same snapshot are `reusable blinded black-box checks`, not fresh OOS;
- this distinction prevents false OOS claims while preserving the owner's reusable-black-box workflow.

## If black-box details are accidentally exposed

Do **not** call the data destroyed or burned.

Instead:

- record the exposure;
- reclassify the exposed black-box snapshot as **Validation** from that point forward;
- keep it permanently available for detailed research and tuning;
- create a replacement black-box pool only when a blinded holdout is scientifically needed.

Only the owner may explicitly authorize deliberate black-box unblinding.

## Historical periods already inspected before this policy

Because detailed 2024, 2025 and 2026-through-2026-08-21 results have already been inspected in prior work, they are assigned to the reusable **Validation** pool. They are not retroactively represented as black-box data.

Prior sealed documents may retain labels such as `development`, `consumed`, `repeat audit`, or `not fresh OOS`. Those statements describe the historical protocol used at the time. This V2 policy changes forward data-use governance; it does not rewrite historical evidence or upgrade old claims.

## What each pool is for

- **Development:** invent and fit.
- **Validation:** diagnose, compare, understand failures, and iterate.
- **Black box:** answer only "does the frozen candidate still work under the pre-registered test?"

The black box is a measurement instrument, not a debugging dataset.

## Promotion discipline

A production/live decision is outside this repository's current authority. For research promotion within the repository:

- development evidence may nominate a candidate;
- validation evidence may refine and reject candidates;
- black-box evidence may confirm or reject a frozen candidate without revealing why;
- no single period is declared unusable merely because it has been evaluated.

## Data append policy

New incoming data do not automatically become a new OOS year.

- Until BlackBox-V1 has its fixed first 60 complete trading days, eligible post-2026-08-21 data fill that pending black-box snapshot.
- After BlackBox-V1 is fixed, later data stay unassigned until the owner/research protocol assigns them to Development, Validation, or a future black-box pool.
- Do not silently enlarge BlackBox-V1 after its 60-day manifest is frozen.

## Enforcement

Future research protocols must declare:

- which pool is used for fitting;
- which pool is used for detailed validation;
- whether a black-box query will occur;
- the candidate hash and black-box metrics before the query.

`docs/governance/data_usage_declaration.json` is the machine-readable current assignment. `scripts/validate_data_usage_policy.py` checks the declaration and repository invariants.
