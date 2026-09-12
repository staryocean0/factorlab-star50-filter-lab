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
PROTOCOL_BLOB = "e6b78e63c165a0532d1534ac717f26f1f9afcf2c"
SOURCE_MAIN = "b9a6a47b2aca8ea9dddec1aab69c19ae0ae92311"

MODELS = ("B", "O", "L")
ENDPOINTS = ("log_future_sigma", "future_tail")
HORIZONS = (15, 30, 60)
SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
LAMBDA = 0.01
SEED = 20260919
BOOTSTRAPS = 5000
FAMILY = 12
CURRENT_RETURNS = 19


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
    spec = importlib.util.spec_from_file_location("current_path_order_parent", PARENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


parent = load_parent()


def path_coordinates(returns_bp: np.ndarray) -> dict[str, float] | None:
    r = np.asarray(returns_bp, dtype=float)
    if r.shape != (CURRENT_RETURNS,) or not np.isfinite(r).all():
        return None
    energy = float(np.sum(r * r))
    tv = float(np.sum(np.abs(r)))
    if not (energy > 0 and tv > 0):
        return None
    root = float(np.sqrt(energy))
    cum = np.r_[0.0, np.cumsum(r)]
    rtv = float((np.max(cum) - np.min(cum)) / tv)
    ap = float(np.sum(r[1:] * r[:-1]) / energy)
    l1l2 = float(tv / (np.sqrt(float(CURRENT_RETURNS)) * root))
    maxl2 = float(np.max(np.abs(r)) / root)
    tol = 1e-12
    if not (-tol <= rtv <= 1 + tol):
        raise RuntimeError(f"RTV19 bound drift: {rtv}")
    if not (-1 - tol <= ap <= 1 + tol):
        raise RuntimeError(f"AP19 bound drift: {ap}")
    if not (0 < l1l2 <= 1 + tol and 0 < maxl2 <= 1 + tol):
        raise RuntimeError("magnitude-shape bound drift")
    return {
        "l1l2_19": l1l2,
        "maxl2_19": maxl2,
        "rtv19": rtv,
        "ap19": ap,
    }


def build_fine_order_e15(root: Path, p: pd.DataFrame, years: tuple[int, ...]) -> pd.DataFrame:
    """Parent strict M3 path plus frozen current-bar 19-return morphology."""
    out: list[dict] = []
    for symbol in SYMBOLS:
        ps = p[p.symbol.eq(symbol)]
        for year in years:
            sec = parent.load_3s(root, symbol, year)
            local = sec.obs_dt
            sec["afternoon"] = (local.dt.hour >= 13).astype(int)
            sec["second_day"] = local.dt.hour * 3600 + local.dt.minute * 60 + local.dt.second
            sec["second"] = sec.second_day - np.where(sec.afternoon.eq(1), 13 * 3600, 9 * 3600 + 30 * 60)
            sec = sec[sec.second.between(0, 7200)].copy()
            groups = {(str(d), int(a)): g for (d, a), g in sec.groupby(["trading_day", "afternoon"], sort=False)}
            py = ps[ps.year.eq(year)]
            for (day, aft), bars in py.groupby(["trading_day", "afternoon"], sort=False):
                bars = bars.sort_values("bar_end", kind="stable")
                raw = groups.get((str(day), int(aft)))
                sample = parent.sample_session(np.array([]), np.array([]), np.array([])) if raw is None else parent.sample_session(
                    raw.second.to_numpy(float), raw.price.to_numpy(float), raw.row_index.to_numpy())
                price, r15, age = sample["price"], sample["return_bp"], sample["age"]
                start = pd.Timestamp(f"{day} {'13:00:00' if int(aft) else '09:30:00'}")
                for row in bars.itertuples(index=False):
                    decision = pd.Timestamp(row.bar_end) - pd.Timedelta(seconds=15)
                    second = int((decision - start).total_seconds())
                    if second < 0 or second > 7200 or second % 15:
                        raise RuntimeError(f"E15 not on strict grid: {symbol} {row.bar_end}")
                    j = second // 15
                    rec = {
                        "row_id": int(row.row_id), "symbol": symbol, "trading_day": str(day),
                        "year": int(year), "afternoon": int(aft), "slot": int(row.slot),
                        "decision_time": decision,
                        "fine_complete": False, "pre5m_range_bp": np.nan,
                        "A5": np.nan, "partial_price": np.nan, "endpoint_age_seconds": np.nan,
                        "path19_complete": False,
                        "l1l2_19": np.nan, "maxl2_19": np.nan, "rtv19": np.nan, "ap19": np.nan,
                    }
                    # Parent M3 path: previous physical five minutes through E15 = 20 returns / 21 prices.
                    if j >= 20:
                        rr20 = r15[j - 19 : j + 1]
                        px21 = price[j - 20 : j + 1]
                        complete20 = (
                            len(rr20) == 20 and len(px21) == 21 and np.isfinite(rr20).all()
                            and np.isfinite(px21).all() and (px21 > 0).all()
                        )
                        rec["fine_complete"] = bool(complete20)
                        if complete20:
                            rel = np.log(px21 / px21[0]) * 1e4
                            rec["pre5m_range_bp"] = float(rel.max() - rel.min())
                            rec["A5"] = float(np.sqrt(np.mean(rr20 * rr20)))
                            rec["partial_price"] = float(px21[-1])
                            rec["endpoint_age_seconds"] = float(age[j])
                            if rec["endpoint_age_seconds"] > 3:
                                raise RuntimeError("strict M3 endpoint age drift")
                    # Current native-bar path: bar start through E15 = exactly 19 returns / 20 prices.
                    if j >= 19:
                        rr19 = r15[j - 18 : j + 1]
                        px20 = price[j - 19 : j + 1]
                        complete19 = (
                            len(rr19) == CURRENT_RETURNS and len(px20) == CURRENT_RETURNS + 1
                            and np.isfinite(rr19).all() and np.isfinite(px20).all() and (px20 > 0).all()
                        )
                        coords = path_coordinates(rr19) if complete19 else None
                        rec["path19_complete"] = coords is not None
                        if coords is not None:
                            rec.update(coords)
                    out.append(rec)
            del sec, groups
    z = pd.DataFrame(out)
    if z.duplicated("row_id").any():
        raise RuntimeError("duplicate E15 fine/order row")
    return z


def attach_m3_and_lag(fine: pd.DataFrame) -> pd.DataFrame:
    z = parent.attach_m3(fine)
    z = z.sort_values(["symbol", "trading_day", "afternoon", "decision_time"], kind="stable")
    for c in ("rtv19", "ap19"):
        z[f"{c}_lag"] = z.groupby(["symbol", "trading_day", "afternoon"], sort=False)[c].shift(1)
    return z.sort_values("row_id", kind="stable").reset_index(drop=True)


def build_table(root: Path, years_5m: tuple[int, ...], years_3s: tuple[int, ...]) -> tuple[pd.DataFrame, dict]:
    raw = parent.load_5m(root, years_5m)
    hist = parent.attach_history(raw)
    fine = attach_m3_and_lag(build_fine_order_e15(root, hist, years_3s))
    feat = parent.attach_partial_coordinates(hist, fine)
    feat["m3_current_available"] = np.isfinite(feat.M3)
    mag_cols = ["l1l2_19", "maxl2_19"]
    order_cols = ["rtv19", "ap19"]
    lag_cols = ["rtv19_lag", "ap19_lag"]
    feat["magnitude_available"] = feat[mag_cols].notna().all(axis=1) & np.isfinite(feat[mag_cols]).all(axis=1)
    feat["current_order_available"] = feat[order_cols].notna().all(axis=1) & np.isfinite(feat[order_cols]).all(axis=1)
    feat["lag_order_available"] = feat[lag_cols].notna().all(axis=1) & np.isfinite(feat[lag_cols]).all(axis=1)
    labelled = parent.attach_labels(feat)
    identities = {"5m": {}, "3s": {}, "parent_runner_git_blob": PARENT_BLOB}
    for symbol in SYMBOLS:
        for year in years_5m:
            path = root / "data/market/5m" / symbol / f"{year}.parquet"
            identities["5m"][f"{symbol}:{year}"] = sha256_file(path)
        for year in years_3s:
            path = root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"
            identities["3s"][f"{symbol}:{year}"] = sha256_file(path)
    return labelled, identities


def pair_block(q: pd.DataFrame, x: np.ndarray, y: np.ndarray, prefix: str) -> tuple[list[np.ndarray], list[str]]:
    terms = {
        f"{prefix}_x": x,
        f"{prefix}_y": y,
        f"{prefix}_x2": x * x,
        f"{prefix}_y2": y * y,
        f"{prefix}_cross": x * y,
    }
    arrays: list[np.ndarray] = []
    names: list[str] = []
    for name, values in terms.items():
        arrays.append(values)
        names.append(name)
        for state in STATES:
            mask = q.previous_state.eq(state).to_numpy(float)
            arrays.append(values * mask)
            names.append(f"{name}:{state}")
    return arrays, names


def design(q: pd.DataFrame, model: str) -> tuple[np.ndarray, list[str]]:
    if model not in MODELS:
        raise ValueError(model)
    parent_x, parent_names = parent.design(q, "A")  # D4-style C + current M3 block.
    mx = q.l1l2_19.to_numpy(float)
    my = q.maxl2_19.to_numpy(float)
    mag_arrays, mag_names = pair_block(q, mx, my, "magnitude19")
    arrays: list[np.ndarray] = [parent_x] + mag_arrays
    names = parent_names + mag_names
    if model in ("O", "L"):
        if model == "O":
            ox, oy = q.rtv19.to_numpy(float), q.ap19.to_numpy(float)
        else:
            ox, oy = q.rtv19_lag.to_numpy(float), q.ap19_lag.to_numpy(float)
        order_arrays, order_names = pair_block(q, ox, oy, "order19")
        arrays.extend(order_arrays)
        names.extend(order_names)
    x = np.column_stack(arrays).astype(float)
    if not np.isfinite(x).all():
        raise ValueError("nonfinite current path-order design")
    return x, names


def fit_probe(x: np.ndarray, y: np.ndarray, names: list[str]) -> dict:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-14] = 1.0
    z = (x - mean) / scale
    intercept = float(np.mean(y))
    beta = np.linalg.solve(z.T @ z / len(z) + LAMBDA * np.eye(z.shape[1]), z.T @ (y - intercept) / len(z))
    return {
        "names": names, "mean": mean.tolist(), "scale": scale.tolist(),
        "beta": beta.tolist(), "intercept": intercept, "n": int(len(y)),
    }


