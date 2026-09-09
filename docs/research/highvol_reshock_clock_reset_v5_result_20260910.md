# Re-shock clock-reset v5 — retained risk-process evidence

Status: **RECURRENT SHOCK RESETS RECOVERY CLOCK; GENERIC CLUSTER STATE NOT YET SUPPORTED**.

Development-only run `34415064379` used the unchanged HighVol/Unsafe engine on 2021–2023 (2020 warm-up), with no PnL, trading rule, Validation or BlackBox. Artifact `10128736040`, SHA256 `82b5423bdfaa2af5398ccccfbc28bce43a6a25770e3a11c715320dbf0ad679b4`.

STAR50 had 459 initial shock episodes and 72 first recurrent shocks; CSI1000 had 417 and 67. First recurrence was typically early: median 10m for STAR50 and 15m for CSI1000.

The robust finding is a recovery-clock reset. After an initial shock, P(Normal within 15m) was 25.83% STAR50 / 28.54% CSI1000; after the first recurrent shock it fell to 2.78% / 2.99%. At 30m the corresponding change was 26.89%→4.17% and 32.37%→7.46%. These drops held in every Development year for both indices. Median remaining time to Normal after the recurrent shock was again 12 five-minute bars (60m).

Further-shock probability did not define one common cluster state: STAR50 showed slightly lower next-shock probability after recurrence, while CSI1000 was higher pooled but reversed in 2021. Therefore recurrence should not yet be promoted into a universal `CLUSTERED` state.

Next in-scope question: whether recovery calibration is better indexed by **time since most recent shock** rather than only time since episode-start shock.

`production_authority=false`; BlackBox not queried.
