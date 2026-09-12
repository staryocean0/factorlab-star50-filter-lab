from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT_PATH = ROOT / "research/cross_index_degree_transfer_utility_v1/run_study.py"
PARENT_BLOB = "b4d3c72e58706b2eb9ae8425f7e7f5439ba002c5"
PROTOCOL_BLOB = "807623a9f810a37fda0df8ba9e63932471dc3a48"
SOURCE_MAIN = "e30a0eb0e0884a569110c8819fb4b2696bb9dd29"

MODELS = ("B", "R", "Q")
ENDPOINTS = ("log_future_sigma", "future_tail")
HORIZONS = (15, 30, 60)
SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
REL_WINDOW = 48
LAMBDA = 0.01
SEED = 20260916
BOOTSTRAPS = 5000
FAMILY = 12


def git_blob_bytes(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_parent():
    if not PARENT_PATH.exists():
        raise RuntimeError(f"missing frozen parent runner: {PARENT_PATH}")
    if git_blob_bytes(PARENT_PATH.read_bytes()) != PARENT_BLOB:
        raise RuntimeError("cross-index degree parent runner blob drift")
    spec = importlib.util.spec_from_file_location("cross_index_residual_parent", PARENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


base = load_parent()


def other_symbol(symbol: str) -> str:
    return base.other_symbol(symbol)


def relationship_metrics(y_hist, x_hist, y_cur: float, x_cur: float):
    y = np.asarray(y_hist, float)
    x = np.asarray(x_hist, float)
    if len(y) != REL_WINDOW or len(x) != REL_WINDOW:
        return None
    if not np.isfinite(y).all() or not np.isfinite(x).all() or not np.isfinite([y_cur, x_cur]).all():
        return None
    xm = float(x.mean())
    ym = float(y.mean())
    vx = float(np.mean((x - xm) ** 2))
    if vx <= 1e-12:
        return None
    beta = float(np.mean((x - xm) * (y - ym)) / vx)
    alpha = float(ym - beta * xm)
    resid = y - (alpha + beta * x)
    resid_sd = float(np.std(resid, ddof=1))
    spread = y - x
    spread_mean = float(np.mean(spread))
    spread_sd = float(np.std(spread, ddof=1))
    if not np.isfinite(resid_sd) or resid_sd <= 1e-12:
        return None
    if not np.isfinite(spread_sd) or spread_sd <= 1e-12:
        return None
    e_cur = float(y_cur - (alpha + beta * x_cur))
    s_cur = float(y_cur - x_cur)
    rz = float(abs(e_cur) / resid_sd)
    qz = float(abs(s_cur - spread_mean) / spread_sd)
    return {
        "alpha": alpha,
        "beta": beta,
        "resid_sd": resid_sd,
        "spread_mean": spread_mean,
        "spread_sd": spread_sd,
        "residual_signed": e_cur,
        "spread_signed_centered": s_cur - spread_mean,
        "RZ48": rz,
        "QZ48": qz,
    }


def attach_relationship_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    other = frame[["symbol", "trading_day", "bar_end", "decision_time", "r", "partial_return"]].copy()
    other["symbol"] = other.symbol.map(other_symbol)
    other = other.rename(columns={"r": "other_r", "partial_return": "other_partial_return"})
    keys = ["symbol", "trading_day", "bar_end", "decision_time"]
    q = frame.merge(other, on=keys, how="left", validate="one_to_one")
    for col in ("RZ48", "QZ48", "relation_alpha", "relation_beta", "relation_resid_sd",
                "spread_mean", "spread_sd", "residual_signed", "spread_signed_centered"):
        q[col] = np.nan
    q["relation_history_n"] = 0

    for symbol, g in q.groupby("symbol", sort=False):
        hist_y: list[float] = []
        hist_x: list[float] = []
        for i in g.sort_values("bar_end", kind="stable").index:
            q.at[i, "relation_history_n"] = min(len(hist_y), REL_WINDOW)
            y_cur = q.at[i, "partial_return"]
            x_cur = q.at[i, "other_partial_return"]
            if len(hist_y) >= REL_WINDOW and np.isfinite(y_cur) and np.isfinite(x_cur):
                m = relationship_metrics(hist_y[-REL_WINDOW:], hist_x[-REL_WINDOW:], float(y_cur), float(x_cur))
                if m is not None:
                    q.at[i, "RZ48"] = m["RZ48"]
                    q.at[i, "QZ48"] = m["QZ48"]
                    q.at[i, "relation_alpha"] = m["alpha"]
                    q.at[i, "relation_beta"] = m["beta"]
                    q.at[i, "relation_resid_sd"] = m["resid_sd"]
                    q.at[i, "spread_mean"] = m["spread_mean"]
                    q.at[i, "spread_sd"] = m["spread_sd"]
                    q.at[i, "residual_signed"] = m["residual_signed"]
                    q.at[i, "spread_signed_centered"] = m["spread_signed_centered"]
            y_final = q.at[i, "r"]
            x_final = q.at[i, "other_r"]
            if np.isfinite(y_final) and np.isfinite(x_final):
                hist_y.append(float(y_final))
                hist_x.append(float(x_final))

    q["cross_base_available"] = q.base_available & q.other_current_available.fillna(False)
    for c in ("other_shock_intensity", "other_vol_ratio", "partial_return", "other_partial_return"):
        q["cross_base_available"] &= np.isfinite(q[c])
    q["relationship_available"] = q.cross_base_available & np.isfinite(q.RZ48) & np.isfinite(q.QZ48)
    return q


def build_table(root: Path, years_5m: tuple[int, ...], years_3s: tuple[int, ...]):
    frame, identities = base.build_table(root, years_5m, years_3s)
    q = attach_relationship_coordinates(frame)
    identities = dict(identities)
    identities["cross_index_degree_parent_runner_git_blob"] = PARENT_BLOB
    return q, identities


def severity_block(q: pd.DataFrame, column: str) -> tuple[np.ndarray, list[str]]:
    z0 = q[column].to_numpy(float)
    if not np.isfinite(z0).all() or np.any(z0 < 0):
        raise ValueError("invalid severity coordinate")
    u = np.log1p(z0)
    terms = (("relationship_severity", u), ("relationship_severity2", u * u))
    extra: list[np.ndarray] = []
    names: list[str] = []
    for name, values in terms:
        extra.append(values)
        names.append(name)
        for state in STATES:
            extra.append(values * q.previous_state.eq(state).to_numpy(float))
            names.append(f"{name}:state:{state}")
    return np.column_stack(extra).astype(float), names


def design(q: pd.DataFrame, model: str) -> tuple[np.ndarray, list[str]]:
    if model not in MODELS:
        raise ValueError(model)
    xb, namesb = base.design(q, "X")
    if model == "B":
        return xb, namesb
    column = "RZ48" if model == "R" else "QZ48"
    extra, names = severity_block(q, column)
    xx = np.column_stack([xb, extra]).astype(float)
    if not np.isfinite(xx).all():
        raise ValueError("nonfinite residual-dislocation design")
    return xx, namesb + names


def fit_probe(x: np.ndarray, y: np.ndarray, names: list[str]) -> dict:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-14] = 1.0
    z = (x - mean) / scale
    intercept = float(np.mean(y))
    beta = np.linalg.solve(z.T @ z / len(z) + LAMBDA * np.eye(z.shape[1]), z.T @ (y - intercept) / len(z))
    return {"names": names, "mean": mean.tolist(), "scale": scale.tolist(), "beta": beta.tolist(),
            "intercept": intercept, "n": int(len(y))}


def predict(q: pd.DataFrame, model: str, probe: dict, endpoint: str) -> np.ndarray:
    x, names = design(q, model)
    if names != probe["names"]:
        raise RuntimeError("feature schema drift")
    value = ((x - np.asarray(probe["mean"])) / np.asarray(probe["scale"])) @ np.asarray(probe["beta"]) + float(probe["intercept"])
    return np.clip(value, 0, 1) if endpoint == "future_tail" else value


def cohort(frame: pd.DataFrame, years: tuple[int, ...], h: int):
    in_year = frame.year.isin(years)
    base_future = in_year & frame.cross_base_available & frame[f"label_ok_{h}"].fillna(False)
    final = base_future & frame.relationship_available
    z = frame.loc[final].copy().reset_index(drop=True)
    z["sigma"] = z[f"sigma_{h}"]
    z["log_future_sigma"] = z[f"log_future_sigma_{h}"]
    z["future_tail"] = z[f"future_tail_{h}"]
    counts = {
        "target_rows": int(in_year.sum()),
        "cross_base_and_future_feasible": int(base_future.sum()),
        "relation_available": int((base_future & frame.relationship_available).sum()),
        "final": int(final.sum()),
        "coverage": float(final.sum() / base_future.sum()) if base_future.sum() else 0.0,
    }
    return z, counts


def block_stats(q: pd.DataFrame, gain: np.ndarray, days_per_block: int) -> pd.DataFrame:
    d = pd.DataFrame({"day": q.trading_day.to_numpy(), "year": q.year.to_numpy(), "gain": gain, "n": 1})
    days = d[["year", "day"]].drop_duplicates().sort_values(["year", "day"])
    days["block"] = days.groupby("year").cumcount() // days_per_block
    d = d.merge(days, on=["year", "day"], validate="many_to_one")
    return d.groupby(["year", "block"], as_index=False)[["gain", "n"]].sum()


def interval(blocks: pd.DataFrame) -> dict:
    rng = np.random.default_rng(SEED)
    gains = np.zeros(BOOTSTRAPS)
    count = np.zeros(BOOTSTRAPS)
    for _, g in blocks.groupby("year", sort=True):
        ix = rng.integers(0, len(g), size=(BOOTSTRAPS, len(g)))
        gains += g.gain.to_numpy()[ix].sum(axis=1)
        count += g.n.to_numpy()[ix].sum(axis=1)
    a = 0.05 / (2 * FAMILY)
    lo, hi = np.quantile(gains / count, [a, 1 - a])
    return {"low": float(lo), "high": float(hi), "blocks": int(len(blocks)), "repetitions": BOOTSTRAPS}


def compare(q: pd.DataFrame, endpoint: str, base_model: str, probes: dict, forward_gain: float,
            dev_n: int, coverage: float, h: int, out: Path) -> dict:
    y = q[endpoint].to_numpy(float)
    pr = predict(q, "R", probes[f"{h}|{endpoint}|R"], endpoint)
    pb = predict(q, base_model, probes[f"{h}|{endpoint}|{base_model}"], endpoint)
    l0 = (y - pb) ** 2
    l1 = (y - pr) ** 2
    gain = l0 - l1
    absolute = float(gain.mean())
    relative = float(absolute / l0.mean())
    slices = {}
    for col in ("year", "symbol"):
        for key, inds in q.groupby(col, sort=True).indices.items():
            slices[f"{col}:{key}"] = {
                "n": int(len(inds)),
                "absolute_gain": float(gain[inds].mean()),
                "relative_gain": float(gain[inds].mean() / l0[inds].mean()),
            }
    ci = {}
    for days in (5, 20):
        blocks = block_stats(q, gain, days)
        blocks.to_csv(out / f"blocks_{h}_{endpoint}_R_vs_{base_model}_{days}d.csv",
                      index=False, float_format="%.17g")
        ci[str(days)] = interval(blocks)
    gates = {
        "sample_size": len(q) >= 10000 and dev_n >= 20000 and all(v["n"] >= 1000 for v in slices.values()),
        "positive_events": endpoint != "future_tail" or int(y.sum()) >= 100,
        "relative_at_least_one_percent": relative >= 0.01,
        "tail_absolute_at_least_0005": endpoint != "future_tail" or absolute >= 0.0005,
        "adjusted_5day_interval_positive": ci["5"]["low"] > 0,
        "annual_and_symbol_signs": all(v["absolute_gain"] >= 0 for v in slices.values()),
        "coverage": coverage >= 0.95,
        "development_2023_forward_nonnegative": forward_gain >= 0,
    }
    return {
        "horizon": h, "endpoint": endpoint, "comparison": f"R_vs_{base_model}",
        "n": int(len(q)), "development_n": int(dev_n),
        "positive_events": int(y.sum()) if endpoint == "future_tail" else None,
        "baseline_loss": float(l0.mean()), "residual_loss": float(l1.mean()),
        "absolute_gain": absolute, "relative_gain": relative,
        "ci_5day": ci["5"], "ci_20day_sensitivity": ci["20"],
        "slices": slices, "development_forward_gain": float(forward_gain),
        "gates": gates, "supported": bool(all(gates.values())),
    }


def feature_identity_checks(frame: pd.DataFrame) -> dict:
    z = frame[frame.relationship_available].head(200).copy()
    if z.empty:
        raise RuntimeError("no relationship feature rows")
    b, bn = design(z, "B")
    r, rn = design(z, "R")
    q, qn = design(z, "Q")
    if b.shape[1] != 99:
        raise RuntimeError(f"unexpected B columns: {b.shape[1]}")
    if r.shape[1] != 107 or q.shape[1] != 107:
        raise RuntimeError("unexpected R/Q columns")
    if rn != qn or r.shape != q.shape:
        raise RuntimeError("R/Q complexity-match invariant failed")
    if rn[:len(bn)] != bn or len(rn) != len(bn) + 8:
        raise RuntimeError("relationship schema invariant failed")
    return {
        "base_columns": int(b.shape[1]),
        "residual_columns": int(r.shape[1]),
        "raw_spread_control_columns": int(q.shape[1]),
        "R_Q_schema_identical": True,
        "relationship_block_columns": 8,
        "relation_window": REL_WINDOW,
        "current_other_iv_in_base": True,
        "same_row_availability": True,
        "global_sign_invariant": True,
    }


def forward_and_fit(frame: pd.DataFrame, out: Path, identities: dict) -> None:
    feature_check = feature_identity_checks(frame)
    probes: dict[str, dict] = {}
    forward: dict[str, dict] = {}
    coverage = {}
    for h in HORIZONS:
        dev, cov = cohort(frame, (2021, 2022, 2023), h)
        train = dev[dev.year.le(2022)].reset_index(drop=True)
        hold = dev[dev.year.eq(2023)].reset_index(drop=True)
        if train.empty or hold.empty:
            raise RuntimeError(f"empty Development forward split h={h}")
        coverage[str(h)] = cov
        for endpoint in ENDPOINTS:
            fwd = {}
            for model in MODELS:
                x, names = design(train, model)
                fwd[model] = fit_probe(x, train[endpoint].to_numpy(float), names)
                xx, nn = design(dev, model)
                probes[f"{h}|{endpoint}|{model}"] = fit_probe(xx, dev[endpoint].to_numpy(float), nn)
            y = hold[endpoint].to_numpy(float)
            pr = predict(hold, "R", fwd["R"], endpoint)
            for b in ("B", "Q"):
                pb = predict(hold, b, fwd[b], endpoint)
                l0, l1 = (y - pb) ** 2, (y - pr) ** 2
                gain = l0 - l1
                forward[f"{h}|{endpoint}|{b}"] = {
                    "n": int(len(hold)), "absolute_gain": float(gain.mean()),
                    "relative_gain": float(gain.mean() / l0.mean()),
                }
    payload = {
        "schema": "cross_index_residual_dislocation_utility_v1_frozen_models",
        "source_main": SOURCE_MAIN,
        "protocol_git_blob": PROTOCOL_BLOB,
        "parent_runner_git_blob": PARENT_BLOB,
        "ridge_lambda": LAMBDA,
        "relation_window": REL_WINDOW,
        "models": probes,
        "development_forward": forward,
        "development_coverage": coverage,
        "feature_identity": feature_check,
        "input_sha256": identities,
        "training_years": [2021, 2022, 2023],
        "validation_scored": False,
        "validation_reused": True,
        "fresh_oos": False,
        "read_2026": False,
        "synthetic_2026_used": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "candidate_nominated": False,
        "production_authority": False,
        "v20_started": False,
        "d6_started": False,
    }
    model_path = out / "FROZEN_MODELS.json"
    dump_json(model_path, payload)
    model_sha = sha256_file(model_path)
    (out / "MODEL_SHA256.txt").write_text(model_sha + "\n", encoding="utf-8")
    dump_json(out / "FIT_RECEIPT.json", {
        "model_sha256": model_sha,
        "feature_identity": feature_check,
        "development_forward": forward,
        "development_coverage": coverage,
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "git_sha": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
        "validation_scored": False, "validation_reused": True, "fresh_oos": False,
        "read_2026": False, "synthetic_2026_used": False,
        "blackbox_queried": False, "pnl_computed": False,
        "candidate_nominated": False, "production_authority": False,
    })
    print(json.dumps({"fit_complete": True, "model_sha256": model_sha, "forward": forward}, indent=2), flush=True)


def descriptive_outputs(q: pd.DataFrame, h: int, out: Path) -> dict:
    cols = ["RZ48", "QZ48", "relation_beta", "shock_intensity", "other_shock_intensity",
            "vol_ratio", "other_vol_ratio"]
    corr = q[cols].corr().to_dict()
    beta = q.relation_beta.dropna().to_numpy(float)
    summary = {
        "n": int(len(q)),
        "correlations": corr,
        "beta": {
            "median": float(np.median(beta)),
            "p05": float(np.quantile(beta, .05)),
            "p95": float(np.quantile(beta, .95)),
        } if len(beta) else {"n": 0},
    }
    pd.DataFrame({
        "RZ48": q.RZ48, "QZ48": q.QZ48, "beta": q.relation_beta,
        "symbol": q.symbol, "year": q.year, "previous_state": q.previous_state,
    }).describe(include="all").to_csv(out / f"descriptive_{h}.csv")
    return summary


def validate(frame: pd.DataFrame, models_path: Path, model_sha_path: Path, out: Path, identities: dict) -> None:
    expected = model_sha_path.read_text(encoding="utf-8").strip()
    actual = sha256_file(models_path)
    if actual != expected:
        raise RuntimeError("frozen model hash mismatch")
    frozen = json.loads(models_path.read_text(encoding="utf-8"))
    if frozen.get("validation_scored") is not False or frozen.get("protocol_git_blob") != PROTOCOL_BLOB:
        raise RuntimeError("frozen model identity drift")
    if frozen.get("parent_runner_git_blob") != PARENT_BLOB:
        raise RuntimeError("parent dependency drift")

    comparisons = []
    joint = {}
    coverage = {}
    descriptive = {}
    for h in HORIZONS:
        q, cov = cohort(frame, (2024, 2025), h)
        coverage[str(h)] = {"validation": cov, "development": frozen["development_coverage"][str(h)]}
        descriptive[str(h)] = descriptive_outputs(q, h, out)
        for endpoint in ENDPOINTS:
            for b in ("B", "Q"):
                forward_gain = frozen["development_forward"][f"{h}|{endpoint}|{b}"]["absolute_gain"]
                comparisons.append(compare(
                    q, endpoint, b, frozen["models"], forward_gain,
                    frozen["models"][f"{h}|{endpoint}|R"]["n"],
                    cov["coverage"], h, out,
                ))
            subset = [x for x in comparisons if x["horizon"] == h and x["endpoint"] == endpoint]
            joint[f"{h}|{endpoint}"] = bool(len(subset) == 2 and all(x["supported"] for x in subset))

    decision = (
        "CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS"
        if any(joint.values()) else
        "CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    )
    pd.DataFrame([
        {k: v for k, v in x.items() if k not in ("gates", "slices", "ci_5day", "ci_20day_sensitivity")}
        for x in comparisons
    ]).to_csv(out / "comparisons.csv", index=False)
    dump_json(out / "VALIDATION_RESULTS.json", {
        "schema": "cross_index_residual_dislocation_utility_v1_validation",
        "decision": decision,
        "joint_endpoint_support": joint,
        "comparisons": comparisons,
        "coverage": coverage,
        "descriptive": descriptive,
        "model_sha256": actual,
        "input_sha256": identities,
        "validation_years": [2024, 2025],
        "validation_reused": True,
        "fresh_oos": False,
        "read_2026": False,
        "synthetic_2026_used": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "candidate_nominated": False,
        "production_authority": False,
        "v20_started": False,
        "d6_started": False,
        "git_sha": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
    })
    print(json.dumps({
        "decision": decision,
        "joint": joint,
        "comparisons": [{
            "comparison": x["comparison"], "horizon": x["horizon"], "endpoint": x["endpoint"],
            "relative_gain": x["relative_gain"], "absolute_gain": x["absolute_gain"],
            "supported": x["supported"], "gates": x["gates"],
        } for x in comparisons],
    }, indent=2), flush=True)


def physical_guard(root: Path, phase: str) -> None:
    base.physical_guard(root, phase)


def run(args) -> None:
    root = args.repo_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    physical_guard(root, args.phase)
    protocol = root / "research/cross_index_residual_dislocation_utility_v1/PROTOCOL.md"
    if git_blob_bytes(protocol.read_bytes()) != PROTOCOL_BLOB:
        raise RuntimeError("protocol blob drift")

    if args.phase == "fit":
        frame, identities = build_table(root, (2020, 2021, 2022, 2023), (2021, 2022, 2023))
        forward_and_fit(frame, out, identities)
        return

    if args.models is None or args.model_sha is None:
        raise ValueError("validate phase requires --models and --model-sha")
    frame, identities = build_table(
        root, (2020, 2021, 2022, 2023, 2024, 2025), (2021, 2022, 2023, 2024, 2025)
    )
    validate(frame, args.models.resolve(), args.model_sha.resolve(), out, identities)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--phase", choices=("fit", "validate"), required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--models", type=Path)
    ap.add_argument("--model-sha", type=Path)
    args = ap.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
