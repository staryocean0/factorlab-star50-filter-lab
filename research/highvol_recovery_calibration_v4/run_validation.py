from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V3_RUNNER = HERE.parent / "highvol_recovery_hazard_v3" / "run_hazard.py"
FREEZE = HERE / "FROZEN_CALIBRATION_V4.json"
VAL_YEARS = (2024, 2025)
WARMUP_YEAR = 2023


def load_v3():
    spec = importlib.util.spec_from_file_location("highvol_recovery_hazard_v3_validation", V3_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def load_symbol(root: Path, symbol: str, v3) -> pd.DataFrame:
    base = root / "data/market/5m" / symbol
    expected = [f"{y}.parquet" for y in (WARMUP_YEAR, *VAL_YEARS)]
    present = sorted(p.name for p in base.glob("*.parquet"))
    if present != expected:
        raise RuntimeError(f"Validation physical boundary/coverage mismatch for {symbol}: {present}")
    frames = []
    for year in (WARMUP_YEAR, *VAL_YEARS):
        p = base / f"{year}.parquet"
        raw = pd.read_parquet(p)
        day = pd.to_datetime(raw["trading_day"], errors="coerce") if "trading_day" in raw.columns else v3._wall_clock(raw["timestamp"]).dt.normalize()
        if "timestamp" in raw.columns:
            ts = v3._wall_clock(raw["timestamp"])
        elif "bar_end_shanghai" in raw.columns:
            ts = v3._wall_clock(raw["bar_end_shanghai"])
        else:
            raise RuntimeError(f"{p}: missing timestamp")
        x = pd.DataFrame({
            "symbol": symbol,
            "trading_day": day.dt.strftime("%Y-%m-%d"),
            "timestamp": ts,
            "close": pd.to_numeric(raw["close"], errors="coerce"),
        }).dropna(subset=["trading_day", "timestamp", "close"])
        frames.append(x)
    x = pd.concat(frames, ignore_index=True).sort_values(["trading_day", "timestamp"], kind="stable")
    return x.drop_duplicates(["trading_day", "timestamp"], keep="last").reset_index(drop=True)


def binary_scores(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float)
    eps = 1e-12; q = np.clip(p, eps, 1-eps)
    return {
        "n": int(len(y)),
        "brier": float(np.mean((p-y)**2)),
        "log_loss": float(-np.mean(y*np.log(q)+(1-y)*np.log(1-q))),
        "observed_rate": float(np.mean(y)),
        "mean_prediction": float(np.mean(p)),
    }


def run(root: Path, out: Path) -> dict:
    freeze = json.loads(FREEZE.read_text())
    v3 = load_v3()
    frames = v3.restrict_common_days({s: load_symbol(root, s, v3) for s in v3.SYMBOLS})
    frames = {s: v3.add_measurements(df) for s, df in frames.items()}
    v3.DEV_YEARS = VAL_YEARS
    lms = []
    for s in v3.SYMBOLS:
        _, lm = v3.build_landmarks(frames[s])
        lms.append(lm)
    landmarks = pd.concat(lms, ignore_index=True)
    x = landmarks[landmarks.active_at_landmark & landmarks.hazard_supported].copy()
    x = x[x.current_state.isin(["UNSAFE","RECOVERING"]) & x.landmark_bars.isin([1,3,6,9])].copy()
    x["normal_within_next15"] = x.normal_within_next15.astype(bool)

    fmap = pd.DataFrame(freeze["probability_map"]).rename(columns={"state":"current_state"})
    z = x.merge(fmap[["current_state","landmark_bars","probability"]], on=["current_state","landmark_bars"], how="left", validate="many_to_one")
    if z.probability.isna().any():
        raise RuntimeError("unmapped validation rows")
    z["p_global"] = float(freeze["development"]["global_probability"])
    y = z.normal_within_next15.astype(int).to_numpy()
    pooled_model = binary_scores(y, z.probability.to_numpy())
    pooled_global = binary_scores(y, z.p_global.to_numpy())

    annual = []
    for year in VAL_YEARS:
        q = z[z.year == year]
        yy = q.normal_within_next15.astype(int).to_numpy()
        annual.append({"year": year, "model": binary_scores(yy, q.probability.to_numpy()), "global": binary_scores(yy, q.p_global.to_numpy())})

    symbol_scores = []
    for symbol in v3.SYMBOLS:
        q = z[z.symbol == symbol]
        yy = q.normal_within_next15.astype(int).to_numpy()
        symbol_scores.append({"symbol": symbol, "model": binary_scores(yy, q.probability.to_numpy()), "global": binary_scores(yy, q.p_global.to_numpy())})

    observed_cells = z.groupby(["symbol","landmark_bars","current_state"], as_index=False).agg(
        n=("normal_within_next15","size"),
        observed_probability=("normal_within_next15","mean"),
        frozen_prediction=("probability","first"),
    )
    ordering = []
    for symbol in v3.SYMBOLS:
        q = observed_cells[observed_cells.symbol == symbol].set_index(["landmark_bars","current_state"])
        positive = 0; comparable = 0
        for lm in (1,3,6,9):
            if (lm,"UNSAFE") in q.index and (lm,"RECOVERING") in q.index:
                u = q.at[(lm,"UNSAFE"),"observed_probability"]
                r = q.at[(lm,"RECOVERING"),"observed_probability"]
                if pd.notna(u) and pd.notna(r):
                    comparable += 1; positive += int(r > u)
                    ordering.append({"symbol":symbol,"landmark_bars":lm,"unsafe_observed":float(u),"recovering_observed":float(r),"gap":float(r-u),"ordered":bool(r>u)})
        ordering.append({"symbol":symbol,"summary":True,"comparable_landmarks":comparable,"positive_landmarks":positive})

    summary_rows = [r for r in ordering if r.get("summary")]
    acc = freeze["validation_preregistered"]["acceptance"]
    acceptance = {
        "scored_rows_min_1000": bool(len(z) >= int(acc["scored_rows_min"])),
        "pooled_brier_better_than_frozen_global": bool(pooled_model["brier"] < pooled_global["brier"]),
        "pooled_logloss_better_than_frozen_global": bool(pooled_model["log_loss"] < pooled_global["log_loss"]),
        "brier_improves_each_available_year": bool(all(r["model"]["brier"] < r["global"]["brier"] for r in annual)),
        "observed_ordering_at_least_3_of_4_each_symbol": bool(all(r["positive_landmarks"] >= int(acc["observed_recovering_gt_unsafe_landmarks_min_per_symbol"]) for r in summary_rows)),
        "no_refit": True,
        "native_5m_only": True,
    }

    summary = {
        "schema":"highvol_recovery_calibration_v4_reusable_validation",
        "candidate_id": freeze["candidate_id"],
        "validation_coverage":["2024-01-01","2025-12-31"],
        "full_policy_validation_period":["2024-01-01","2026-08-21"],
        "coverage_complete_through_policy_end": False,
        "coverage_gap":"native cross-index 5m 2026-01-01 through 2026-08-21 is not present; no 1m resampling performed",
        "fresh_oos": False,
        "fit_performed": False,
        "parameter_change_performed": False,
        "state_thresholds_unchanged": True,
        "pnl_computed": False,
        "trading_rule_created": False,
        "blackbox_queried": False,
        "production_authority": False,
        "scored_rows": int(len(z)),
        "pooled_model": pooled_model,
        "pooled_frozen_global_baseline": pooled_global,
        "annual": annual,
        "symbol_scores": symbol_scores,
        "observed_cell_calibration": observed_cells.to_dict(orient="records"),
        "observed_state_ordering": ordering,
        "acceptance": acceptance,
        "available_coverage_validation_supported": bool(all(acceptance.values())),
        "decision_scope":"2024-2025 native-5m reusable Validation only; cannot claim full through-2026 validation until native 5m 2026 is available",
    }
    out.mkdir(parents=True, exist_ok=True)
    z.to_csv(out/"validation_scored_rows.csv", index=False)
    observed_cells.to_csv(out/"observed_cell_calibration.csv", index=False)
    (out/"summary.json").write_text(json.dumps(summary, indent=2, default=str, allow_nan=False)+"\n")
    print(json.dumps(summary, default=str, allow_nan=False))
    return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); run(Path(a.repo_root).resolve(), Path(a.out))

if __name__ == "__main__": main()
