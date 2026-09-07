"""Fit once, calibrate once, then forward-validate frozen volatility tools."""

# ruff: noqa: E402
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from star50_filter.causal_volatility import FLOOR, VolatilityModel, event_metrics, fit_model, future_variance, past_features

OUT = ROOT / "artifacts/causal_volatility_tool_v1"
INPUT = ROOT / "artifacts/tail_distribution_v1/panel_1m.parquet"
SYMBOLS = ["000852.SH", "000688.SH"]


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n")


def freeze():
    assert not OUT.exists()
    parent = json.loads((INPUT.parent / "prepared.json").read_text())
    expected = next(r["panel_sha256"] for r in parent["views"] if r["minutes"] == 1)
    assert sha(INPUT) == expected
    sources = [
        "src/star50_filter/causal_volatility.py",
        "scripts/research_causal_volatility_v1.py",
        "tests/test_causal_volatility.py",
        "docs/research/causal_volatility_tool_v1/protocol.md",
        "docs/research/causal_volatility_tool_v1/data_usage.json",
    ]
    save(OUT / "freeze.json", {"input_sha256": expected, "sources": {n: sha(ROOT / n) for n in sources}, "production_authority": False})


def check():
    f = json.loads((OUT / "freeze.json").read_text())
    for p, h in f["sources"].items():
        assert sha(ROOT / p) == h, p
    assert sha(INPUT) == f["input_sha256"]
    return f


def load(symbol, year):
    return pd.read_parquet(INPUT, filters=[("symbol", "==", symbol), ("year", "<=", year)]).sort_values("timestamp").reset_index(drop=True)


def fit():
    check()
    assert not (OUT / "fit_receipt.json").exists()
    rows = []
    for symbol in SYMBOLS:
        f = past_features(load(symbol, 2023))
        assert f.year.max() == 2023
        for h in [5, 15, 30]:
            model, y = fit_model(f, h)
            path = OUT / "models" / f"{symbol}_{h}"
            model.save(path)
            valid = f.features_ready & y.notna()
            rows.append(
                {
                    "symbol": symbol,
                    "horizon": h,
                    "fit_rows": int((valid & f.year.isin([2021, 2022])).sum()),
                    "cal_rows": int((valid & (f.year == 2023)).sum()),
                    "low_high_edges_sigma_bp": (model.state_edges * 10000).tolist(),
                    "fit_last_year": 2022,
                    "cal_last_year": 2023,
                    "metadata_sha256": sha(path / "model.json"),
                    "parameters_sha256": sha(path / "parameters.npz"),
                }
            )
    save(OUT / "fit_receipt.json", {"freeze_sha256": sha(OUT / "freeze.json"), "models": rows, "test_years_read": []})
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def regression_metrics(actual, pred, edges):
    y = np.asarray(actual, float)
    p = np.asarray(pred, float)
    e = np.log(np.maximum(p, np.sqrt(FLOOR))) - np.log(np.maximum(y, np.sqrt(FLOOR)))
    truth = np.searchsorted(edges, y, side="right")
    guess = np.searchsorted(edges, p, side="right")
    cm = np.zeros((3, 3), dtype=int)
    np.add.at(cm, (truth, guess), 1)
    recalls = np.divide(np.diag(cm), cm.sum(axis=1), out=np.zeros(3), where=cm.sum(axis=1) > 0)
    high = event_metrics(truth == 2, guess == 2)
    return {
        "rows": len(y),
        "log_sigma_rmse": float(np.sqrt(np.mean(e**2))),
        "median_absolute_factor_error": float(np.exp(np.median(abs(e)))),
        "spearman": float(spearmanr(y, p).statistic),
        "bucket_accuracy": float((truth == guess).mean()),
        "balanced_accuracy": float(recalls.mean()),
        "actual_high_share": float((truth == 2).mean()),
        "high_precision": high["precision"],
        "high_recall": high["recall"],
        "predicted_high_time_share": high["alert_time_share"],
    }, cm


