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
PARENT_PATH = ROOT / "research/activity_degree_incremental_utility_v1/run_study.py"
PARENT_BLOB = "b148d8ccf1d13651434b7b14b42a27dc4b31f5e6"
PROTOCOL_BLOB = "9d925368f01163b51421d5221d9a3ba4f5adaaaf"
SOURCE_MAIN = "165cfb0a56aaf3ac7c616f9d2eadd27501f2e0e6"

MODELS = ("C", "X", "L")
ENDPOINTS = ("log_future_sigma", "future_tail")
HORIZONS = (15, 30, 60)
SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
LAMBDA = 0.01
SEED = 20260915
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
        raise RuntimeError("activity-degree parent runner blob drift")
    spec = importlib.util.spec_from_file_location("cross_index_degree_parent", PARENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


base = load_parent()


def other_symbol(symbol: str) -> str:
    if symbol == SYMBOLS[0]:
        return SYMBOLS[1]
    if symbol == SYMBOLS[1]:
        return SYMBOLS[0]
    raise ValueError(symbol)


def attach_lag_std12(p: pd.DataFrame) -> pd.DataFrame:
    q = p.copy()
    q["lag_std12"] = np.nan
    for _, g in q.groupby("symbol", sort=False):
        v = g.r.dropna()
        q.loc[v.index, "lag_std12"] = v.shift(1).rolling(12, min_periods=12).std(ddof=0)
    q["lag_intensity"] = q.last_abs / q.bg48
    q["lag_ratio"] = q.lag_std12 / q.bg48
    return q


def select_snapshot(obs: pd.DataFrame, start: pd.Timestamp, decision: pd.Timestamp):
    """Latest stable source row <= decision, but never before current native bar."""
    if obs.empty:
        return None
    times = obs.obs_dt.to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(times, np.datetime64(decision.to_datetime64()), side="right") - 1)
    if pos < 0:
        return None
    row = obs.iloc[pos]
    if pd.Timestamp(row.obs_dt) < start:
        return None
    return float(row.price), pd.Timestamp(row.obs_dt), float(row.row_index)


def build_e15_snapshots(root: Path, p: pd.DataFrame, years: tuple[int, ...]) -> pd.DataFrame:
    rows: list[dict] = []
    for symbol in SYMBOLS:
        ps = p[p.symbol.eq(symbol)]
        for year in years:
            sec = base.load_3s(root, symbol, year)
            groups = {str(day): g.reset_index(drop=True) for day, g in sec.groupby("trading_day", sort=False)}
            for day, bars in ps[ps.year.eq(year)].groupby("trading_day", sort=False):
                obs = groups.get(str(day), pd.DataFrame(columns=sec.columns))
                for bar in bars.sort_values("bar_end", kind="stable").itertuples(index=False):
                    decision = pd.Timestamp(bar.bar_end) - pd.Timedelta(seconds=15)
                    start = pd.Timestamp(bar.bar_end) - pd.Timedelta(minutes=5)
                    selected = select_snapshot(obs, start, decision)
                    rec = {
                        "row_id": int(bar.row_id),
                        "symbol": symbol,
                        "trading_day": str(day),
                        "bar_end": pd.Timestamp(bar.bar_end),
                        "decision_time": decision,
                        "partial_price": np.nan,
                        "observation_time": pd.NaT,
                        "observation_age_seconds": np.nan,
                        "source_row_index": np.nan,
                        "current_snapshot_available": False,
                    }
                    if selected is not None:
                        price, obs_time, source_row = selected
                        rec.update({
                            "partial_price": price,
                            "observation_time": obs_time,
                            "observation_age_seconds": float((decision - obs_time).total_seconds()),
                            "source_row_index": source_row,
                            "current_snapshot_available": True,
                        })
                    rows.append(rec)
            del sec, groups
    z = pd.DataFrame(rows)
    if z.duplicated("row_id").any():
        raise RuntimeError("duplicate E15 snapshot row_id")
    return z


