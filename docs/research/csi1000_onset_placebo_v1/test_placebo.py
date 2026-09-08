from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

MOD = Path(__file__).resolve().parent / "run_placebo.py"
spec = importlib.util.spec_from_file_location("placebo", MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _row(day, session, minute, onset_row, onset, ongoing, gross, candidate_id=None, year=2022):
    d = {
        "symbol": "000852.SH",
        "year": year,
        "trading_day": day,
        "session": session,
        "half": int(session.rsplit("/", 1)[-1]),
        "minute": minute,
        "clock_bucket15": (minute - 1) // 15,
        "onset_row": onset_row,
        "is_onset": onset,
        "is_ongoing_highvol": ongoing,
        "slow30_net_bp": 8.0,
        "net5_bp": 4.0,
        "tail2_share": 0.7,
        "tail1_share": 0.4,
        "recovery_ratio": 1.8,
        "gross_3m_bp": gross,
    }
    if candidate_id is not None:
        d["candidate_id"] = candidate_id
    return d


def test_candidate_nonoverlap_contract():
    z = pd.DataFrame([
        _row("2022-01-04", "2022-01-04/0", 41, 40, True, False, 1.0),
        _row("2022-01-04", "2022-01-04/0", 44, 43, True, False, 2.0),
        _row("2022-01-04", "2022-01-04/0", 46, 45, True, False, 3.0),
    ])
    q = m.select_nonoverlap_candidates(z)
    assert list(q.onset_row) == [40, 45]


def test_control_exclusion_is_session_local_plus_minus_ten():
    cand = pd.DataFrame([
        _row("2022-01-04", "2022-01-04/0", 41, 40, True, False, 1.0, 0)
    ])
    ctrl = pd.DataFrame([
        _row("2022-01-04", "2022-01-04/0", 49, 48, False, True, 0.0),
        _row("2022-01-04", "2022-01-04/0", 52, 51, False, True, 0.0),
        _row("2022-01-04", "2022-01-04/1", 41, 40, False, True, 0.0),
    ])
    q = m.exclude_near_candidates(ctrl, cand)
    assert set(zip(q.session, q.onset_row)) == {("2022-01-04/0", 51), ("2022-01-04/1", 40)}


def test_matching_identity_does_not_use_future_outcome():
    cand = pd.DataFrame([
        _row("2022-01-04", "2022-01-04/0", 46, 45, True, False, 99.0, 0)
    ])
    controls = pd.DataFrame([
        _row("2022-02-01", "2022-02-01/0", 46, 45, False, True, -1000.0),
        _row("2022-02-02", "2022-02-02/0", 46, 45, False, True, 1000.0),
    ])
    # Make the second control farther using a past-only feature.
    controls.loc[1, "slow30_net_bp"] = 80.0
    q1 = m.match_role(cand, controls, "Development")
    picked1 = (q1.control_day.iloc[0], int(q1.control_minute.iloc[0]))
    controls2 = controls.copy()
    controls2["gross_3m_bp"] *= -10_000
    q2 = m.match_role(cand, controls2, "Development")
    picked2 = (q2.control_day.iloc[0], int(q2.control_minute.iloc[0]))
    assert picked1 == picked2 == ("2022-02-01", 46)


def test_pair_metrics_known_values():
    p = pd.DataFrame({
        "candidate_gross_3m_bp": [4.0, 2.0],
        "control_gross_3m_bp": [1.0, 3.0],
        "paired_diff_bp": [3.0, -1.0],
        "match_tier": [0, 1],
        "match_distance": [0.2, 0.4],
    })
    q = m.pair_metrics(p, 2)
    assert q["matched_count"] == 2
    assert abs(q["mean_paired_diff_bp"] - 1.0) < 1e-12
    assert abs(q["coverage"] - 1.0) < 1e-12
    assert abs(q["tier1_fraction"] - 0.5) < 1e-12


def test_day_bootstrap_is_deterministic():
    p = pd.DataFrame({
        "candidate_day": ["2022-01-04", "2022-01-04", "2022-01-05"],
        "paired_diff_bp": [1.0, 3.0, -1.0],
    })
    a = m.day_block_bootstrap(p, seed=7, draws=100)
    b = m.day_block_bootstrap(p, seed=7, draws=100)
    assert a == b
    assert a["candidate_days"] == 2
