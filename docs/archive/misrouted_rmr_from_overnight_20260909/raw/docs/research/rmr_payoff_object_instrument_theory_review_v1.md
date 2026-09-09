# RMR payoff-object / instrument-theory review v1

## Status

This is a results-blind research boundary document.

No empirical candidate is authorized.
No BLACKBOX access is authorized.
`production_authority = false`.

## Motivation

Certified R1 and R2 mechanisms establish restoration probability structure:

- R1: intact trend parent + lower-scale counter-move increases recovery probability.
- R2: intact range parent + attempted boundary break increases re-entry probability.

The mechanism-to-execution diagnostic established that these probabilities did not translate into the tested index-level next-minute execution family.

The current research question is therefore not:

"How can the signal be tuned?"

It is:

"Is the observed restoration mechanism attached to a different economic payoff object than the tested execution representation?"

## Prohibited transformations

This review does not authorize:

- R1 economic v4;
- R2 economic v2;
- router v2;
- probability filtering;
- horizon selection;
- entry delay search;
- stop/target search;
- cost search;
- scale search;
- BLACKBOX queries.

## Allowed theory questions

### 1. Execution timing theory

Question:

Does restoration occur through a path-dependent process whose economic realization is not represented by immediate next-minute index exposure?

Requirement:

Any future test must define an independent causal timing theory before measurement.

### 2. Instrument mapping theory

Question:

Does the payoff geometry of another instrument better represent restoration convexity, path dependency, or delayed normalization?

Requirement:

Before any empirical study, define:

- instrument source;
- spread assumptions;
- basis treatment;
- carry treatment;
- liquidity assumptions;
- convexity/premium assumptions;
- execution convention.

### 3. Stop economic translation

If no independent payoff theory exists, economic conversion should stop.

## Governance

Any future program must first pass theory review before opening DEV data.

VALIDATION and BLACKBOX remain governed by existing three-role policy.