def predict(q: pd.DataFrame, model: str, probe: dict, endpoint: str) -> np.ndarray:
    x, names = design(q, model)
    if names != probe["names"]:
        raise RuntimeError("feature schema drift")
    value = ((x - np.asarray(probe["mean"])) / np.asarray(probe["scale"])) @ np.asarray(probe["beta"]) + float(probe["intercept"])
    return np.clip(value, 0, 1) if endpoint == "future_tail" else value


def cohort(frame: pd.DataFrame, years: tuple[int, ...], h: int) -> tuple[pd.DataFrame, dict]:
    y = frame.year.isin(years)
    b = (
        y & frame.base_available & frame.fine_complete.fillna(False) & frame.m3_current_available.fillna(False)
        & frame.magnitude_available.fillna(False) & frame[f"label_ok_{h}"].fillna(False)
    )
    final = b & frame.current_order_available.fillna(False) & frame.lag_order_available.fillna(False)
    z = frame.loc[final].copy().reset_index(drop=True)
    z["sigma"] = z[f"sigma_{h}"]
    z["log_future_sigma"] = z[f"log_future_sigma_{h}"]
    z["future_tail"] = z[f"future_tail_{h}"]
    counts = {
        "all_e15_rows": int(y.sum()),
        "base_history_and_iv": int((y & frame.base_available).sum()),
        "strict_parent_path_complete": int((y & frame.base_available & frame.fine_complete.fillna(False)).sum()),
        "baseline_B_future_feasible": int(b.sum()),
        "current_order_available": int((b & frame.current_order_available.fillna(False)).sum()),
        "lag_order_available_final": int(final.sum()),
        "final": int(final.sum()),
        "coverage": float(final.sum() / b.sum()) if b.sum() else 0.0,
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
    po = predict(q, "O", probes[f"{h}|{endpoint}|O"], endpoint)
    pb = predict(q, base_model, probes[f"{h}|{endpoint}|{base_model}"], endpoint)
    l0 = (y - pb) ** 2
    l1 = (y - po) ** 2
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
        blocks.to_csv(out / f"blocks_{h}_{endpoint}_O_vs_{base_model}_{days}d.csv", index=False, float_format="%.17g")
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
        "horizon": h, "endpoint": endpoint, "comparison": f"O_vs_{base_model}", "n": int(len(q)),
        "development_n": int(dev_n), "positive_events": int(y.sum()) if endpoint == "future_tail" else None,
        "baseline_loss": float(l0.mean()), "order_loss": float(l1.mean()),
        "absolute_gain": absolute, "relative_gain": relative,
        "ci_5day": ci["5"], "ci_20day_sensitivity": ci["20"],
        "slices": slices, "development_forward_gain": float(forward_gain),
        "gates": gates, "supported": bool(all(gates.values())),
    }


