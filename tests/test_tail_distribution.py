import numpy as np
import pandas as pd
from star50_filter.tail_distribution import (
    calibrate,
    cluster_episodes,
    holm,
    permute_same_year_clock,
    prepare_instrument,
    previous_any,
    probability_scores,
)


def toy():
    dates = []
    for day in pd.bdate_range("2021-01-04", periods=6):
        for a, b in [("09:31", "11:30"), ("13:01", "15:00")]:
            dates.extend(pd.date_range(f"{day.date()} {a}", f"{day.date()} {b}", freq="min"))
    price = 100 * np.exp(np.cumsum(np.random.default_rng(7).normal(0, 0.001, len(dates))))
    return pd.DataFrame({"timestamp": dates, "open": price, "high": price, "low": price, "close": price, "symbol": "A"})


def test_sigma_strict_lag_and_session_boundary():
    f = toy()
    a = prepare_instrument(f, 1)
    assert a.groupby(["day", "session"]).r.first().notna().all()
    assert a.loc[a.boundary, "r"].isna().all()
    f.loc[900, ["open", "high", "low", "close"]] *= 1.2
    b = prepare_instrument(f, 1)
    assert a.sigma_prior.iloc[900] == b.sigma_prior.iloc[900]
    assert a.sigma_prior.iloc[901] != b.sigma_prior.iloc[901]
    np.testing.assert_allclose(a.return_all, a.body + a.gap, equal_nan=True, atol=1e-14)


def test_string_ohlc_source_is_numeric_before_all_comparisons():
    f = toy()
    expected = prepare_instrument(f, 1)
    f[["open", "high", "low", "close"]] = f[["open", "high", "low", "close"]].astype(str)
    actual = prepare_instrument(f, 1)
    pd.testing.assert_frame_equal(actual, expected)


def test_calibration_never_reads_later_returns():
    a = prepare_instrument(toy(), 1)
    a["year"] = 2021
    b = a.copy()
    b["symbol"] = "B"
    b["r"] *= 2
    b["z"] *= 2
    b["robust_z"] *= 2
    cut = calibrate([a, b])
    future = a.copy()
    future["year"] = 2024
    future["r"] = 100
    assert calibrate([pd.concat([a, future]), b]) == cut
    assert cut["tail_cutoffs"]["raw"] > a.r.abs().quantile(0.995)


def test_recent_history_and_cluster_definitions():
    y = np.zeros((2, 2, 12), bool)
    y[0, 0, [1, 3, 10]] = True
    y[0, 1, 0] = True
    p = previous_any(y, 5)
    assert not p[0, 0, 1] and p[0, 0, 3] and not p[0, 0, 10]
    assert not p[0, 1, 0] and not p[1].any()
    e = cluster_episodes(y, 1)
    assert sorted(e.events) == [1, 1, 2]


def test_permutation_preserves_year_clock_counts():
    y = np.random.default_rng(5).random((30, 2, 12)) < 0.15
    years = np.repeat([2024, 2025], 15)
    p = permute_same_year_clock(y, years, np.random.default_rng(71))
    for year in [2024, 2025]:
        np.testing.assert_array_equal(y[years == year].sum(axis=0), p[years == year].sum(axis=0))
    assert not np.array_equal(y, p)


def test_holm_and_probability_predictions():
    np.testing.assert_allclose(holm([0.01, 0.03, 0.2]), [0.03, 0.06, 0.2])
    tr = pd.DataFrame({"vol_bin": [0] * 10 + [2] * 10, "prior5": [False] * 20, "event": [0] * 10 + [1] * 10, "clock": ["09:32"] * 20})
    te = tr.copy()
    rows, p = probability_scores(tr, te)
    te["event"] = 1 - te.event
    _, again = probability_scores(tr, te)
    np.testing.assert_array_equal(p, again)
    assert p[0] < p[-1] and len(rows) == 3
