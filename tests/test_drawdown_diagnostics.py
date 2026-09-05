"""Mathematical path invariants; these tests do not load market data."""

import numpy as np
import pytest

from star50_filter.drawdown_diagnostics import (
    drawdown_summary,
    log_returns_to_nav,
    permutation_drawdown_reference,
    permute_blocks,
)


def returns_from_nav(nav):
    return np.diff(np.log(np.asarray(nav, dtype=float)))


def test_initial_capital_first_loss_and_recovery_are_counted():
    nav = [1.0, 0.8, 0.9, 1.0, 1.1, 0.88, 1.1]
    values = returns_from_nav(nav)
    np.testing.assert_allclose(log_returns_to_nav(values), nav)
    summary = drawdown_summary(values)
    assert summary["mdd"] == pytest.approx(0.2)
    assert summary["episode_count"] == 2
    first = next(episode for episode in summary["episodes"] if episode["peak_index"] == 0)
    assert first["trough_index"] == 1
    assert first["recovery_index"] == 3
    assert first["underwater_observations"] == 2
    assert first["peak_to_recovery_or_end_observations"] == 3
    assert summary["longest_underwater_observations"] == 2
    assert summary["longest_peak_to_recovery_or_end_observations"] == 3


def test_unrecovered_episode_indexes_and_duration_end_at_last_observation():
    summary = drawdown_summary(returns_from_nav([1.0, 1.2, 1.1, 0.9, 0.95]))
    assert summary["mdd"] == pytest.approx(0.25)
    episode = summary["episodes"][0]
    assert episode["peak_index"] == 1
    assert episode["first_underwater_index"] == 2
    assert episode["trough_index"] == 3
    assert episode["recovery_index"] is None
    assert episode["end_index"] == 4
    assert episode["underwater_observations"] == 3
    assert episode["peak_to_recovery_or_end_observations"] == 3


def test_repeated_peak_uses_last_peak_and_episodes_rank_by_depth():
    summary = drawdown_summary(returns_from_nav([1, 1, 0.9, 1, 1, 0.7, 0.7, 1.1]), top_n=1)
    assert summary["episode_count"] == 2
    assert len(summary["episodes"]) == 1
    episode = summary["episodes"][0]
    assert episode["peak_index"] == 4
    assert episode["trough_index"] == 5  # first tied trough
    assert episode["recovery_index"] == 7
    assert episode["drawdown"] == pytest.approx(0.3)


def test_full_path_does_not_reset_across_slices():
    # These slices could straddle any year boundary; the full path spans it.
    values = returns_from_nav([1, 1.2, 1.08, 0.9, 1.2])
    full = drawdown_summary(values)
    assert full["mdd"] == pytest.approx(0.25)
    assert full["episodes"][0]["peak_index"] == 1
    assert full["episodes"][0]["recovery_index"] == 4
    assert full["mdd"] > max(drawdown_summary(values[:2])["mdd"], drawdown_summary(values[2:])["mdd"])


@pytest.mark.parametrize("values", [[], [0], [0, 0], [0.1, 0.2]])
def test_empty_and_nonlosing_paths_have_zero_drawdown(values):
    summary = drawdown_summary(values)
    assert summary["mdd"] == 0
    assert summary["episodes"] == []
    assert summary["longest_underwater_observations"] == 0
    assert summary["longest_peak_to_recovery_or_end_observations"] == 0
    assert log_returns_to_nav(values)[0] == 1


@pytest.mark.parametrize("block_size", [1, 5, 20, 50])
def test_block_permutation_preserves_every_return_total_and_within_block_order(block_size):
    values = (np.arange(43) - 21) / 1000
    shuffled = permute_blocks(values, block_size, np.random.default_rng(9))
    np.testing.assert_array_equal(np.sort(shuffled), np.sort(values))
    assert np.sum(shuffled) == pytest.approx(np.sum(values), abs=1e-15)
    assert log_returns_to_nav(shuffled)[-1] == pytest.approx(log_returns_to_nav(values)[-1])
    # Every complete or shorter final block is still contiguous and ordered.
    for start in range(0, len(values), block_size):
        block = values[start : start + block_size]
        new_start = int(np.flatnonzero(shuffled == block[0])[0])
        np.testing.assert_array_equal(shuffled[new_start : new_start + len(block)], block)


def test_reference_is_reproducible_and_seed_stream_does_not_depend_on_size_order():
    values = np.array([0.04, 0.03, -0.08, -0.05, -0.04, 0.05, 0.03, -0.02])
    first = permutation_drawdown_reference(values, n_permutations=30)
    assert first == permutation_drawdown_reference(values, n_permutations=30)
    reordered = permutation_drawdown_reference(values, n_permutations=30, block_sizes=(20, 5, 1))
    assert first["references"] == reordered["references"]
    assert first["observed"]["mdd"] == pytest.approx(drawdown_summary(values)["mdd"])
    assert set(first["references"]) == {"1", "5", "20"}
    for reference in first["references"].values():
        for metric in first["observed"]:
            stat = reference[metric]
            assert stat["upper_tail_plus_one"] == (1 + stat["upper_tail_count"]) / 31
            assert 1 / 31 <= stat["upper_tail_plus_one"] <= 1


def test_single_block_reference_is_original_path_with_inclusive_ties():
    values = [0.02, -0.03, -0.05, 0.01]
    reference = permutation_drawdown_reference(values, n_permutations=7, block_sizes=(20,))
    for metric, observed in reference["observed"].items():
        stat = reference["references"]["20"][metric]
        assert stat["upper_tail_plus_one"] == 1
        assert all(value == pytest.approx(observed) for value in stat["quantiles"].values())


@pytest.mark.parametrize("bad", [[1.0, np.nan], [[0.1, 0.2]], [np.inf]])
def test_invalid_return_arrays_are_rejected(bad):
    with pytest.raises(ValueError):
        drawdown_summary(bad)
    with pytest.raises(ValueError):
        permutation_drawdown_reference(bad, n_permutations=2)


@pytest.mark.parametrize("bad", [0, -1, 1.5, True])
def test_invalid_block_size_is_rejected(bad):
    with pytest.raises(ValueError):
        permute_blocks([0.1], bad, np.random.default_rng(1))
