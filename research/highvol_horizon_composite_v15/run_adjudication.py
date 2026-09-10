from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V11_RUNNER = HERE.parent / "highvol_recovery_survival_v11" / "run_survival.py"
V11_RUNNER_BLOB = "713f0dcc41e7f32f75934fc7709a406ff71579e6"

DEV_YEARS = (2021, 2022, 2023)
HORIZONS = (15, 30, 60)
STATES = ("UNSAFE", "RECOVERING")
BUCKETS = ("LT15", "M15_25", "M30_40", "GE45")
EXPECTED_ROWS = 7327
MIN_TRAIN_CELL_N = 50
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260910


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_v11():
    if not V11_RUNNER.exists():
        raise FileNotFoundError(V11_RUNNER)
    got = git_blob_sha(V11_RUNNER)
    if got != V11_RUNNER_BLOB:
        raise RuntimeError(f"V11 runner drift: {got} != {V11_RUNNER_BLOB}")
    spec = importlib.util.spec_from_file_location("v11_frozen_for_v15", V11_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(V11_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_rows(root: Path, v11) -> pd.DataFrame:
    if tuple(v11.DEV_YEARS) != DEV_YEARS:
        raise RuntimeError("V11 Development years drift")
    if tuple(v11.HORIZONS) != HORIZONS:
        raise RuntimeError("V11 horizons drift")
    if tuple(v11.STATES) != STATES or tuple(v11.BUCKETS) != BUCKETS:
        raise RuntimeError("V11 state/age dimensions drift")
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in v11.SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v11.build_rows(frames[s]) for s in v11.SYMBOLS], ignore_index=True)
    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"cohort drift: {len(rows)} != {EXPECTED_ROWS}")
    return rows


def smooth_prob(y: pd.Series) -> float:
    a = y.astype(int)
    return float((int(a.sum()) + 1) / (len(a) + 2))


def fit_age_only(train: pd.DataFrame, horizon: int) -> dict[str, float]:
    out = {}
    for bucket in BUCKETS:
        g = train[train.age_bucket == bucket]
        if g.empty:
            raise RuntimeError(f"missing age bucket {bucket}")
        out[bucket] = smooth_prob(g[f"normal_within_{horizon}m"])
    return out


def fit_state_age(train: pd.DataFrame, horizon: int) -> tuple[dict[tuple[str, str], float], dict[str, int]]:
    out = {}
    ns = {}
    for state in STATES:
        for bucket in BUCKETS:
            g = train[(train.current_state == state) & (train.age_bucket == bucket)]
            if g.empty:
                raise RuntimeError(f"missing state-age cell {state}/{bucket}")
            out[(state, bucket)] = smooth_prob(g[f"normal_within_{horizon}m"])
            ns[f"{state}|{bucket}"] = int(len(g))
    return out, ns


