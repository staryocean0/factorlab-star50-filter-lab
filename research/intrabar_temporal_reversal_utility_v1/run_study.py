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
PARENT_PATH = ROOT / "research/degree_trajectory_utility_v1/run_study.py"
PARENT_BLOB = "0afc45e5061f45f544ecc7ee4519eae4e5204bca"
PROTOCOL_BLOB = "f801991737fb1dc043807cb5f3e4fd9fb17f1187"
SOURCE_MAIN = "b9a6a47b2aca8ea9dddec1aab69c19ae0ae92311"

MODELS = ("C", "T", "O")
ENDPOINTS = ("log_future_sigma", "future_tail")
HORIZONS = (15, 30, 60)
SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
LAMBDA = 0.01
SEED = 20260912
BOOTSTRAPS = 5000
FAMILY = 12
INTRABAR_RETURNS = 19


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
        raise RuntimeError("degree-trajectory parent runner blob drift")
    spec = importlib.util.spec_from_file_location("intrabar_temporal_parent", PARENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


parent = load_parent()
activity = parent.parent.base


def temporal_coordinates(rr: np.ndarray, bg48: float) -> dict[str, float] | None:
    r = np.asarray(rr, dtype=float)
    if r.shape != (INTRABAR_RETURNS,) or not np.isfinite(r).all():
        return None
    if not np.isfinite(bg48) or bg48 <= 0:
        return None

    left = r[:-1]
    right = r[1:]
    sign_pair = (left != 0) & (right != 0)
    pair_n = int(sign_pair.sum())
    left_energy = float(np.dot(left, left))
    right_energy = float(np.dot(right, right))
    energy = float(np.dot(r, r))
    path = float(np.abs(r).sum())
    if pair_n == 0 or left_energy <= 0 or right_energy <= 0 or energy <= 0 or path <= 0:
        return None

    arf19 = float(((left[sign_pair] * right[sign_pair]) < 0).mean())
    lac19 = float(np.dot(left, right) / np.sqrt(left_energy * right_energy))
    frms19 = float(np.sqrt(energy / INTRABAR_RETURNS) / (10000.0 * bg48))
    npe19 = float(abs(r.sum()) / path)

    if not np.isfinite([arf19, lac19, frms19, npe19]).all():
        return None
    if not (-1.0 - 1e-12 <= lac19 <= 1.0 + 1e-12):
        raise RuntimeError("LAC19 bound drift")
    if not (0.0 <= arf19 <= 1.0 and 0.0 <= npe19 <= 1.0 + 1e-12 and frms19 > 0):
        raise RuntimeError("intrabar coordinate bound drift")
    return {"arf19": arf19, "lac19": lac19, "frms19": frms19, "npe19": npe19}


def build_intrabar_paths(root: Path, frame: pd.DataFrame, years: tuple[int, ...]) -> pd.DataFrame:
    rows: list[dict] = []
    for symbol in SYMBOLS:
        ps = frame[frame.symbol.eq(symbol)]
        for year in years:
            sec = activity.load_3s(root, symbol, year)
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
                sample = activity.sample_session(np.array([]), np.array([]), np.array([])) if raw is None else activity.sample_session(
                    raw.second.to_numpy(float), raw.price.to_numpy(float), raw.row_index.to_numpy()
                )
                price = sample["price"]
                r15 = sample["return_bp"]
                age = sample["age"]
                session_start = pd.Timestamp(f"{day} {'13:00:00' if int(aft) else '09:30:00'}")

                for bar in bars.itertuples(index=False):
                    bar_start = pd.Timestamp(bar.bar_end) - pd.Timedelta(minutes=5)
                    decision = pd.Timestamp(bar.bar_end) - pd.Timedelta(seconds=15)
                    start_second = int((bar_start - session_start).total_seconds())
                    decision_second = int((decision - session_start).total_seconds())
                    if start_second < 0 or decision_second > 7200 or start_second % 15 or decision_second % 15:
                        raise RuntimeError(f"intrabar E15 grid drift: {symbol} {bar.bar_end}")
                    j0 = start_second // 15
                    j1 = decision_second // 15
                    if j1 - j0 != INTRABAR_RETURNS:
                        raise RuntimeError("unexpected intrabar return count")

                    px = price[j0 : j1 + 1]
                    rr = r15[j0 + 1 : j1 + 1]
                    rec = {
                        "row_id": int(bar.row_id),
                        "symbol": symbol,
                        "trading_day": str(day),
                        "bar_end": pd.Timestamp(bar.bar_end),
                        "intrabar_decision_time": decision,
                        "intrabar_complete": False,
                        "intrabar_endpoint_age_seconds": np.nan,
                        "arf19": np.nan,
                        "lac19": np.nan,
                        "frms19": np.nan,
                        "npe19": np.nan,
                    }
                    complete = (
                        len(px) == INTRABAR_RETURNS + 1
                        and len(rr) == INTRABAR_RETURNS
                        and np.isfinite(px).all()
                        and np.isfinite(rr).all()
                        and (px > 0).all()
                    )
                    if complete:
                        coords = temporal_coordinates(rr, float(bar.bg48))
                        if coords is not None:
                            rec["intrabar_complete"] = True
                            rec["intrabar_endpoint_age_seconds"] = float(age[j1])
                            if rec["intrabar_endpoint_age_seconds"] > 3:
                                raise RuntimeError("intrabar endpoint age drift")
                            rec.update(coords)
                    rows.append(rec)
            del sec, groups

    z = pd.DataFrame(rows)
    if z.duplicated("row_id").any():
        raise RuntimeError("duplicate intrabar row_id")
    return z


def attach_intrabar(frame: pd.DataFrame, intrabar: pd.DataFrame) -> pd.DataFrame:
    keys = ["row_id", "symbol", "trading_day", "bar_end"]
    q = frame.merge(intrabar, on=keys, how="left", validate="one_to_one")
    cols = ["arf19", "lac19", "frms19", "npe19"]
    q["intrabar_available"] = q.intrabar_complete.fillna(False) & np.isfinite(q[cols]).all(axis=1)
    return q


def build_table(root: Path, years_5m: tuple[int, ...], years_3s: tuple[int, ...]) -> tuple[pd.DataFrame, dict]:
    frame, identities = parent.build_table(root, years_5m, years_3s)
    intrabar = build_intrabar_paths(root, frame, years_3s)
    frame = attach_intrabar(frame, intrabar)
    identities = dict(identities)
    identities["intrabar_parent_runner_git_blob"] = PARENT_BLOB
    return frame, identities


def design(q: pd.DataFrame, model: str) -> tuple[np.ndarray, list[str]]:
    if model not in MODELS:
        raise ValueError(model)
    x0, names0 = parent.design(q, "C")
    if model == "C":
        return x0, names0

    if model == "T":
        x = q.arf19.to_numpy(float)
        y = q.lac19.to_numpy(float)
        prefix = "temporal"
    else:
        x = q.frms19.to_numpy(float)
        y = q.npe19.to_numpy(float)
        prefix = "order_invariant"

    terms = {
        f"{prefix}_x": x,
        f"{prefix}_y": y,
        f"{prefix}_x2": x * x,
        f"{prefix}_y2": y * y,
        f"{prefix}_cross": x * y,
    }
    extra: list[np.ndarray] = []
    names: list[str] = []
    for name, values in terms.items():
        extra.append(values)
        names.append(name)
        for state in STATES:
            mask = q.previous_state.eq(state).to_numpy(float)
            extra.append(values * mask)
            names.append(f"{name}:{state}")
    xx = np.column_stack([x0] + extra).astype(float)
    if not np.isfinite(xx).all():
        raise ValueError("nonfinite intrabar temporal design")
    return xx, names0 + names


def fit_probe(x: np.ndarray, y: np.ndarray, names: list[str]) -> dict:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-14] = 1.0
    z = (x - mean) / scale
    intercept = float(np.mean(y))
    beta = np.linalg.solve(z.T @ z / len(z) + LAMBDA * np.eye(z.shape[1]), z.T @ (y - intercept) / len(z))
    return {
        "names": names,
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "beta": beta.tolist(),
        "intercept": intercept,
        "n": int(len(y)),
    }


