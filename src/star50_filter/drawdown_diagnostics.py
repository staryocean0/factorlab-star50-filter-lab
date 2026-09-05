"""Drawdown accounting and order-exchangeability references.

Inputs are one-dimensional log returns. NAV index 0 is the initial capital of
1, and return index i is earned between NAV indices i and i + 1. Indexes do not
reset at year boundaries. Drawdowns are positive fractions, not percentages.

The permutation reference is descriptive: it conditions on the realized daily
returns and changes their order. It neither establishes a causal mechanism nor
proves that losses are non-random. Daily observations cannot measure intraday
bar-level maximum drawdown. Fixed blocks retain order inside each block, but
their boundaries are arbitrary and their lengths can affect the reference.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np


# Treat numerically equal wealth levels as recovery after a log/exp round trip.
_LOG_NAV_TOLERANCE = 1e-12
_METRICS = (
    "mdd",
    "longest_underwater_observations",
    "longest_peak_to_recovery_or_end_observations",
)


def _validate_returns(log_returns: Iterable[float] | np.ndarray) -> np.ndarray:
    values = np.asarray(log_returns, dtype=float)
    if values.ndim != 1:
        raise ValueError("log_returns must be one-dimensional")
    if not np.all(np.isfinite(values)):
        raise ValueError("log_returns must contain only finite values")
    return values


def _log_nav(values: np.ndarray) -> np.ndarray:
    with np.errstate(over="ignore", invalid="ignore"):
        log_nav = np.concatenate(([0.0], np.cumsum(values)))
    if not np.all(np.isfinite(log_nav)):
        raise ValueError("cumulative log returns exceed floating-point range")
    return log_nav


def log_returns_to_nav(log_returns: Iterable[float] | np.ndarray) -> np.ndarray:
    """Return n + 1 wealth levels, including initial NAV 1 before any return."""
    with np.errstate(over="ignore", under="ignore"):
        nav = np.exp(_log_nav(_validate_returns(log_returns)))
    if not np.all(np.isfinite(nav)) or np.any(nav <= 0):
        raise ValueError("NAV exceeds positive finite floating-point range")
    return nav


def _accounting(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    log_nav = _log_nav(values)
    log_drawdown = log_nav - np.maximum.accumulate(log_nav)
    underwater = log_drawdown < -_LOG_NAV_TOLERANCE
    # Tiny log/exp roundoff is not an underwater episode or a drawdown.
    log_drawdown[~underwater] = 0.0
    edges = np.diff(np.concatenate(([False], underwater, [False])).astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)  # recovery index, or len(log_nav)
    return log_drawdown, starts, stops


def _metrics(
    log_drawdown: np.ndarray, starts: np.ndarray, stops: np.ndarray
) -> dict[str, float | int]:
    underwater_lengths = stops - starts
    # Recovered episodes include the interval ending at recovery; open episodes
    # stop at the last observed NAV and are right-censored there.
    episode_spans = np.minimum(stops, len(log_drawdown) - 1) - (starts - 1)
    return {
        "mdd": float(-np.expm1(np.min(log_drawdown))),
        "longest_underwater_observations": int(
            np.max(underwater_lengths, initial=0)
        ),
        "longest_peak_to_recovery_or_end_observations": int(
            np.max(episode_spans, initial=0)
        ),
    }


def drawdown_summary(
    log_returns: Iterable[float] | np.ndarray, top_n: int = 10
) -> dict:
    """Summarize drawdowns across the complete path without calendar resets.

    ``underwater_observations`` counts observations strictly below the previous
    high. ``peak_to_recovery_or_end_observations`` counts sampling intervals
    from the last peak to recovery, or the last NAV if still unrecovered. Open
    episode durations are lower bounds on their eventual recovery durations.
    No interpretation as calendar days is implied by these observation counts.

    Episode indexes refer to the n + 1 NAV array. ``recovery_index`` is None for
    an open episode; otherwise it is the first observed NAV at or above its
    peak (within 1e-12 log-NAV numerical tolerance). Tied troughs use the first
    occurrence. Episodes are ranked by depth, then peak index.
    """
    if isinstance(top_n, bool) or not isinstance(top_n, (int, np.integer)) or top_n < 0:
        raise ValueError("top_n must be a nonnegative integer")
    values = _validate_returns(log_returns)
    log_drawdown, starts, stops = _accounting(values)
    episodes = []
    for start, stop in zip(starts, stops):
        peak = int(start - 1)
        trough = int(start + np.argmin(log_drawdown[start:stop]))
        recovery = int(stop) if stop < len(log_drawdown) else None
        end = recovery if recovery is not None else len(log_drawdown) - 1
        episodes.append(
            {
                "peak_index": peak,
                "first_underwater_index": int(start),
                "trough_index": trough,
                "recovery_index": recovery,
                "end_index": int(end),
                "drawdown": float(-np.expm1(log_drawdown[trough])),
                "underwater_observations": int(stop - start),
                "peak_to_recovery_or_end_observations": int(end - peak),
            }
        )
    episodes.sort(key=lambda episode: (-episode["drawdown"], episode["peak_index"]))
    return {
        "n_returns": int(len(values)),
        **_metrics(log_drawdown, starts, stops),
        "episode_count": len(episodes),
        "episodes": episodes[:top_n],
        "index_convention": "NAV[0] = 1; return[i] ends at NAV[i + 1]",
        "recovery_log_nav_tolerance": _LOG_NAV_TOLERANCE,
    }


def _validate_block_size(block_size: int) -> None:
    if (
        isinstance(block_size, bool)
        or not isinstance(block_size, (int, np.integer))
        or block_size < 1
    ):
        raise ValueError("block_size must be a positive integer")


def _permuted_blocks(
    values: np.ndarray, block_size: int, rng: np.random.Generator
) -> np.ndarray:
    if len(values) == 0:
        return values.copy()
    blocks = [values[start : start + block_size] for start in range(0, len(values), block_size)]
    return np.concatenate([blocks[i] for i in rng.permutation(len(blocks))])


def permute_blocks(
    log_returns: Iterable[float] | np.ndarray,
    block_size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Permute disjoint consecutive blocks without resampling return values.

    Blocks are anchored at the first input observation. The shorter final block
    participates as a whole. Each original observation appears exactly once,
    preserving the mathematical sum of log returns and terminal wealth; usual
    floating-point summation-order roundoff can still occur.
    """
    _validate_block_size(block_size)
    return _permuted_blocks(_validate_returns(log_returns), int(block_size), rng)