def binary_score(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    q = np.clip(p, 1e-12, 1 - 1e-12)
    return {
        "n": int(len(y)),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
        "observed_rate": float(np.mean(y)),
        "mean_prediction": float(np.mean(p)),
    }


def make_oof(rows: pd.DataFrame) -> tuple[pd.DataFrame, list[dict], int]:
    parts = []
    annual = []
    min_cell = 10**9
    for held in DEV_YEARS:
        train = rows[rows.year != held]
        test = rows[rows.year == held].copy().reset_index(drop=True)
        rec = {"held_out_year": held, "horizons": {}}
        out = test[["symbol", "trading_day", "year", "current_state", "age_bucket"]].copy()
        for h in HORIZONS:
            age_map = fit_age_only(train, h)
            state_map, ns = fit_state_age(train, h)
            min_cell = min(min_cell, min(ns.values()))
            y = test[f"normal_within_{h}m"].astype(int).to_numpy()
            p_age = np.array([age_map[b] for b in test.age_bucket], float)
            p_sa = np.array([state_map[(s, b)] for s, b in zip(test.current_state, test.age_bucket)], float)
            age_score = binary_score(y, p_age)
            state_score = binary_score(y, p_sa)
            rec["horizons"][str(h)] = {
                "age_only": age_score,
                "state_plus_age": state_score,
                "brier_improvement_state_over_age": float(age_score["brier"] - state_score["brier"]),
                "logloss_improvement_state_over_age": float(age_score["log_loss"] - state_score["log_loss"]),
                "state_age_training_cell_n": ns,
            }
            out[f"y_{h}"] = y
            out[f"p_age_{h}"] = p_age
            out[f"p_state_age_{h}"] = p_sa
            out[f"delta_brier_{h}"] = (p_age - y) ** 2 - (p_sa - y) ** 2
        parts.append(out)
        annual.append(rec)
    oof = pd.concat(parts, ignore_index=True)
    if len(oof) != EXPECTED_ROWS:
        raise RuntimeError(f"OOF row drift: {len(oof)} != {EXPECTED_ROWS}")
    return oof, annual, int(min_cell)


def clustered_bootstrap(oof: pd.DataFrame, horizon: int) -> dict:
    col = f"delta_brier_{horizon}"
    day = oof.groupby("trading_day", sort=True)[col].agg(["sum", "count"])
    sums = day["sum"].to_numpy(float)
    counts = day["count"].to_numpy(float)
    if len(sums) < 2:
        raise RuntimeError("too few trading-day clusters")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.empty(BOOTSTRAP_REPS, float)
    n_days = len(sums)
    for i in range(BOOTSTRAP_REPS):
        idx = rng.integers(0, n_days, size=n_days)
        draws[i] = float(sums[idx].sum() / counts[idx].sum())
    point = float(oof[col].mean())
    lo, hi = np.quantile(draws, [0.025, 0.975])
    return {
        "horizon_minutes": horizon,
        "cluster_key": "trading_day",
        "clusters": int(n_days),
        "repetitions": BOOTSTRAP_REPS,
        "seed": BOOTSTRAP_SEED,
        "point_brier_improvement": point,
        "ci95_lower": float(lo),
        "ci95_upper": float(hi),
        "probability_improvement_positive": float(np.mean(draws > 0)),
        "ci95_contains_zero": bool(lo <= 0 <= hi),
    }


def pooled_metrics(oof: pd.DataFrame) -> dict:
    out = {}
    for h in HORIZONS:
        y = oof[f"y_{h}"].to_numpy(float)
        pa = oof[f"p_age_{h}"].to_numpy(float)
        ps = oof[f"p_state_age_{h}"].to_numpy(float)
        a = binary_score(y, pa)
        s = binary_score(y, ps)
        out[str(h)] = {
            "age_only": a,
            "state_plus_age": s,
            "brier_improvement_state_over_age": float(a["brier"] - s["brier"]),
            "logloss_improvement_state_over_age": float(a["log_loss"] - s["log_loss"]),
        }
    return out


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def run(root: Path, out: Path) -> dict:
    v11 = load_v11()
    rows = build_rows(root, v11)
    oof, annual, min_cell = make_oof(rows)
    pooled = pooled_metrics(oof)
    boot = {str(h): clustered_bootstrap(oof, h) for h in HORIZONS}
    annual_brier_wins = {
        str(h): int(sum(f["horizons"][str(h)]["brier_improvement_state_over_age"] > 0 for f in annual))
        for h in HORIZONS
    }

    acceptance = {
        "row_count_exact_7327": int(len(rows)) == EXPECTED_ROWS,
        "every_state_age_training_cell_n_ge_50": min_cell >= MIN_TRAIN_CELL_N,
        "h15_bootstrap_ci_lower_gt_zero": boot["15"]["ci95_lower"] > 0,
        "h30_bootstrap_ci_lower_gt_zero": boot["30"]["ci95_lower"] > 0,
        "h60_bootstrap_ci_contains_zero": boot["60"]["ci95_contains_zero"],
        "h15_annual_brier_wins_ge_2_of_3": annual_brier_wins["15"] >= 2,
        "h30_annual_brier_wins_ge_2_of_3": annual_brier_wins["30"] >= 2,
        "state_thresholds_unchanged": True,
        "age_buckets_unchanged": True,
        "horizons_unchanged": True,
        "sample_cohort_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    supported = bool(all(acceptance.values()))
    summary = {
        "schema": "highvol_horizon_composite_v15_development_adjudication_v1",
        "development_only": True,
        "validation_informed_hypothesis": True,
        "development_years": list(DEV_YEARS),
        "row_count": int(len(rows)),
        "models": ["age_only", "state_plus_age"],
        "horizons_minutes": list(HORIZONS),
        "bootstrap": {
            "cluster_key": "trading_day",
            "repetitions": BOOTSTRAP_REPS,
            "seed": BOOTSTRAP_SEED,
            "results": boot,
        },
        "min_state_age_training_cell_n": min_cell,
        "annual_brier_win_count": annual_brier_wins,
        "annual_leave_one_year_out": annual,
        "pooled_leave_one_year_out": pooled,
        "acceptance": acceptance,
        "horizon_dependence_supported": supported,
        "next_step_authorized": "CONSTRUCT_MONOTONE_HORIZON_ADAPTIVE_SURFACE_IN_NEW_DEVELOPMENT_BRANCH" if supported else "NO_HORIZON_ADAPTIVE_SURFACE_AUTHORIZED",
        "threshold_search_performed": False,
        "parameter_change_performed": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
    }
    out.mkdir(parents=True, exist_ok=True)
    oof.to_parquet(out / "oof_predictions.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
