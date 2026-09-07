import numpy as np
import pandas as pd
import pytest
from star50_filter.causal_volatility import (
    FEATURES,
    VolatilityModel,
    event_metrics,
    fit_model,
    forecast_latest,
    future_variance,
    past_features,
)


def toy():
    times = []
    for year in [2021, 2023, 2024]:
        for day in pd.bdate_range(f"{year}-01-04", periods=5):
            for start, end in [("09:31", "11:30"), ("13:01", "15:00")]:
                times.extend(pd.date_range(f"{day.date()} {start}", f"{day.date()} {end}", freq="min", tz="Asia/Shanghai"))
    r = np.random.default_rng(731).normal(0, 0.001, len(times))
    boundary = np.arange(len(r)) % 120 == 0
    r[boundary] = np.nan
    return pd.DataFrame(
        {"timestamp": times, "r": r, "body": np.nan_to_num(r), "gap": np.where(boundary, 0.003, 0), "boundary": boundary, "symbol": "TEST"}
    )


def test_features_have_no_future_values():
    f = toy()
    full = past_features(f)
    for n in [800, 1500, 2500]:
        pd.testing.assert_frame_equal(full[FEATURES].iloc[:n], past_features(f.iloc[:n])[FEATURES])
    changed = f.copy()
    changed.loc[2600:, ["r", "body"]] *= 100
    pd.testing.assert_frame_equal(full[FEATURES].iloc[:2600], past_features(changed)[FEATURES].iloc[:2600])


def test_forward_label_is_strict_and_stays_in_session():
    f = past_features(toy())
    y = future_variance(f, 15)
    assert np.isclose(y.iloc[900], np.mean(f.r.iloc[901:916] ** 2))
    assert y[f.session_slot > 105].isna().all()
    changed = f.copy()
    changed.loc[900, "r"] = 100
    assert future_variance(changed, 15).iloc[900] == y.iloc[900]


def test_fit_ignores_evaluation_outcomes_and_saves(tmp_path):
    f = toy()
    x = past_features(f)
    model, _ = fit_model(x, 15)
    changed = f.copy()
    changed.loc[changed.timestamp.dt.year == 2024, ["r", "body"]] *= 5
    other, _ = fit_model(past_features(changed), 15)
    np.testing.assert_array_equal(model.coefficient, other.coefficient)
    np.testing.assert_array_equal(model.residuals, other.residuals)
    model.save(tmp_path / "model")
    loaded = VolatilityModel.load(tmp_path / "model")
    pd.testing.assert_frame_equal(model.predict_features(x), loaded.predict_features(x))


def test_probabilities_intervals_and_prefix_prediction():
    f = toy()
    x = past_features(f)
    model, _ = fit_model(x, 15)
    p = model.predict_features(x)
    valid = p.forecast_available
    assert (p.loc[valid, "sigma_p10"] <= p.loc[valid, "sigma_p90"]).all()
    assert (p.loc[valid, "p_amplify_2"] >= p.loc[valid, "p_amplify_3"]).all()
    assert (p.loc[valid, "p_amplify_3"] >= p.loc[valid, "p_amplify_4"]).all()
    pd.testing.assert_frame_equal(p.iloc[:2600], model.predict_features(past_features(f.iloc[:2600])))
    with pytest.raises(ValueError):
        forecast_latest(f.iloc[:120], model)
    with pytest.raises(ValueError):
        forecast_latest(f, model)


def test_event_denominators_are_not_interchanged():
    m = event_metrics([1, 1, 0, 0], [1, 0, 1, 1])
    assert m["precision"] == 1 / 3 and m["recall"] == 0.5 and m["alert_time_share"] == 0.75
    z = event_metrics([0, 0], [0, 0])
    assert z["precision"] is None and z["recall"] is None