def permutation_drawdown_reference(
    daily_log_returns: Iterable[float] | np.ndarray,
    n_permutations: int = 2000,
    seed: int = 20260906,
    block_sizes: tuple[int, ...] = (1, 5, 20),
    quantiles: tuple[float, ...] = (0.025, 0.5, 0.95, 0.975, 0.99),
) -> dict:
    """Compare daily-path drawdown and duration with fixed-block permutations.

    Block size 1 is individual-day permutation; sizes 5 and 20 shuffle fixed
    consecutive 5-/20-observation blocks. All use every input day exactly once.
    The default is 2,000 permutations per block size with a fixed seed.

    ``upper_tail_plus_one`` is (1 + count(reference >= observed)) / (B + 1),
    using inclusive ties and a 1e-12 numerical tolerance for MDD comparisons.
    It is an empirical order-reference tail fraction, not evidence of causation
    or a calibrated p-value under arbitrary dependent/nonstationary returns.
    The return frequency must be daily; this routine cannot infer that from
    values, and it must not be used to label daily MDD as bar-level MDD.
    """
    values = _validate_returns(daily_log_returns)
    if (
        isinstance(n_permutations, bool)
        or not isinstance(n_permutations, (int, np.integer))
        or n_permutations < 1
    ):
        raise ValueError("n_permutations must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if not block_sizes:
        raise ValueError("block_sizes must not be empty")
    for block_size in block_sizes:
        _validate_block_size(block_size)
    if len(set(block_sizes)) != len(block_sizes):
        raise ValueError("block_sizes must be unique")
    quantile_values = np.asarray(quantiles, dtype=float)
    if (
        quantile_values.ndim != 1
        or len(quantile_values) == 0
        or not np.all(np.isfinite(quantile_values))
        or np.any((quantile_values < 0) | (quantile_values > 1))
        or len(np.unique(quantile_values)) != len(quantile_values)
    ):
        raise ValueError("quantiles must be unique finite values between 0 and 1")

    observed = _metrics(*_accounting(values))
    references = {}
    for block_size in block_sizes:
        # Per-size streams make a size's results independent of argument order.
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), int(block_size)]))
        samples = {metric: np.empty(n_permutations) for metric in _METRICS}
        for trial in range(n_permutations):
            result = _metrics(*_accounting(_permuted_blocks(values, int(block_size), rng)))
            for metric in _METRICS:
                samples[metric][trial] = result[metric]
        reference = {
            "block_size": int(block_size),
            "n_blocks": int((len(values) + block_size - 1) // block_size),
        }
        for metric in _METRICS:
            tolerance = _LOG_NAV_TOLERANCE if metric == "mdd" else 0.0
            tail_count = int(np.count_nonzero(samples[metric] >= observed[metric] - tolerance))
            reference[metric] = {
                "quantiles": {
                    str(float(q)): float(value)
                    for q, value in zip(quantile_values, np.quantile(samples[metric], quantile_values))
                },
                "upper_tail_count": tail_count,
                "upper_tail_plus_one": float((tail_count + 1) / (n_permutations + 1)),
            }
        references[str(block_size)] = reference
    return {
        "sampling": "daily",
        "n_observations": int(len(values)),
        "n_permutations": int(n_permutations),
        "seed": int(seed),
        "observed": observed,
        "references": references,
        "interpretation": (
            "Descriptive order-exchangeability reference conditional on realized daily returns; "
            "not a causal proof or a calibrated p-value under arbitrary dependent/nonstationary "
            "returns. Daily sampling cannot reveal bar-level maximum drawdown. Unrecovered "
            "episode durations are right-censored at the final observation."
        ),
    }