def predict(q: pd.DataFrame, model: str, probe: dict, endpoint: str) -> np.ndarray:
    x, names = design(q, model)
    if names != probe["names"]:
        raise RuntimeError("feature schema drift")
    value = ((x - np.asarray(probe["mean"])) / np.asarray(probe["scale"])) @ np.asarray(probe["beta"]) + float(probe["intercept"])
    return np.clip(value, 0, 1) if endpoint == "future_tail" else value


def cohort(frame: pd.DataFrame, years: tuple[int, ...], h: int) -> tuple[pd.DataFrame, dict]:
    in_year = frame.year.isin(years)
    base_future = in_year & frame.base_available & frame[f"label_ok_{h}"].fillna(False)
    final = base_future & frame.intrabar_available.fillna(False)
    z = frame.loc[final].copy().reset_index(drop=True)
    z["sigma"] = z[f"sigma_{h}"]
    z["log_future_sigma"] = z[f"log_future_sigma_{h}"]
    z["future_tail"] = z[f"future_tail_{h}"]
    counts = {
        "target_rows": int(in_year.sum()),
        "own_base_available": int((in_year & frame.base_available).sum()),
        "own_base_and_future_feasible": int(base_future.sum()),
        "intrabar_available": int(final.sum()),
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


def compare(
    q: pd.DataFrame,
    endpoint: str,
    base_model: str,
    probes: dict,
    forward_gain: float,
    dev_n: int,
    coverage: float,
    h: int,
    out: Path,
) -> dict:
    y = q[endpoint].to_numpy(float)
    pt = predict(q, "T", probes[f"{h}|{endpoint}|T"], endpoint)
    pb = predict(q, base_model, probes[f"{h}|{endpoint}|{base_model}"], endpoint)
    l0 = (y - pb) ** 2
    l1 = (y - pt) ** 2
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
        blocks.to_csv(out / f"blocks_{h}_{endpoint}_T_vs_{base_model}_{days}d.csv", index=False, float_format="%.17g")
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
        "horizon": h,
        "endpoint": endpoint,
        "comparison": f"T_vs_{base_model}",
        "n": int(len(q)),
        "development_n": int(dev_n),
        "positive_events": int(y.sum()) if endpoint == "future_tail" else None,
        "baseline_loss": float(l0.mean()),
        "temporal_loss": float(l1.mean()),
        "absolute_gain": absolute,
        "relative_gain": relative,
        "ci_5day": ci["5"],
        "ci_20day_sensitivity": ci["20"],
        "slices": slices,
        "development_forward_gain": float(forward_gain),
        "gates": gates,
        "supported": bool(all(gates.values())),
    }