def attach_current_coordinates(p: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    q = p.merge(snapshots, on=["row_id", "symbol", "trading_day", "bar_end"], how="left", validate="one_to_one")
    q["partial_return"] = np.log(q.partial_price / q.prev_close)
    q["shock_intensity"] = q.partial_return.abs() / q.bg48
    mean12 = (q.prev11_sum + q.partial_return) / 12.0
    var12 = (q.prev11_sq + q.partial_return.pow(2)) / 12.0 - mean12.pow(2)
    q["vol_ratio"] = np.sqrt(np.maximum(var12, 0.0)) / q.bg48
    history_cols = ["bg48", "last_abs", "rms3", "rms6", "rms12", "rms48", "prev11_sum", "prev11_sq", "prev_close"]
    q["base_available"] = q[history_cols].notna().all(axis=1)
    q["base_available"] &= q.previous_state.isin(STATES)
    q["base_available"] &= q.current_snapshot_available.fillna(False)
    q["base_available"] &= np.isfinite(q.shock_intensity) & np.isfinite(q.vol_ratio) & q.bg48.gt(0)
    q["lag_available"] = np.isfinite(q.lag_intensity) & np.isfinite(q.lag_ratio)
    return q


def pair_other(frame: pd.DataFrame) -> pd.DataFrame:
    other = frame[[
        "symbol", "trading_day", "bar_end", "decision_time",
        "shock_intensity", "vol_ratio", "lag_intensity", "lag_ratio",
        "base_available", "lag_available", "observation_time", "observation_age_seconds",
    ]].copy()
    other["symbol"] = other.symbol.map(other_symbol)
    other = other.rename(columns={
        "shock_intensity": "other_shock_intensity",
        "vol_ratio": "other_vol_ratio",
        "lag_intensity": "other_lag_intensity",
        "lag_ratio": "other_lag_ratio",
        "base_available": "other_current_available",
        "lag_available": "other_lag_available",
        "observation_time": "other_observation_time",
        "observation_age_seconds": "other_observation_age_seconds",
    })
    keys = ["symbol", "trading_day", "bar_end", "decision_time"]
    q = frame.merge(other, on=keys, how="left", validate="one_to_one")
    q["paired_available"] = q.base_available & q.other_current_available.fillna(False) & q.other_lag_available.fillna(False)
    for c in ("other_shock_intensity", "other_vol_ratio", "other_lag_intensity", "other_lag_ratio"):
        q["paired_available"] &= np.isfinite(q[c])
    return q


def build_table(root: Path, years_5m: tuple[int, ...], years_3s: tuple[int, ...]) -> tuple[pd.DataFrame, dict]:
    raw = base.load_5m(root, years_5m)
    hist = attach_lag_std12(base.attach_history(raw))
    snapshots = build_e15_snapshots(root, hist, years_3s)
    feat = pair_other(attach_current_coordinates(hist, snapshots))
    labelled = base.attach_labels(feat)
    identities = {"5m": {}, "3s": {}, "parent_runner_git_blob": PARENT_BLOB}
    for symbol in SYMBOLS:
        for year in years_5m:
            path = root / "data/market/5m" / symbol / f"{year}.parquet"
            identities["5m"][f"{symbol}:{year}"] = sha256_file(path)
        for year in years_3s:
            path = root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"
            identities["3s"][f"{symbol}:{year}"] = sha256_file(path)
    return labelled, identities


def design(q: pd.DataFrame, model: str) -> tuple[np.ndarray, list[str]]:
    if model not in MODELS:
        raise ValueError(model)
    x0, names0 = base.design(q, "C")
    if model == "C":
        return x0, names0
    if model == "X":
        i = q.other_shock_intensity.to_numpy(float)
        v0 = q.other_vol_ratio.to_numpy(float)
    else:
        i = q.other_lag_intensity.to_numpy(float)
        v0 = q.other_lag_ratio.to_numpy(float)
    u = np.log1p(i)
    v = np.log(np.maximum(v0, 1e-12))
    terms = {
        "other_intensity": u,
        "other_ratio": v,
        "other_intensity2": u*u,
        "other_ratio2": v*v,
        "other_cross": u*v,
    }
    extra: list[np.ndarray] = []
    names: list[str] = []
    for name, values in terms.items():
        extra.append(values)
        names.append(name)
        for symbol in SYMBOLS:
            extra.append(values * q.symbol.eq(symbol).to_numpy(float))
            names.append(f"{name}:target:{symbol}")
    xx = np.column_stack([x0] + extra).astype(float)
    if not np.isfinite(xx).all():
        raise ValueError("nonfinite cross-index design")
    return xx, names0 + names


def fit_probe(x: np.ndarray, y: np.ndarray, names: list[str]) -> dict:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-14] = 1.0
    z = (x - mean) / scale
    intercept = float(np.mean(y))
    beta = np.linalg.solve(z.T @ z / len(z) + LAMBDA * np.eye(z.shape[1]), z.T @ (y - intercept) / len(z))
    return {"names": names, "mean": mean.tolist(), "scale": scale.tolist(), "beta": beta.tolist(), "intercept": intercept, "n": int(len(y))}


