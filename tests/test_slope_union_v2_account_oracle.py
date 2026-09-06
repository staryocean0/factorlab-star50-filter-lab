import numpy as np
import pandas as pd
from star50_filter.slope_union_v2 import account


def test_cash_and_fixed_share_independent_oracle():
    rng = np.random.default_rng(510)
    price = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 700)))
    signal = rng.choice([-1, 0, 1], size=700)
    times = pd.Series(pd.date_range("2021-01-04 09:30", periods=700, freq="min"))
    fee = 0.0002
    _, _, calculated, _ = account(price, times, signal, prior_decision=-1)
    positions = np.r_[-1, signal[:-1]]
    positions[-1] = 0
    cash, shares = 1.0, 0.0
    old = 0
    expected = []
    for p, wanted in zip(price, positions, strict=True):
        if wanted != old:
            if old:
                cash += shares * p - abs(shares) * p * fee
                shares = 0.0
            if wanted:
                shares = wanted * cash / (p * (1 + fee))
                cash -= shares * p + abs(shares) * p * fee
            old = wanted
        expected.append(cash + shares * p)
    np.testing.assert_allclose(calculated, expected, rtol=1e-12, atol=1e-12)