def feature_identity_checks(frame: pd.DataFrame) -> dict:
    z = frame[
        frame.base_available & frame.fine_complete.fillna(False) & frame.m3_current_available.fillna(False)
        & frame.magnitude_available.fillna(False) & frame.current_order_available.fillna(False)
        & frame.lag_order_available.fillna(False)
    ].head(200).copy()
    if z.empty:
        raise RuntimeError("no current path-order feature rows")
    b, bn = design(z, "B")
    o, on = design(z, "O")
    l, ln = design(z, "L")
    if o.shape != l.shape or on != ln:
        raise RuntimeError("O/L complexity-match invariant failed")
    if on[:len(bn)] != bn or ln[:len(bn)] != bn:
        raise RuntimeError("B prefix schema drift")
    if (b.shape[1], o.shape[1], l.shape[1]) != (112, 132, 132):
        raise RuntimeError(f"unexpected feature counts B/O/L={b.shape[1]}/{o.shape[1]}/{l.shape[1]}")
    if not (z.rtv19.between(-1e-12, 1 + 1e-12).all() and z.ap19.between(-1 - 1e-12, 1 + 1e-12).all()):
        raise RuntimeError("current order coordinate bound failed")
    return {
        "baseline_B_columns": int(b.shape[1]),
        "current_order_O_columns": int(o.shape[1]),
        "lag_order_L_columns": int(l.shape[1]),
        "O_L_schema_identical": True,
        "magnitude_block_columns": 20,
        "order_block_columns": 20,
        "current_path_returns": CURRENT_RETURNS,
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
            po = predict(hold, "O", fwd["O"], endpoint)
            for b in ("B", "L"):
                pb = predict(hold, b, fwd[b], endpoint)
                l0, l1 = (y - pb) ** 2, (y - po) ** 2
                gain = l0 - l1
                forward[f"{h}|{endpoint}|{b}"] = {
                    "n": int(len(hold)), "absolute_gain": float(gain.mean()),
                    "relative_gain": float(gain.mean() / l0.mean()),
                }
    payload = {
        "schema": "current_path_order_utility_v1_frozen_models",
        "source_main": SOURCE_MAIN,
        "protocol_git_blob": PROTOCOL_BLOB,
        "parent_runner_git_blob": PARENT_BLOB,
        "ridge_lambda": LAMBDA,
        "current_path_returns": CURRENT_RETURNS,
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
        "validation_scored": False, "read_2026": False, "blackbox_queried": False,
        "pnl_computed": False, "production_authority": False,
    })
    print(json.dumps({"fit_complete": True, "model_sha256": model_sha, "forward": forward}, indent=2), flush=True)