def predict(q: pd.DataFrame, model: str, probe: dict, endpoint: str) -> np.ndarray:
    x, names = design(q, model)
    if names != probe["names"]:
        raise RuntimeError("feature schema drift")
    value = ((x - np.asarray(probe["mean"])) / np.asarray(probe["scale"])) @ np.asarray(probe["beta"]) + float(probe["intercept"])
    return np.clip(value, 0, 1) if endpoint == "future_tail" else value


def cohort(frame: pd.DataFrame, years: tuple[int, ...], h: int) -> tuple[pd.DataFrame, dict]:
    in_year = frame.year.isin(years)
    base_future = in_year & frame.base_available & frame[f"label_ok_{h}"].fillna(False)
    final = base_future & frame.paired_available
    z = frame.loc[final].copy().reset_index(drop=True)
    z["sigma"] = z[f"sigma_{h}"]
    z["log_future_sigma"] = z[f"log_future_sigma_{h}"]
    z["future_tail"] = z[f"future_tail_{h}"]
    counts = {
        "target_rows": int(in_year.sum()),
        "target_base_available": int((in_year & frame.base_available).sum()),
        "target_base_and_future_feasible": int(base_future.sum()),
        "other_current_available": int((base_future & frame.other_current_available.fillna(False)).sum()),
        "other_lag_available": int((base_future & frame.other_lag_available.fillna(False)).sum()),
        "paired_final": int(final.sum()),
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
    lo, hi = np.quantile(gains / count, [a, 1-a])
    return {"low": float(lo), "high": float(hi), "blocks": int(len(blocks)), "repetitions": BOOTSTRAPS}


def compare(q: pd.DataFrame, endpoint: str, base_model: str, probes: dict, forward_gain: float,
            dev_n: int, coverage: float, h: int, out: Path) -> dict:
    y = q[endpoint].to_numpy(float)
    px = predict(q, "X", probes[f"{h}|{endpoint}|X"], endpoint)
    pb = predict(q, base_model, probes[f"{h}|{endpoint}|{base_model}"], endpoint)
    l0 = (y - pb) ** 2
    l1 = (y - px) ** 2
    gain = l0 - l1
    absolute = float(gain.mean())
    relative = float(absolute / l0.mean())
    slices = {}
    for col in ("year", "symbol"):
        for key, inds in q.groupby(col, sort=True).indices.items():
            slices[f"{col}:{key}"] = {
                "n": int(len(inds)), "absolute_gain": float(gain[inds].mean()),
                "relative_gain": float(gain[inds].mean() / l0[inds].mean()),
            }
    ci = {}
    for days in (5, 20):
        blocks = block_stats(q, gain, days)
        blocks.to_csv(out / f"blocks_{h}_{endpoint}_X_vs_{base_model}_{days}d.csv", index=False, float_format="%.17g")
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
        "horizon": h, "endpoint": endpoint, "comparison": f"X_vs_{base_model}", "n": int(len(q)),
        "development_n": int(dev_n), "positive_events": int(y.sum()) if endpoint == "future_tail" else None,
        "baseline_loss": float(l0.mean()), "cross_current_loss": float(l1.mean()),
        "absolute_gain": absolute, "relative_gain": relative,
        "ci_5day": ci["5"], "ci_20day_sensitivity": ci["20"], "slices": slices,
        "development_forward_gain": float(forward_gain), "gates": gates,
        "supported": bool(all(gates.values())),
    }


