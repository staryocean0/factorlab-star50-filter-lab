# STAR50 ongoing-HighVol sign-flip V15 — Development only

## Question

All onset-centered STAR50 routers V7–V14 failed to produce a stable cost-covering 3-minute module. V15 changes the event itself: while HighVol is already active, does a reversal in the latest-5-minute net direction mark a genuine short-horizon regime switch?

## Fixed event

Instrument: `000688.SH`.

Within one half-session, at minute `t`:

- state at `t-1` is `HighVol`;
- state at `t` is `HighVol`;
- latest-five-minute net close-to-close return at `t-1` has a non-zero sign;
- latest-five-minute net close-to-close return at `t` has the opposite sign.

Fixed event types:

- `UpToDown`
- `DownToUp`

No magnitude or age threshold is added.

## Execution diagnostic

Direction reference = the **new** latest-5-minute direction after the flip.

- enter next-minute open;
- fixed 3-minute hold;
- same half-session;
- full valid path;
- non-overlapping accepted events.

Report continuation of the new direction and reversal back toward the old direction for 2021/2022/2023 and pooled.

A view is `mechanism_promising` only if every Development year has at least 15 events and either continuation or reversal is positive after 1 bp per leg in all three years. No candidate is automatically nominated.

Development 2021–2023 only; 2020 warm-up allowed; Validation and BlackBox are not queried.