def invariant_checks() -> dict:
    rr = np.array([3, -1, 2, -4, 1, 5, -2, 2, -3, 4, 1, -1, 3, -2, 5, -4, 2, 1, -3], dtype=float)
    perm = np.sort(rr)
    a = temporal_coordinates(rr, 0.001)
    b = temporal_coordinates(-rr, 0.001)
    c = temporal_coordinates(perm, 0.001)
    assert a is not None and b is not None and c is not None
    for key in ("arf19", "lac19", "frms19", "npe19"):
        if not np.isclose(a[key], b[key], rtol=0, atol=1e-15):
            raise RuntimeError(f"global-sign invariance failed for {key}")
    for key in ("frms19", "npe19"):
        if not np.isclose(a[key], c[key], rtol=0, atol=1e-15):
            raise RuntimeError(f"order-invariant control drift for {key}")
    if np.isclose(a["arf19"], c["arf19"], rtol=0, atol=1e-12) and np.isclose(a["lac19"], c["lac19"], rtol=0, atol=1e-12):
        raise RuntimeError("synthetic ordering perturbation failed to change temporal block")
    return {
        "global_sign_invariant": True,
        "control_permutation_invariant": True,
        "temporal_block_order_sensitive": True,
        "current_bar_returns": INTRABAR_RETURNS,
    }


