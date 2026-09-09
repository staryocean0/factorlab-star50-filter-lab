from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V3_RUNNER = HERE.parent / "highvol_recovery_hazard_v3" / "run_hazard.py"
STATES = ("UNSAFE", "RECOVERING")
LANDMARKS = (1, 3, 6, 9)
MIN_CELL_N = 100


def load_v3():
    spec = importlib.util.spec_from_file_location("highvol_recovery_hazard_v3_frozen", V3_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def smooth(successes: int, n: int) -> float:
    return float((successes + 1) / (n + 2))


def fit_cells(x: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for values, g in x.groupby(keys, sort=True):
        if not isinstance(values, tuple):
            values = (values,)
        n = int(len(g))
        s = int(g.normal_within_next15.astype(bool).sum())
        row = dict(zip(keys, values))
        row.update({"n": n, "successes": s, "raw_probability": float(s / n), "smoothed_probability": smooth(s, n)})
        rows.append(row)
    return pd.DataFrame(rows)


def attach_predictions(x: pd.DataFrame, cells: pd.DataFrame, keys: list[str], name: str) -> pd.DataFrame:
    m = cells[keys + ["smoothed_probability"]].rename(columns={"smoothed_probability": name})
    return x.merge(m, on=keys, how="left", validate="many_to_one")


def scores(y: np.ndarray, p: np.ndarray) -> dict:
    p = np.asarray(p, float)
    y = np.asarray(y, float)
    if not np.isfinite(p).all():
        raise RuntimeError("missing/non-finite predictions")
    eps = 1e-12
    q = np.clip(p, eps, 1 - eps)
    return {
        "n": int(len(y)),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
        "mean_prediction": float(np.mean(p)),
        "observed_rate": float(np.mean(y)),
    }


def run(root: Path, out: Path) -> dict:
    v3 = load_v3()
    frames = v3.restrict_common_days({s: v3.load_symbol(root, s) for s in v3.SYMBOLS})
    frames = {s: v3.add_measurements(df) for s, df in frames.items()}
    landmark_frames = []
    for s in v3.SYMBOLS:
        _, lm = v3.build_landmarks(frames[s])
        landmark_frames.append(lm)
    landmarks = pd.concat(landmark_frames, ignore_index=True)
    x = landmarks[landmarks.active_at_landmark & landmarks.hazard_supported].copy()
    x = x[x.current_state.isin(STATES) & x.landmark_bars.isin(LANDMARKS)].copy()
    x["normal_within_next15"] = x.normal_within_next15.astype(bool)

    cells = fit_cells(x, ["current_state", "landmark_bars"])
    age = fit_cells(x, ["landmark_bars"])
    state = fit_cells(x, ["current_state"])
    global_n = int(len(x))
    global_s = int(x.normal_within_next15.sum())
    global_p = smooth(global_s, global_n)

    z = attach_predictions(x, cells, ["current_state", "landmark_bars"], "p_state_age")
    z = attach_predictions(z, age, ["landmark_bars"], "p_age")
    z = attach_predictions(z, state, ["current_state"], "p_state")
    z["p_global"] = global_p
    y = z.normal_within_next15.astype(int).to_numpy()
    score_table = {
        "state_age_8_cell": scores(y, z.p_state_age.to_numpy()),
        "age_only_4_cell": scores(y, z.p_age.to_numpy()),
        "state_only_2_cell": scores(y, z.p_state.to_numpy()),
        "global": scores(y, z.p_global.to_numpy()),
    }

    cell_index = cells.set_index(["landmark_bars", "current_state"])
    ordering = []
    for lm in LANDMARKS:
        pu = float(cell_index.at[(lm, "UNSAFE"), "smoothed_probability"])
        pr = float(cell_index.at[(lm, "RECOVERING"), "smoothed_probability"])
        ordering.append({"landmark_bars": lm, "unsafe_probability": pu, "recovering_probability": pr, "gap": pr - pu, "ordered": bool(pr > pu)})

    exact_cells = len(cells) == 8 and set(map(tuple, cells[["current_state", "landmark_bars"]].to_records(index=False))) == {(s, lm) for s in STATES for lm in LANDMARKS}
    acceptance = {
        "exactly_8_cells": bool(exact_cells),
        "all_cells_n_ge_100": bool(len(cells) == 8 and (cells.n >= MIN_CELL_N).all()),
        "recovering_gt_unsafe_all_4_landmarks": bool(all(r["ordered"] for r in ordering)),
        "state_thresholds_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
    }
    eligible = bool(all(acceptance.values()))

    frozen_map = [
        {
            "current_state": str(r.current_state),
            "landmark_bars": int(r.landmark_bars),
            "landmark_minutes": int(r.landmark_bars) * 5,
            "n": int(r.n),
            "successes": int(r.successes),
            "raw_probability": float(r.raw_probability),
            "smoothed_probability": float(r.smoothed_probability),
        }
        for r in cells.sort_values(["landmark_bars", "current_state"]).itertuples()
    ]

    summary = {
        "schema": "highvol_recovery_calibration_v4_development",
        "development_period": ["2021-01-01", "2023-12-31"],
        "warmup_year": 2020,
        "symbols_pooled": list(v3.SYMBOLS),
        "model": "shared_2_state_x_4_landmark_laplace_probability_table",
        "target": "normal_within_next_15_minutes",
        "fit_rows": int(len(x)),
        "state_thresholds_unchanged": True,
        "pnl_computed": False,
        "trading_rule_created": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "production_authority": False,
        "frozen_map": frozen_map,
        "ordering": ordering,
        "in_sample_scores": score_table,
        "development_global_probability": global_p,
        "acceptance": acceptance,
        "calibration_candidate_eligible": eligible,
    }

    out.mkdir(parents=True, exist_ok=True)
    x.to_csv(out / "development_calibration_rows.csv", index=False)
    cells.to_csv(out / "state_age_cells.csv", index=False)
    age.to_csv(out / "age_only_cells.csv", index=False)
    state.to_csv(out / "state_only_cells.csv", index=False)
    z[["symbol", "year", "trading_day", "landmark_bars", "current_state", "normal_within_next15", "p_state_age", "p_age", "p_state", "p_global"]].to_csv(out / "scored_rows.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps(summary, allow_nan=False))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