def descriptive_outputs(q: pd.DataFrame, probes: dict, h: int, out: Path) -> dict:
    cols = ["shock_intensity", "vol_ratio", "M3", "l1l2_19", "maxl2_19", "rtv19", "ap19", "rtv19_lag", "ap19_lag"]
    corr = q[cols].corr().to_dict()
    summary = {}
    for c in cols:
        summary[c] = {
            "mean": float(q[c].mean()), "median": float(q[c].median()),
            "p05": float(q[c].quantile(0.05)), "p95": float(q[c].quantile(0.95)),
        }
    slice_rows = []
    for endpoint in ENDPOINTS:
        po = predict(q, "O", probes[f"{h}|{endpoint}|O"], endpoint)
        y = q[endpoint].to_numpy(float)
        for b in ("B", "L"):
            pb = predict(q, b, probes[f"{h}|{endpoint}|{b}"], endpoint)
            gain = (y - pb) ** 2 - (y - po) ** 2
            for col in ("symbol", "year", "previous_state", "slot"):
                for key, inds in q.groupby(col, sort=True).indices.items():
                    slice_rows.append({
                        "horizon": h, "endpoint": endpoint, "comparison": f"O_vs_{b}",
                        "slice_type": col, "slice": str(key), "n": int(len(inds)),
                        "absolute_gain": float(gain[inds].mean()),
                    })
    pd.DataFrame(slice_rows).to_csv(out / f"slice_gains_{h}.csv", index=False)
    return {"correlations": corr, "coordinate_summary": summary, "n": int(len(q))}


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
            for b in ("B", "L"):
                forward_gain = frozen["development_forward"][f"{h}|{endpoint}|{b}"]["absolute_gain"]
                comparisons.append(compare(
                    q, endpoint, b, frozen["models"], forward_gain,
                    frozen["models"][f"{h}|{endpoint}|O"]["n"], cov["coverage"], h, out,
                ))
            subset = [x for x in comparisons if x["horizon"] == h and x["endpoint"] == endpoint]
            joint[f"{h}|{endpoint}"] = bool(len(subset) == 2 and all(x["supported"] for x in subset))
    decision = (
        "CURRENT_E15_PATH_ORDER_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS"
        if any(joint.values()) else "CURRENT_E15_PATH_ORDER_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    )
    pd.DataFrame([
        {k: v for k, v in x.items() if k not in ("gates", "slices", "ci_5day", "ci_20day_sensitivity")}
        for x in comparisons
    ]).to_csv(out / "comparisons.csv", index=False)
    dump_json(out / "VALIDATION_RESULTS.json", {
        "schema": "current_path_order_utility_v1_validation",
        "decision": decision, "joint_endpoint_support": joint,
        "comparisons": comparisons, "coverage": coverage, "descriptive": descriptive,
        "model_sha256": actual, "input_sha256": identities,
        "validation_years": [2024, 2025], "validation_reused": True, "fresh_oos": False,
        "read_2026": False, "blackbox_queried": False, "pnl_computed": False,
        "candidate_nominated": False, "production_authority": False,
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
    if git_blob_bytes((HERE / "PROTOCOL.md").read_bytes()) != PROTOCOL_BLOB:
        raise RuntimeError("protocol blob drift")
    physical_guard(root, args.phase)
    if args.phase == "fit":
        frame, identities = build_table(root, (2020, 2021, 2022, 2023), (2021, 2022, 2023))
        forward_and_fit(frame, out, identities)
    else:
        if args.models is None or args.model_sha is None:
            raise RuntimeError("validate requires --models and --model-sha")
        frame, identities = build_table(root, (2020, 2021, 2022, 2023, 2024, 2025), (2021, 2022, 2023, 2024, 2025))
        validate(frame, args.models.resolve(), args.model_sha.resolve(), out, identities)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--phase", choices=("fit", "validate"), required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--models", type=Path)
    ap.add_argument("--model-sha", type=Path)
    args = ap.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