def evaluate(year):
    check()
    assert year in [2024, 2025]
    if year == 2025:
        assert (OUT / "2024/review.json").exists()
    dest = OUT / str(year)
    assert not dest.exists()
    dest.mkdir()
    fit_record = json.loads((OUT / "fit_receipt.json").read_text())
    metrics = []
    events = []
    coverage = []
    for symbol in SYMBOLS:
        history = load(symbol, year)
        all_features = past_features(history)
        for h in [5, 15, 30]:
            entry = next(r for r in fit_record["models"] if r["symbol"] == symbol and r["horizon"] == h)
            path = OUT / "models" / f"{symbol}_{h}"
            assert sha(path / "parameters.npz") == entry["parameters_sha256"] and sha(path / "model.json") == entry["metadata_sha256"]
            model = VolatilityModel.load(path)
            prediction = model.predict_features(all_features)
            future = future_variance(all_features, h)
            keep = (all_features.year == year) & prediction.forecast_available & future.notna()
            f = all_features.loc[keep].reset_index(drop=True)
            p = prediction.loc[keep].reset_index(drop=True)
            y = np.sqrt(future.loc[keep].to_numpy())
            past = np.sqrt(f[f"past_var_{h}"].clip(lower=FLOOR).to_numpy())
            p["actual_sigma"] = y
            p["past_sigma"] = past
            p["actual_ratio"] = y / past
            p["clock_sigma"] = np.sqrt(f.clock.map(model.clock_variance).to_numpy())
            assert np.isfinite(p.clock_sigma).all()
            p["day"] = f.day
            p["session"] = f.session
            p["session_slot"] = f.session_slot
            p["nonoverlap"] = (f.session_slot - 1) % h == 0
            p["recent_shock5"] = f.recent_shock5
            p["actual_bucket"] = np.searchsorted(model.state_edges, y, side="right")
            p["high_edge"] = model.state_edges[1]
            p["quiet_context"] = (past < model.state_edges[1]) & ~f.recent_shock5.to_numpy()
            for k in [2, 3, 4]:
                p[f"actual_amplify_{k}"] = (y >= k * past) & (y >= model.state_edges[1])
            p.to_parquet(dest / f"{symbol}_{h}_predictions.parquet", index=False)
            for sampling, select in [("dense", np.ones(len(p), bool)), ("nonoverlap", p.nonoverlap.to_numpy())]:
                q = p.loc[select]
                a = q.actual_sigma.to_numpy()
                base = {"symbol": symbol, "horizon": h, "year": year, "sampling": sampling}
                coverage.append(
                    {
                        **base,
                        "rows": len(q),
                        "interval_80_coverage": float(((a >= q.sigma_p10) & (a <= q.sigma_p90)).mean()),
                        "median_interval_width_ratio": float((q.sigma_p90 / q.sigma_p10).median()),
                    }
                )
                for name, column in [("multiscale", "forecast_sigma"), ("persistence", "past_sigma"), ("clock_only", "clock_sigma")]:
                    m, cm = regression_metrics(a, q[column], model.state_edges)
                    metrics.append({**base, "model": name, **m})
                    save(
                        dest / f"{symbol}_{h}_{sampling}_{name}_confusion.json",
                        {"rows_actual_columns_predicted": cm.tolist(), "states": ["low", "medium", "high"]},
                    )
                    for k in [2, 3, 4]:
                        predicted = (q[column] >= k * q.past_sigma) & (q[column] >= q.high_edge)
                        for context, mask in [("all", np.ones(len(q), bool)), ("quiet_no_recent_shock", q.quiet_context.to_numpy())]:
                            events.append(
                                {
                                    **base,
                                    "model": name,
                                    "rule": "point",
                                    "factor": k,
                                    "context": context,
                                    **event_metrics(q.loc[mask, f"actual_amplify_{k}"], predicted.loc[mask]),
                                }
                            )
                events.append(
                    {
                        **base,
                        "model": "multiscale",
                        "rule": "probability_0.5",
                        "factor": "high_level",
                        "context": "all",
                        **event_metrics(q.actual_bucket == 2, q.p_future_high >= 0.5),
                    }
                )
                for k in [2, 3, 4]:
                    for context, mask in [("all", np.ones(len(q), bool)), ("quiet_no_recent_shock", q.quiet_context.to_numpy())]:
                        events.append(
                            {
                                **base,
                                "model": "multiscale",
                                "rule": "probability_0.5",
                                "factor": k,
                                "context": context,
                                **event_metrics(q.loc[mask, f"actual_amplify_{k}"], q.loc[mask, f"p_amplify_{k}"] >= 0.5),
                            }
                        )
            # An actual prefix must reproduce earlier predictions with no future values available.
            stop = int(np.flatnonzero(keep)[len(p) // 2]) + 1
            prefix = model.predict_features(past_features(history.iloc[:stop]))
            pd.testing.assert_frame_equal(prediction.iloc[:stop], prefix, check_exact=False, rtol=1e-12, atol=1e-14)
    for name, rows in [("metrics", metrics), ("events", events), ("intervals", coverage)]:
        pd.DataFrame(rows).to_csv(dest / f"{name}.csv", index=False)
    save(
        dest / "receipt.json",
        {
            "year": year,
            "fit_receipt_sha256": sha(OUT / "fit_receipt.json"),
            "prior_review_sha256": None if year == 2024 else sha(OUT / "2024/review.json"),
            "files": {p.name: sha(p) for p in sorted(dest.iterdir()) if p.is_file()},
            "prefix_prediction_within_1e_12_relative_1e_14_absolute": True,
            "max_read_year": year,
            "production_authority": False,
        },
    )
    print(pd.DataFrame(metrics).query('sampling=="nonoverlap" and horizon==15').to_string(index=False))
    print(
        pd.DataFrame(events)
        .query('sampling=="nonoverlap" and horizon==15 and model=="multiscale" and rule=="probability_0.5"')
        .to_string(index=False)
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["freeze", "fit", "evaluate"])
    p.add_argument("--year", type=int)
    a = p.parse_args()
    if a.mode == "freeze":
        freeze()
    elif a.mode == "fit":
        fit()
    else:
        evaluate(a.year)