def feature_identity_checks(frame: pd.DataFrame) -> dict:
    z = frame[frame.paired_available].head(200).copy()
    if z.empty:
        raise RuntimeError("no paired feature rows")
    c, cn = design(z, "C")
    x, xn = design(z, "X")
    l, ln = design(z, "L")
    if xn != ln or x.shape != l.shape or x.shape[1] - c.shape[1] != 15:
        raise RuntimeError("X/L complexity-match invariant failed")
    if xn[:len(cn)] != cn or len(xn) != len(cn) + 15:
        raise RuntimeError("cross-index schema invariant failed")
    return {
        "base_columns": int(c.shape[1]), "cross_current_columns": int(x.shape[1]),
        "lag_control_columns": int(l.shape[1]), "X_L_schema_identical": True,
        "cross_block_columns": 15,
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
            px = predict(hold, "X", fwd["X"], endpoint)
            for b in ("C", "L"):
                pb = predict(hold, b, fwd[b], endpoint)
                l0, l1 = (y-pb)**2, (y-px)**2
                gain = l0-l1
                forward[f"{h}|{endpoint}|{b}"] = {
                    "n": int(len(hold)), "absolute_gain": float(gain.mean()),
                    "relative_gain": float(gain.mean()/l0.mean()),
                }
    payload = {
        "schema": "cross_index_degree_transfer_utility_v1_frozen_models",
        "source_main": SOURCE_MAIN,
        "protocol_git_blob": PROTOCOL_BLOB,
        "parent_runner_git_blob": PARENT_BLOB,
        "ridge_lambda": LAMBDA,
        "cross_block_columns": 15,
        "models": probes,
        "development_forward": forward,
        "development_coverage": coverage,
        "feature_identity": feature_check,
        "input_sha256": identities,
        "training_years": [2021, 2022, 2023],
        "validation_scored": False,
        "validation_reused": True,
        "fresh_oos": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "production_authority": False,
    }
    model_path = out / "FROZEN_MODELS.json"
    dump_json(model_path, payload)
    model_sha = sha256_file(model_path)
    (out / "MODEL_SHA256.txt").write_text(model_sha + "\n", encoding="utf-8")
    dump_json(out / "FIT_RECEIPT.json", {
        "model_sha256": model_sha, "feature_identity": feature_check,
        "development_forward": forward, "development_coverage": coverage,
        "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "git_sha": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
        "validation_scored": False, "blackbox_queried": False, "production_authority": False,
    })
    print(json.dumps({"fit_complete": True, "model_sha256": model_sha, "forward": forward}, indent=2), flush=True)


def descriptive_outputs(q: pd.DataFrame, probes: dict, h: int, out: Path) -> dict:
    corr_cols = ["shock_intensity", "vol_ratio", "other_shock_intensity", "other_vol_ratio", "other_lag_intensity", "other_lag_ratio"]
    corr = q[corr_cols].corr().to_dict()
    ages = {}
    for name in ("observation_age_seconds", "other_observation_age_seconds"):
        s = q[name].dropna().to_numpy(float)
        ages[name] = {
            "n": int(len(s)), "median": float(np.median(s)), "p95": float(np.quantile(s, .95)),
            "max": float(np.max(s)),
        } if len(s) else {"n": 0}
    slice_rows = []
    decile_rows = []
    for endpoint in ENDPOINTS:
        pc = predict(q, "C", probes[f"{h}|{endpoint}|C"], endpoint)
        px = predict(q, "X", probes[f"{h}|{endpoint}|X"], endpoint)
        pl = predict(q, "L", probes[f"{h}|{endpoint}|L"], endpoint)
        y = q[endpoint].to_numpy(float)
        for b, pb in (("C", pc), ("L", pl)):
            gain = (y-pb)**2 - (y-px)**2
            for col in ("symbol", "year", "previous_state", "slot"):
                for key, inds in q.groupby(col, sort=True).indices.items():
                    slice_rows.append({
                        "horizon": h, "endpoint": endpoint, "comparison": f"X_vs_{b}",
                        "slice_type": col, "slice": str(key), "n": int(len(inds)),
                        "absolute_gain": float(gain[inds].mean()),
                    })
        increment = px - pc
        dec = pd.qcut(pd.Series(increment), 10, labels=False, duplicates="drop")
        tmp = pd.DataFrame({"decile": dec, "sigma": q.sigma.to_numpy(float), "tail": q.future_tail.to_numpy(float), "increment": increment})
        for d, g in tmp.groupby("decile", dropna=False, sort=True):
            decile_rows.append({
                "horizon": h, "endpoint": endpoint, "increment_decile": None if pd.isna(d) else int(d),
                "n": int(len(g)), "increment_mean": float(g.increment.mean()),
                "sigma_mean": float(g.sigma.mean()), "tail_rate": float(g.tail.mean()),
            })
    pd.DataFrame(slice_rows).to_csv(out / f"slice_gains_{h}.csv", index=False)
    pd.DataFrame(decile_rows).to_csv(out / f"increment_deciles_{h}.csv", index=False)
    return {"correlations": corr, "observation_age": ages, "n": int(len(q))}


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
        descriptive[str(h)] = descriptive_outputs(q, frozen["models"], h, out)
        for endpoint in ENDPOINTS:
            for b in ("C", "L"):
                forward_gain = frozen["development_forward"][f"{h}|{endpoint}|{b}"]["absolute_gain"]
                comparisons.append(compare(
                    q, endpoint, b, frozen["models"], forward_gain,
                    frozen["models"][f"{h}|{endpoint}|X"]["n"], cov["coverage"], h, out,
                ))
            subset = [x for x in comparisons if x["horizon"] == h and x["endpoint"] == endpoint]
            joint[f"{h}|{endpoint}"] = bool(len(subset) == 2 and all(x["supported"] for x in subset))
    decision = (
        "CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS"
        if any(joint.values()) else "CROSS_INDEX_CURRENT_DEGREE_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    )
    pd.DataFrame([{k: v for k, v in x.items() if k not in ("gates", "slices", "ci_5day", "ci_20day_sensitivity")} for x in comparisons]).to_csv(out / "comparisons.csv", index=False)
    dump_json(out / "VALIDATION_RESULTS.json", {
        "schema": "cross_index_degree_transfer_utility_v1_validation",
        "decision": decision, "joint_endpoint_support": joint, "comparisons": comparisons,
        "coverage": coverage, "descriptive": descriptive, "model_sha256": actual,
        "input_sha256": identities, "validation_years": [2024, 2025], "validation_reused": True,
        "fresh_oos": False, "read_2026": False, "blackbox_queried": False,
        "pnl_computed": False, "candidate_nominated": False, "production_authority": False,
        "v20_started": False, "d6_started": False,
        "git_sha": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
    })
    print(json.dumps({
        "decision": decision, "joint": joint,
        "comparisons": [{
            "comparison": x["comparison"], "horizon": x["horizon"], "endpoint": x["endpoint"],
            "relative_gain": x["relative_gain"], "absolute_gain": x["absolute_gain"],
            "supported": x["supported"], "gates": x["gates"],
        } for x in comparisons],
    }, indent=2), flush=True)


def physical_guard(root: Path, phase: str) -> None:
    if (root / "data/cross_index_risk_gate_2026_v1").exists():
        raise RuntimeError("2026 protected data present")
    if phase == "fit":
        forbidden = []
        for symbol in SYMBOLS:
            for year in (2024, 2025, 2026):
                for p in (
                    root / "data/market/5m" / symbol / f"{year}.parquet",
                    root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet",
                ):
                    if p.exists():
                        forbidden.append(str(p))
        if forbidden:
            raise RuntimeError(f"fit workspace contains Validation data: {forbidden[:4]}")


def run(args) -> None:
    root = args.repo_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    physical_guard(root, args.phase)
    protocol = root / "research/cross_index_degree_transfer_utility_v1/PROTOCOL.md"
    if git_blob_bytes(protocol.read_bytes()) != PROTOCOL_BLOB:
        raise RuntimeError("protocol blob drift")
    if args.phase == "fit":
        frame, identities = build_table(root, (2020, 2021, 2022, 2023), (2021, 2022, 2023))
        forward_and_fit(frame, out, identities)
        return
    if args.models is None or args.model_sha is None:
        raise ValueError("validate phase requires --models and --model-sha")
    frame, identities = build_table(root, (2020, 2021, 2022, 2023, 2024, 2025), (2021, 2022, 2023, 2024, 2025))
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