def feature_identity_checks(frame: pd.DataFrame) -> dict:
    z = frame[frame.base_available & frame.intrabar_available].head(200).copy()
    if z.empty:
        raise RuntimeError("no intrabar temporal feature rows")
    c, cn = design(z, "C")
    t, tn = design(z, "T")
    o, on = design(z, "O")
    if t.shape != o.shape or t.shape[1] - c.shape[1] != 20:
        raise RuntimeError("T/O complexity-match invariant failed")
    if tn[: len(cn)] != cn or on[: len(cn)] != cn:
        raise RuntimeError("inherited C schema drift")
    if c.shape[1] != 84 or t.shape[1] != 104 or o.shape[1] != 104:
        raise RuntimeError(f"unexpected inherited feature counts: C={c.shape[1]} T={t.shape[1]} O={o.shape[1]}")
    if not z.arf19.between(0, 1).all() or not z.lac19.between(-1 - 1e-12, 1 + 1e-12).all():
        raise RuntimeError("temporal coordinate bounds failed")
    if not z.npe19.between(0, 1 + 1e-12).all() or not z.frms19.gt(0).all():
        raise RuntimeError("order-invariant coordinate bounds failed")
    expected_decision = z.bar_end - pd.Timedelta(seconds=15)
    if not z.intrabar_decision_time.eq(expected_decision).all():
        raise RuntimeError("E15 decision-time drift")
    return {
        "base_columns": int(c.shape[1]),
        "temporal_columns": int(t.shape[1]),
        "order_invariant_columns": int(o.shape[1]),
        "temporal_block_columns": 20,
        "order_invariant_block_columns": 20,
        "T_O_complexity_matched": True,
        "same_row_availability": True,
        "E15_current_bar_only": True,
        **invariant_checks(),
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
            pt = predict(hold, "T", fwd["T"], endpoint)
            for b in ("C", "O"):
                pb = predict(hold, b, fwd[b], endpoint)
                l0, l1 = (y - pb) ** 2, (y - pt) ** 2
                gain = l0 - l1
                forward[f"{h}|{endpoint}|{b}"] = {
                    "n": int(len(hold)),
                    "absolute_gain": float(gain.mean()),
                    "relative_gain": float(gain.mean() / l0.mean()),
                }

    payload = {
        "schema": "intrabar_temporal_reversal_utility_v1_frozen_models",
        "source_main": SOURCE_MAIN,
        "protocol_git_blob": PROTOCOL_BLOB,
        "parent_runner_git_blob": PARENT_BLOB,
        "ridge_lambda": LAMBDA,
        "intrabar_return_count": INTRABAR_RETURNS,
        "temporal_block_columns": 20,
        "order_invariant_control_columns": 20,
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
    }
    model_path = out / "FROZEN_MODELS.json"
    dump_json(model_path, payload)
    model_sha = sha256_file(model_path)
    (out / "MODEL_SHA256.txt").write_text(model_sha + "\n", encoding="utf-8")
    dump_json(
        out / "FIT_RECEIPT.json",
        {
            "model_sha256": model_sha,
            "feature_identity": feature_check,
            "development_forward": forward,
            "development_coverage": coverage,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "git_sha": os.getenv("GITHUB_SHA"),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "validation_scored": False,
            "read_2026": False,
            "synthetic_2026_used": False,
            "blackbox_queried": False,
            "pnl_computed": False,
            "production_authority": False,
        },
    )
    print(json.dumps({"fit_complete": True, "model_sha256": model_sha, "forward": forward}, indent=2), flush=True)


def descriptive_outputs(q: pd.DataFrame, probes: dict, h: int, out: Path) -> dict:
    corr_cols = ["shock_intensity", "vol_ratio", "arf19", "lac19", "frms19", "npe19"]
    corr = q[corr_cols].corr().to_dict()
    summary = {
        c: {
            "mean": float(q[c].mean()),
            "median": float(q[c].median()),
            "p05": float(q[c].quantile(0.05)),
            "p95": float(q[c].quantile(0.95)),
        }
        for c in corr_cols
    }

    slice_rows = []
    for endpoint in ENDPOINTS:
        pc = predict(q, "C", probes[f"{h}|{endpoint}|C"], endpoint)
        pt = predict(q, "T", probes[f"{h}|{endpoint}|T"], endpoint)
        po = predict(q, "O", probes[f"{h}|{endpoint}|O"], endpoint)
        y = q[endpoint].to_numpy(float)
        for b, pb in (("C", pc), ("O", po)):
            gain = (y - pb) ** 2 - (y - pt) ** 2
            for col in ("symbol", "year", "previous_state", "slot"):
                for key, inds in q.groupby(col, sort=True).indices.items():
                    slice_rows.append(
                        {
                            "horizon": h,
                            "endpoint": endpoint,
                            "comparison": f"T_vs_{b}",
                            "slice_type": col,
                            "slice": str(key),
                            "n": int(len(inds)),
                            "absolute_gain": float(gain[inds].mean()),
                        }
                    )
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
            for b in ("C", "O"):
                forward_gain = frozen["development_forward"][f"{h}|{endpoint}|{b}"]["absolute_gain"]
                comparisons.append(
                    compare(
                        q,
                        endpoint,
                        b,
                        frozen["models"],
                        forward_gain,
                        frozen["models"][f"{h}|{endpoint}|T"]["n"],
                        cov["coverage"],
                        h,
                        out,
                    )
                )
            subset = [x for x in comparisons if x["horizon"] == h and x["endpoint"] == endpoint]
            joint[f"{h}|{endpoint}"] = bool(len(subset) == 2 and all(x["supported"] for x in subset))

    decision = (
        "INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS"
        if any(joint.values())
        else "INTRABAR_TEMPORAL_REVERSAL_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    )
    pd.DataFrame(
        [{k: v for k, v in x.items() if k not in ("gates", "slices", "ci_5day", "ci_20day_sensitivity")} for x in comparisons]
    ).to_csv(out / "comparisons.csv", index=False)
    dump_json(
        out / "VALIDATION_RESULTS.json",
        {
            "schema": "intrabar_temporal_reversal_utility_v1_validation",
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
        },
    )
    print(
        json.dumps(
            {
                "decision": decision,
                "joint": joint,
                "comparisons": [
                    {
                        "comparison": x["comparison"],
                        "horizon": x["horizon"],
                        "endpoint": x["endpoint"],
                        "relative_gain": x["relative_gain"],
                        "absolute_gain": x["absolute_gain"],
                        "supported": x["supported"],
                        "gates": x["gates"],
                    }
                    for x in comparisons
                ],
            },
            indent=2,
        ),
        flush=True,
    )


def physical_guard(root: Path, phase: str) -> None:
    if (root / "data/cross_index_risk_gate_2026_v1").exists():
        raise RuntimeError("2026 protected data present")
    data_root = root / "data"
    synthetic_hits = list(data_root.glob("**/*2026*synthetic*")) + list(data_root.glob("**/*synthetic*2026*")) if data_root.exists() else []
    if synthetic_hits:
        raise RuntimeError(f"synthetic 2026 data present: {synthetic_hits[:4]}")
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
