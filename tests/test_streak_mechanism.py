import numpy as np
from star50_filter.streak_mechanism import sequence_stats, permuted_sequences, holm, runs


def test_neutral_breaks_runs_and_scans_all_positions():
    x = np.r_[np.ones(30), -np.ones(20), 0, -np.ones(3)].astype(np.int8)
    r = sequence_stats(x, .5)[0]
    assert r[0] == 20 and r[1] == 30
    assert np.isclose(r[2], np.sqrt(20))
    assert np.isclose(r[3], np.sqrt(20))
    assert runs(x).length.sum() == len(x)


def test_day_clusters_preserve_internal_order_and_counts():
    x = np.array([1, -1, -1, 1, 0, -1], dtype=np.int8)
    ids = np.array([0, 0, 0, 1, 1, 1])
    simulated = permuted_sequences(x, ids, 30, 17)
    assert np.array_equal(simulated, permuted_sequences(x, ids, 30, 17))
    possible = (x, np.r_[x[3:], x[:3]])
    assert all(any(np.array_equal(row, choice) for choice in possible) for row in simulated)
    assert np.all((simulated == -1).sum(axis=1) == 3)


def test_holm_controls_all_hypotheses_and_restores_order():
    assert np.allclose(holm([.03, .001, .02]), [.04, .003, .04])


def test_window_variance_uses_each_calendar_year_baseline():
    x = np.r_[np.ones(25), -np.ones(25)].astype(np.int8)
    p = np.r_[np.full(25, .8), np.full(25, .2)]
    r = sequence_stats(x, p)[0]
    brute = []
    for w in (20, 50):
        for a in range(len(x)-w+1):
            expect = p[a:a+w].sum()
            variance = np.sum(p[a:a+w]*(1-p[a:a+w]))
            brute.append((expect-np.count_nonzero(x[a:a+w] == 1))/np.sqrt(variance))
    assert np.isclose(r[2], max(brute))
