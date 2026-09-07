#!/usr/bin/env python3
"""Execute the frozen low-vol first-shock conditional-structure study.

Uses only authorized 000688.SH/000852.SH minute + 3s data through 2025.  Event
labels and decision eligibility are imported from the sealed V1 engine; strict
15-second support is imported from seconds_v2.  No model fitting, P&L, or 2026.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "docs/research/first_shock_gate_v1/code"))
sys.path.insert(0, str(REPO / "docs/research/first_shock_seconds_v2/code"))

import structure as st
import first_shock_gate as g
import seconds_v2 as s2

SYMBOLS = ("000688.SH", "000852.SH")
RANGES = (20.0, 30.0, 40.0)


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def load_minute_panel(root: Path, symbol: str) -> pd.DataFrame:
    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data
    native = load_market_data(symbol, "1m", "2021-01-01", "2025-12-31", root=root)
    panel = g.minute_panel(native, symbol)
    if (panel.year > 2025).any():
        raise st.StudyError("2026 row reached minute panel")
    return panel


def build_strict_fine(root: Path, symbol: str, panel: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    rows = []
    audits = []
    for year in range(2021, 2026):
        seconds, audit = s2.read_seconds(root, symbol, year)
        groups = {key: z for key, z in seconds.groupby("session", sort=False)}
        year_panel = panel[panel.year == year]
        valid_sessions = 0
        for session, part in year_panel.groupby("session", sort=False):
            raw = groups.get(session)
            if raw is None:
                t = np.array([]); p = np.array([]); r = np.array([], dtype=int)
            else:
                t = raw.second.to_numpy(float)
                p = raw.price.to_numpy(float)
                r = raw.row_index.to_numpy()
            sample = s2.sample_session(t, p, r, step=15, gap_limit=3)
            fm = st.fine_measurements(sample, part.return_bp.to_numpy(float))
            fm["session"] = session
            fm["day"] = str(part.day.iloc[0])
            fm["year"] = int(year)
            fm["afternoon"] = int(part.afternoon.iloc[0])
            fm["symbol"] = symbol
            valid_sessions += int(fm.fine_complete5.any())
            rows.append(fm)
        audit = dict(audit)
        audit["strict_gap_limit_seconds"] = 3
        audit["sessions_with_any_complete_5m"] = int(valid_sessions)
        audits.append(audit)
    fine = pd.concat(rows, ignore_index=True)
    return fine, audits


def prepare_symbol(root: Path, symbol: str) -> tuple[pd.DataFrame, list[dict]]:
    panel = load_minute_panel(root, symbol)
    q = s2.aligned_targets(g.make_features(panel))
    q["symbol"] = symbol
    fine, audits = build_strict_fine(root, symbol, panel)
    keys = ["symbol", "session", "day", "year", "afternoon", "minute"]
    if fine.duplicated(keys).any() or q.duplicated(["symbol", "session", "minute"]).any():
        raise st.StudyError("duplicate analysis key")
    q = q.merge(fine, on=keys, how="left", validate="one_to_one", suffixes=("", "_fine"))
    if len(q) != len(panel):
        raise st.StudyError("minute/fine merge changed row count")
    q["C1"] = np.sqrt(pd.to_numeric(q.rv5, errors="coerce"))
    q = st.attach_activity_surprise(q)
    # Fine admissibility is separate from V1's minute-only decision eligibility.
    q["decision_ok"] = q.decision_ok.astype(bool) & q.fine_complete5.astype(bool)
    st.assert_results_blind(q.columns)
    return q, audits


def thresholds_for_range(frame: pd.DataFrame, range_bp: float) -> pd.DataFrame:
    primary = st.freeze_thresholds(frame, range_bp=range_bp)
    control_rows = []
    for symbol, q in frame.groupby("symbol", sort=True):
        cal = q[(q.year == 2023) & q.decision_ok & q.fine_complete5 &
                (q.pre5m_range_bp < range_bp)]
        values = pd.to_numeric(cal.C1, errors="coerce")
        values = values[np.isfinite(values)]
        if len(values) < 100:
            raise st.StudyError(f"insufficient C1 calibration for {symbol}: {len(values)}")
        control_rows.append({"symbol": symbol, "measure": "C1", "year": 2023,
                             "quantile": .8, "threshold": float(np.quantile(values, .8)),
                             "calibration_n": int(len(values)), "range_bp": float(range_bp)})
    return pd.concat([primary, pd.DataFrame(control_rows)], ignore_index=True)


def clock_control(q: pd.DataFrame, range_bp: float) -> list[dict]:
    x = q[q.decision_ok & q.fine_complete5 & (q.pre5m_range_bp < range_bp) & np.isfinite(q.target)].copy()
    x["clock_bucket"] = pd.cut(x.minute, bins=[30,45,60,75,90,105], include_lowest=True)
    rows = []
    for (symbol, year, bucket), z in x[x.year.isin([2024,2025])].groupby(
            ["symbol", "year", "clock_bucket"], observed=True, sort=True):
        rows.append({"symbol": symbol, "year": int(year), "clock_bucket": str(bucket),
                     "n": int(len(z)), "first_shock_window_risk": float(z.target.mean())})
    return rows


def same_coverage_diagnostic(q: pd.DataFrame, measure: str, year: int, range_bp: float) -> dict:
    x = q[(q.year == year) & q.decision_ok & q.fine_complete5 &
          (q.pre5m_range_bp < range_bp) & np.isfinite(q[measure])].copy()
    x["analysis_ok"] = True
    if len(x) == 0:
        return {"n": 0}
    cutoff = float(np.quantile(x[measure], .8))
    x["alarm"] = x[measure] >= cutoff
    return {"n": int(len(x)), "diagnostic_eval_year_cutoff": cutoff,
            "nondeployable": True, **st.decision_metrics(x)}


def evaluate_all(frame: pd.DataFrame, thresholds: pd.DataFrame, range_bp: float,
                 bootstrap_repeats: int) -> tuple[list[dict], list[dict]]:
    rows = []
    event_rows = []
    for measure in (*st.MEASURES, "C1"):
        applied = st.apply_threshold(frame, thresholds, measure, range_bp=range_bp)
        for symbol in SYMBOLS:
            for year in st.EVALUATION_YEARS:
                q = applied[(applied.symbol == symbol) & (applied.year == year)].copy()
                dm = st.decision_metrics(q)
                em = st.event_metrics(q)
                boot = st.moving_block_bootstrap(q, repeats=bootstrap_repeats,
                                                  seed=st.SEED + year + sum(map(ord, symbol+measure)))
                rows.append({"symbol": symbol, "year": int(year), "measure": measure,
                             "range_bp": float(range_bp), **dm,
                             "bootstrap_status": boot["status"],
                             "ci_low": boot["ci"][0], "ci_high": boot["ci"][1],
                             "p_two_sided": boot["p_two_sided"],
                             "bootstrap_repeats": boot["repeats"]})
                event_rows.append({"symbol": symbol, "year": int(year), "measure": measure,
                                   "range_bp": float(range_bp), **em})
    return rows, event_rows


def add_holm(primary_rows: list[dict]) -> None:
    tests = [r for r in primary_rows if r["measure"] in st.MEASURES and r["range_bp"] == 30.0]
    if len(tests) != 16:
        raise st.StudyError(f"expected 16 primary comparisons, got {len(tests)}")
    adjusted = st.holm_adjust([r["p_two_sided"] for r in tests])
    for row, adj in zip(tests, adjusted):
        row["holm_p"] = adj


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=REPO)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--bootstrap-repeats", type=int, default=2000)
    args = p.parse_args()
    root = args.root.resolve(); out = args.out.resolve()
    if args.bootstrap_repeats < 100:
        raise st.StudyError("bootstrap repeats too small")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("refuse to overwrite output")
    out.mkdir(parents=True, exist_ok=True)

    # Reuse V2's pinned-input validation. In the sparse Actions workspace this
    # proves exactly the 20 permitted 2021-2025 parquet partitions are present.
    s2.validate_inputs(root, out)
    frames = []; support_audit = []
    for symbol in SYMBOLS:
        q, audit = prepare_symbol(root, symbol)
        frames.append(q); support_audit.extend(audit)
    frame = pd.concat(frames, ignore_index=True)
    if (frame.year > 2025).any():
        raise st.StudyError("future year detected")

    all_thresholds=[]; result_rows=[]; event_rows=[]
    for range_bp in RANGES:
        thresholds = thresholds_for_range(frame, range_bp)
        all_thresholds.append(thresholds)
        r,e = evaluate_all(frame, thresholds, range_bp, args.bootstrap_repeats)
        result_rows.extend(r); event_rows.extend(e)
    add_holm(result_rows)

    result = pd.DataFrame(result_rows)
    events = pd.DataFrame(event_rows)
    thresholds = pd.concat(all_thresholds, ignore_index=True)
    clock = pd.DataFrame(clock_control(frame, 30.0))
    diag=[]
    for measure in (*st.MEASURES, "C1"):
        for symbol in SYMBOLS:
            for year in st.EVALUATION_YEARS:
                q=frame[frame.symbol==symbol]
                diag.append({"symbol":symbol,"year":year,"measure":measure,
                             **same_coverage_diagnostic(q,measure,year,30.0)})

    result.to_csv(out/"primary_and_sensitivity_results.csv", index=False)
    events.to_json(out/"event_metrics.json", orient="records", indent=2)
    thresholds.to_csv(out/"frozen_thresholds.csv", index=False)
    clock.to_csv(out/"clock_control.csv", index=False)
    pd.DataFrame(diag).to_json(out/"same_coverage_diagnostic.json", orient="records", indent=2)
    write_json(out/"support_audit.json", support_audit)

    primary = result[(result.range_bp==30.0) & result.measure.isin(st.MEASURES)].copy()
    summary = {
        "protocol": "low_vol_first_shock_conditional_structure_v1",
        "protocol_commit": "5723ec921f99ba24a22508b6c933566e64e14814",
        "event_engine_blob": "18ec71c64ba441460a221dfcc59b97080a026d81",
        "seconds_v2_blob": "fb07081a4f42bcf9dda509fd3d16cb661fa45ce3",
        "strict_fine_gap_limit_seconds": 3,
        "calibration_year": 2023,
        "evaluation_years": [2024,2025],
        "primary_range_bp": 30.0,
        "primary_comparisons": primary.to_dict("records"),
        "results_blind": True,
        "read_2026": False,
        "fresh_oos": False,
        "returns_or_pnl_evaluated": False,
        "trading_or_production": False,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_sha": os.getenv("GITHUB_SHA"),
    }
    write_json(out/"summary.json", summary)
    output_hashes = {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file()}
    write_json(out/"receipt.json", {"outputs_sha256": output_hashes,
        "rows": {"analysis_frame": int(len(frame)), "results": int(len(result)),
                 "event_metric_cells": int(len(events))},
        "status": "completed_results_blind_structure_study",
        "results_blind": True, "read_2026": False, "production_authority": False})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
