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
PROTOCOL_BLOB = "8e5690d4fa1250fcc2e3b5cc3bfdea733dd46880"
SOURCE_MAIN = "291d04861e85492337a2f86f1fade0419254972d"

MODELS = ("C", "A", "M")
ENDPOINTS = ("log_future_sigma", "future_tail")
HORIZONS = (15, 30, 60)
SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
LAMBDA = 0.01
SEED = 20260918
BOOTSTRAPS = 5000
FAMILY = 12
WINDOW = 12


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
    spec = importlib.util.spec_from_file_location("signed_risk_parent", PARENT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


parent = load_parent()


def attach_asymmetry_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach frozen 12-valid-completed-bar sign and magnitude-shape coordinates.

    The current row's final 5m return is explicitly excluded by shift(1).
    Only valid finite returns contribute to the valid-bar history window.
    """
    q = frame.copy()
    cols = ("sei12", "sai12", "l1l2_12", "maxl2_12")
    for c in cols:
        q[c] = np.nan

    for _, g in q.groupby("symbol", sort=False):
        v = g.r.dropna().astype(float)
        if v.empty:
            continue
        prior = v.shift(1)
        abs_prior = prior.abs()
        sq_prior = prior * prior
        sum_sq = sq_prior.rolling(WINDOW, min_periods=WINDOW).sum()
        sum_abs = abs_prior.rolling(WINDOW, min_periods=WINDOW).sum()
        sum_signed = prior.rolling(WINDOW, min_periods=WINDOW).sum()
        signed_energy = (prior * abs_prior).rolling(WINDOW, min_periods=WINDOW).sum()
        max_abs = abs_prior.rolling(WINDOW, min_periods=WINDOW).max()
        root_energy = np.sqrt(sum_sq)

        with np.errstate(divide="ignore", invalid="ignore"):
            sei = signed_energy / sum_sq
            sai = sum_signed / sum_abs
            l1l2 = sum_abs / (np.sqrt(float(WINDOW)) * root_energy)
            maxl2 = max_abs / root_energy

        q.loc[v.index, "sei12"] = sei.to_numpy(float)
        q.loc[v.index, "sai12"] = sai.to_numpy(float)
        q.loc[v.index, "l1l2_12"] = l1l2.to_numpy(float)
        q.loc[v.index, "maxl2_12"] = maxl2.to_numpy(float)

    finite = np.isfinite(q[list(cols)]).all(axis=1)
    positive_shape = (q.l1l2_12 > 0) & (q.maxl2_12 > 0)
    bounded_signed = q.sei12.abs().le(1 + 1e-12) & q.sai12.abs().le(1 + 1e-12)
    q["asymmetry_available"] = finite & positive_shape & bounded_signed
    return q


def build_table(root: Path, years_5m: tuple[int, ...], years_3s: tuple[int, ...]) -> tuple[pd.DataFrame, dict]:
    frame, identities = parent.build_table(root, years_5m, years_3s)
    frame = attach_asymmetry_history(frame)
    identities = dict(identities)
    identities["signed_parent_runner_git_blob"] = PARENT_BLOB
    return frame, identities


def design(q: pd.DataFrame, model: str) -> tuple[np.ndarray, list[str]]:
    if model not in MODELS:
        raise ValueError(model)
    x0, names0 = parent.design(q, "C")
    if model == "C":
        return x0, names0

    if model == "A":
        x = q.sei12.to_numpy(float)
        y = q.sai12.to_numpy(float)
        prefix = "signed"
    else:
        x = q.l1l2_12.to_numpy(float)
        y = q.maxl2_12.to_numpy(float)
        prefix = "magnitude"

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
        raise ValueError("nonfinite signed-risk asymmetry design")
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
    final = base_future & frame.asymmetry_available.fillna(False)
    z = frame.loc[final].copy().reset_index(drop=True)
    z["sigma"] = z[f"sigma_{h}"]
    z["log_future_sigma"] = z[f"log_future_sigma_{h}"]
    z["future_tail"] = z[f"future_tail_{h}"]
    counts = {
        "target_rows": int(in_year.sum()),
        "own_base_available": int((in_year & frame.base_available).sum()),
        "own_base_and_future_feasible": int(base_future.sum()),
        "asymmetry_available": int((base_future & frame.asymmetry_available.fillna(False)).sum()),
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
    pa = predict(q, "A", probes[f"{h}|{endpoint}|A"], endpoint)
    pb = predict(q, base_model, probes[f"{h}|{endpoint}|{base_model}"], endpoint)
    l0 = (y - pb) ** 2
    l1 = (y - pa) ** 2
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
        blocks.to_csv(out / f"blocks_{h}_{endpoint}_A_vs_{base_model}_{days}d.csv", index=False, float_format="%.17g")
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
        "comparison": f"A_vs_{base_model}",
        "n": int(len(q)),
        "development_n": int(dev_n),
        "positive_events": int(y.sum()) if endpoint == "future_tail" else None,
        "baseline_loss": float(l0.mean()),
        "asymmetry_loss": float(l1.mean()),
        "absolute_gain": absolute,
        "relative_gain": relative,
        "ci_5day": ci["5"],
        "ci_20day_sensitivity": ci["20"],
        "slices": slices,
        "development_forward_gain": float(forward_gain),
        "gates": gates,
        "supported": bool(all(gates.values())),
    }


def feature_identity_checks(frame: pd.DataFrame) -> dict:
    z = frame[frame.base_available & frame.asymmetry_available].head(200).copy()
    if z.empty:
        raise RuntimeError("no signed-risk asymmetry feature rows")
    c, cn = design(z, "C")
    a, an = design(z, "A")
    m, mn = design(z, "M")
    if a.shape != m.shape or a.shape[1] - c.shape[1] != 20:
        raise RuntimeError("A/M complexity-match invariant failed")
    if an[:len(cn)] != cn or mn[:len(cn)] != cn:
        raise RuntimeError("inherited C schema drift")
    if len(an) != len(cn) + 20 or len(mn) != len(cn) + 20:
        raise RuntimeError("asymmetry block schema invariant failed")
    if c.shape[1] != 84 or a.shape[1] != 104 or m.shape[1] != 104:
        raise RuntimeError(f"unexpected inherited feature counts: C={c.shape[1]} A={a.shape[1]} M={m.shape[1]}")
    if not (z.sei12.abs().le(1 + 1e-12).all() and z.sai12.abs().le(1 + 1e-12).all()):
        raise RuntimeError("signed coordinate bound failed")
    return {
        "base_columns": int(c.shape[1]),
        "signed_columns": int(a.shape[1]),
        "magnitude_control_columns": int(m.shape[1]),
        "signed_block_columns": 20,
        "magnitude_block_columns": 20,
        "A_M_complexity_matched": True,
        "current_final_return_excluded_by_shift1": True,
        "signed_coordinates_bounded": True,
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
            pa = predict(hold, "A", fwd["A"], endpoint)
            for b in ("C", "M"):
                pb = predict(hold, b, fwd[b], endpoint)
                l0, l1 = (y - pb) ** 2, (y - pa) ** 2
                gain = l0 - l1
                forward[f"{h}|{endpoint}|{b}"] = {
                    "n": int(len(hold)),
                    "absolute_gain": float(gain.mean()),
                    "relative_gain": float(gain.mean() / l0.mean()),
                }

    payload = {
        "schema": "signed_risk_asymmetry_utility_v1_frozen_models",
        "source_main": SOURCE_MAIN,
        "protocol_git_blob": PROTOCOL_BLOB,
        "parent_runner_git_blob": PARENT_BLOB,
        "ridge_lambda": LAMBDA,
        "lookback_valid_completed_bars": WINDOW,
        "signed_block_columns": 20,
        "magnitude_control_columns": 20,
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
        "blackbox_queried": False,
        "pnl_computed": False,
        "production_authority": False,
    })
    print(json.dumps({"fit_complete": True, "model_sha256": model_sha, "forward": forward}, indent=2), flush=True)


def descriptive_outputs(q: pd.DataFrame, probes: dict, h: int, out: Path) -> dict:
    corr_cols = ["shock_intensity", "vol_ratio", "sei12", "sai12", "l1l2_12", "maxl2_12"]
    corr = q[corr_cols].corr().to_dict()
    summary = {}
    for c in corr_cols:
        summary[c] = {
            "mean": float(q[c].mean()),
            "median": float(q[c].median()),
            "p05": float(q[c].quantile(0.05)),
            "p95": float(q[c].quantile(0.95)),
        }

    slice_rows = []
    decile_rows = []
    for endpoint in ENDPOINTS:
        pc = predict(q, "C", probes[f"{h}|{endpoint}|C"], endpoint)
        pa = predict(q, "A", probes[f"{h}|{endpoint}|A"], endpoint)
        pm = predict(q, "M", probes[f"{h}|{endpoint}|M"], endpoint)
        y = q[endpoint].to_numpy(float)
        for b, pb in (("C", pc), ("M", pm)):
            gain = (y - pb) ** 2 - (y - pa) ** 2
            for col in ("symbol", "year", "previous_state", "slot"):
                for key, inds in q.groupby(col, sort=True).indices.items():
                    slice_rows.append({
                        "horizon": h,
                        "endpoint": endpoint,
                        "comparison": f"A_vs_{b}",
                        "slice_type": col,
                        "slice": str(key),
                        "n": int(len(inds)),
                        "absolute_gain": float(gain[inds].mean()),
                    })
        increment = pa - pc
        dec = pd.qcut(pd.Series(increment), 10, labels=False, duplicates="drop")
        tmp = pd.DataFrame({"decile": dec, "sigma": q.sigma.to_numpy(float), "tail": q.future_tail.to_numpy(float), "increment": increment})
        for d, g in tmp.groupby("decile", dropna=False, sort=True):
            decile_rows.append({
                "horizon": h,
                "endpoint": endpoint,
                "increment_decile": None if pd.isna(d) else int(d),
                "n": int(len(g)),
                "increment_mean": float(g["increment"].mean()),
                "sigma_mean": float(g["sigma"].mean()),
                "tail_rate": float(g["tail"].mean()),
            })

    pd.DataFrame(slice_rows).to_csv(out / f"slice_gains_{h}.csv", index=False)
    pd.DataFrame(decile_rows).to_csv(out / f"increment_deciles_{h}.csv", index=False)
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
            for b in ("C", "M"):
                forward_gain = frozen["development_forward"][f"{h}|{endpoint}|{b}"]["absolute_gain"]
                comparisons.append(compare(
                    q, endpoint, b, frozen["models"], forward_gain,
                    frozen["models"][f"{h}|{endpoint}|A"]["n"], cov["coverage"], h, out,
                ))
            subset = [x for x in comparisons if x["horizon"] == h and x["endpoint"] == endpoint]
            joint[f"{h}|{endpoint}"] = bool(len(subset) == 2 and all(x["supported"] for x in subset))

    decision = (
        "SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS"
        if any(joint.values()) else "SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    )
    pd.DataFrame([
        {k: v for k, v in x.items() if k not in ("gates", "slices", "ci_5day", "ci_20day_sensitivity")}
        for x in comparisons
    ]).to_csv(out / "comparisons.csv", index=False)
    dump_json(out / "VALIDATION_RESULTS.json", {
        "schema": "signed_risk_asymmetry_utility_v1_validation",
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
            "comparison": x["comparison"],
            "horizon": x["horizon"],
            "endpoint": x["endpoint"],
            "relative_gain": x["relative_gain"],
            "absolute_gain": x["absolute_gain"],
            "supported": x["supported"],
            "gates": x["gates"],
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
