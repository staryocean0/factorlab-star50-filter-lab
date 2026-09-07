"""V3.5 future-label-blind state and measurement support audit.

This audit follows the stopped V3.2/V3.3/V3.4 scale-score route. It never
computes a future shock target, event recall, Clean risk, returns/PnL or a new
risk gate. It separates 2022-2023 state transport from 3s/fine measurement
support drift across STAR50 and CSI1000.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
RESEARCH = HERE.parents[1]
sys.path.insert(0, str(RESEARCH / "first_shock_morphology_v3/code"))
sys.path.insert(0, str(RESEARCH / "first_shock_seconds_v2/code"))
sys.path.insert(0, str(RESEARCH / "first_shock_gate_v1/code"))
import morphology_v3 as m3
import seconds_v2 as v2
import first_shock_gate as g

SYMBOLS = ("000688.SH", "000852.SH")
YEARS = (2022, 2023, 2024, 2025)
REF_YEARS = (2022, 2023)
AUDIT_YEARS = (2024, 2025)
CLOCK_LO = 31
CLOCK_HI = 105
K = 100
SUPPORT_Q = 0.99
STATE = ("log_sigma_pre", "log_rv480")
FINE_SUPPORT = ("fine_gap3_fraction5", "fine_max_age5", "fine_repeat_fraction5")
BANDS = ((31, 55), (56, 80), (81, 105))


def past_only_minute_state(minute: pd.DataFrame) -> pd.DataFrame:
    """Reproduce needed V1 state and first-tail history without future targets."""
    f = minute.reset_index(drop=True).copy()
    for c in ("sigma_pre", "first_tail"):
        f[c] = np.nan
    for _, ix0 in f.groupby("session", sort=False).groups.items():
        ix = np.asarray(ix0)
        r = f.loc[ix, "return_bp"].to_numpy(float)
        rv30 = g.roll_mean(r * r, 30)
        sigma = np.sqrt(np.r_[np.nan, rv30[:-1]])
        event = g.event_flags(r, sigma)
        first = np.full(len(ix), np.nan)
        for j in range(30, len(ix)):
            before = event[j - 30:j]
            if np.isfinite(before).all() and np.isfinite(event[j]):
                first[j] = float(event[j] == 1 and not before.any())
        f.loc[ix, "sigma_pre"] = sigma
        f.loc[ix, "first_tail"] = first
    r = f.return_bp.to_numpy(float)
    rv480 = g.roll_mean(r * r, 480, 456)
    f["log_sigma_pre"] = np.log(np.maximum(f.sigma_pre.to_numpy(float), 1e-8))
    f["log_rv480"] = np.log(np.maximum(rv480, 1e-8))
    return f


def add_past_first_30m(frame: pd.DataFrame) -> pd.DataFrame:
    z = frame.copy()
    z["past_first_tail_30m"] = False
    for _, ix0 in z.groupby("session", sort=False).groups.items():
        ix = np.asarray(ix0)
        minutes = z.loc[ix, "minute"].to_numpy(int)
        first = z.loc[ix, "first_tail"].to_numpy(float)
        past = np.zeros(len(ix), dtype=bool)
        for j, m in enumerate(minutes):
            earlier = (minutes < m) & (minutes >= m - 30) & (first == 1.0)
            past[j] = bool(earlier.any())
        z.loc[ix, "past_first_tail_30m"] = past
    return z


def build_past_only_frame(root: Path, symbol: str) -> tuple[pd.DataFrame, list[dict]]:
    """Build frozen state/fine measurements while never creating a future label."""
    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data

    native = load_market_data(symbol, "1m", "2022-01-01", "2025-12-31", root=root)
    minute = g.minute_panel(native, symbol)
    state = past_only_minute_state(minute)
    fine_parts = []
    morph_rows = []
    audits = []
    for year in YEARS:
        seconds, audit = v2.read_seconds(root, symbol, year)
        groups = {s: x for s, x in seconds.groupby("session", sort=False)}
        year_state = state[state.year == year]
        for session, ix0 in year_state.groupby("session", sort=False).groups.items():
            ix = np.asarray(ix0)
            raw = groups.get(session)
            if raw is None:
                t = np.array([]); p = np.array([]); rows = np.array([], dtype=int)
            else:
                t = raw.second.to_numpy(float)
                p = raw.price.to_numpy(float)
                rows = raw.row_index.to_numpy()
            sample = v2.sample_session(t, p, rows, 15, 15)
            fine = v2.fine_features(sample)
            fine["row_ix"] = ix
            fine_parts.append(fine)
            for local, row_ix in enumerate(ix):
                mm = m3.minute_morphology(sample, local + 1)
                morph_rows.append({
                    "row_ix": row_ix,
                    "quiet_pre": mm.get("quiet_pre"),
                    "pre_support": mm.get("pre_support"),
                })
        audits.append(audit)
        print("AUDIT_MEASURED", symbol, year)
    fine = pd.concat(fine_parts, ignore_index=True).set_index("row_ix").sort_index()
    morph = pd.DataFrame(morph_rows).set_index("row_ix").sort_index()
    q = pd.concat([state, fine, morph], axis=1)
    q["primary_scale_score"] = 0.5 * (
        (q.fine_log_e30 - q.fine_log_e240) + (q.fine_log_e60 - q.fine_log_e240)
    )
    q = add_past_first_30m(q)
    q["month"] = q.day.astype(str).str.slice(0, 7)
    q["minute_band"] = [minute_band(int(m)) for m in q.minute]
    return q, audits


def minute_band(minute: int) -> str:
    for lo, hi in BANDS:
        if lo <= minute <= hi:
            return f"{lo}-{hi}"
    return "outside"


def clock_state_rows(q: pd.DataFrame) -> pd.DataFrame:
    mask = q.minute.between(CLOCK_LO, CLOCK_HI) & np.isfinite(q[list(STATE)]).all(axis=1)
    return q.loc[mask].copy()


def causal_route_rows(q: pd.DataFrame) -> pd.DataFrame:
    mask = (
        q.minute.between(CLOCK_LO, CLOCK_HI)
        & q.quiet_pre.fillna(False).astype(bool)
        & ~(q.first_tail.fillna(0).to_numpy(float) == 1.0)
        & ~q.past_first_tail_30m.fillna(False).astype(bool)
        & np.isfinite(q[["primary_scale_score", *STATE]]).all(axis=1)
    )
    return q.loc[mask].copy()


def group_reference(reference: pd.DataFrame) -> pd.DataFrame:
    """Freeze exact-clock state scales/envelopes and leave-one-out KNN support."""
    rows = []
    for (aft, minute), part in reference.groupby(["afternoon", "minute"], sort=True):
        p = part.sort_values(["year", "session", "day"], kind="stable").reset_index(drop=True)
        x = p[list(STATE)].to_numpy(float)
        scale = np.maximum(np.std(x, axis=0, ddof=0), 1e-8)
        kth = []
        if len(p) >= K + 1:
            for i in range(len(p)):
                d = np.sqrt(np.sum(((x - x[i]) / scale) ** 2, axis=1))
                d[i] = np.inf
                kth.append(float(np.partition(d, K - 1)[K - 1]))
        rows.append({
            "afternoon": int(aft), "minute": int(minute), "reference_rows": int(len(p)),
            "sigma_scale": float(scale[0]), "rv480_scale": float(scale[1]),
            "sigma_q01": float(np.quantile(x[:, 0], .01)), "sigma_q50": float(np.quantile(x[:, 0], .50)),
            "sigma_q99": float(np.quantile(x[:, 0], .99)), "rv480_q01": float(np.quantile(x[:, 1], .01)),
            "rv480_q50": float(np.quantile(x[:, 1], .50)), "rv480_q99": float(np.quantile(x[:, 1], .99)),
            "support_limit_q99": float(np.quantile(kth, SUPPORT_Q)) if kth else np.nan,
            "loo_kth_distance_median": float(np.median(kth)) if kth else np.nan,
        })
    return pd.DataFrame(rows)


def attach_state_support(rows: pd.DataFrame, reference: pd.DataFrame, ref_table: pd.DataFrame) -> pd.DataFrame:
    refs = {
        (int(a), int(m)): x.sort_values(["year", "session", "day"], kind="stable").reset_index(drop=True)
        for (a, m), x in reference.groupby(["afternoon", "minute"], sort=False)
    }
    meta = ref_table.set_index(["afternoon", "minute"]).to_dict("index")
    out = []
    for _, row in rows.iterrows():
        key = (int(row.afternoon), int(row.minute))
        cal = refs.get(key)
        mm = meta.get(key)
        if cal is None or mm is None or len(cal) < K:
            continue
        scale = np.array([mm["sigma_scale"], mm["rv480_scale"]], float)
        target = row[list(STATE)].to_numpy(float)
        x = cal[list(STATE)].to_numpy(float)
        d = np.sqrt(np.sum(((x - target) / scale) ** 2, axis=1))
        kth = float(np.partition(d, K - 1)[K - 1])
        limit = float(mm["support_limit_q99"])
        item = row.to_dict()
        item.update({
            "kth_neighbor_distance": kth,
            "support_limit_q99": limit,
            "state_extrapolated": bool(np.isfinite(limit) and kth > limit),
            "sigma_outside_q01_q99": bool(target[0] < mm["sigma_q01"] or target[0] > mm["sigma_q99"]),
            "rv480_outside_q01_q99": bool(target[1] < mm["rv480_q01"] or target[1] > mm["rv480_q99"]),
            "sigma_center_z": float((target[0] - mm["sigma_q50"]) / scale[0]),
            "rv480_center_z": float((target[1] - mm["rv480_q50"]) / scale[1]),
        })
        out.append(item)
    return pd.DataFrame(out)


def state_summary(z: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for keys, p in z.groupby(group_cols, dropna=False, sort=True):
        if not isinstance(keys, tuple): keys = (keys,)
        item = {c: k for c, k in zip(group_cols, keys)}
        item.update({
            "rows": int(len(p)),
            "state_extrapolated_fraction": float(p.state_extrapolated.mean()),
            "kth_neighbor_distance_median": float(p.kth_neighbor_distance.median()),
            "kth_neighbor_distance_p95": float(p.kth_neighbor_distance.quantile(.95)),
            "sigma_outside_q01_q99_fraction": float(p.sigma_outside_q01_q99.mean()),
            "rv480_outside_q01_q99_fraction": float(p.rv480_outside_q01_q99.mean()),
            "sigma_center_z_mean": float(p.sigma_center_z.mean()),
            "rv480_center_z_mean": float(p.rv480_center_z.mean()),
        })
        rows.append(item)
    return pd.DataFrame(rows)


def measurement_summary(q: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    base = q[q.minute.between(CLOCK_LO, CLOCK_HI)].copy()
    base["primary_score_available"] = np.isfinite(base.primary_scale_score.to_numpy(float))
    rows = []
    for keys, p in base.groupby(group_cols, dropna=False, sort=True):
        if not isinstance(keys, tuple): keys = (keys,)
        item = {c: k for c, k in zip(group_cols, keys)}
        item.update({
            "rows": int(len(p)),
            "primary_score_available_fraction": float(p.primary_score_available.mean()),
        })
        for col in FINE_SUPPORT:
            finite = p[col][np.isfinite(p[col].to_numpy(float))]
            item[f"{col}_available_fraction"] = float(len(finite) / len(p)) if len(p) else np.nan
            item[f"{col}_mean"] = float(finite.mean()) if len(finite) else np.nan
            item[f"{col}_p95"] = float(finite.quantile(.95)) if len(finite) else np.nan
            item[f"{col}_median"] = float(finite.median()) if len(finite) else np.nan
        rows.append(item)
    return pd.DataFrame(rows)


def route_measurement_split(z: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (year, outside), p in z.groupby(["year", "state_extrapolated"], sort=True):
        item = {"year": int(year), "state_extrapolated": bool(outside), "rows": int(len(p))}
        for col in FINE_SUPPORT:
            finite = p[col][np.isfinite(p[col].to_numpy(float))]
            item[f"{col}_mean"] = float(finite.mean()) if len(finite) else np.nan
            item[f"{col}_p95"] = float(finite.quantile(.95)) if len(finite) else np.nan
        rows.append(item)
    return pd.DataFrame(rows)


def compact_year_dict(table: pd.DataFrame, symbol: str) -> dict:
    z = table[table.symbol == symbol] if "symbol" in table.columns else table
    out = {}
    for _, row in z.iterrows():
        year = str(int(row.year))
        out[year] = {c: (bool(v) if isinstance(v, (np.bool_, bool)) else float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v)
                     for c, v in row.items() if c not in {"symbol", "year"}}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(); root = args.repo_root.resolve(); out = args.out.resolve()
    if out.exists() and any(out.iterdir()): raise FileExistsError("immutable output directory")
    out.mkdir(parents=True, exist_ok=True)

    all_state_year = []; all_state_month = []; all_state_half = []; all_state_band = []
    all_measure_year = []; all_measure_month = []
    route_tables = {}; source_audit = {}; ref_tables = []
    route_split = []

    for symbol in SYMBOLS:
        q, audit = build_past_only_frame(root, symbol); source_audit[symbol] = audit
        state = clock_state_rows(q)
        ref = state[state.year.isin(REF_YEARS)].copy()
        eval_rows = state[state.year.isin(AUDIT_YEARS)].copy()
        rt = group_reference(ref); rt["symbol"] = symbol; ref_tables.append(rt)
        attached = attach_state_support(eval_rows, ref, rt.drop(columns="symbol")); attached["symbol"] = symbol
        for groups, sink in ((["symbol", "year"], all_state_year), (["symbol", "year", "month"], all_state_month),
                             (["symbol", "year", "afternoon"], all_state_half), (["symbol", "year", "minute_band"], all_state_band)):
            sink.append(state_summary(attached, groups))
        my = measurement_summary(q, ["year"]); my["symbol"] = symbol; all_measure_year.append(my)
        mm = measurement_summary(q, ["year", "month"]); mm["symbol"] = symbol; all_measure_month.append(mm)

        if symbol == "000688.SH":
            route = causal_route_rows(q)
            route_ref = route[route.year.isin(REF_YEARS)].copy()
            route_eval = route[route.year.isin(AUDIT_YEARS)].copy()
            route_rt = group_reference(route_ref)
            route_attached = attach_state_support(route_eval, route_ref, route_rt)
            route_tables["reference"] = route_rt
            route_tables["year"] = state_summary(route_attached, ["year"])
            route_tables["month"] = state_summary(route_attached, ["year", "month"])
            route_tables["half"] = state_summary(route_attached, ["year", "afternoon"])
            route_tables["band"] = state_summary(route_attached, ["year", "minute_band"])
            route_split.append(route_measurement_split(route_attached))

    state_year = pd.concat(all_state_year, ignore_index=True)
    state_month = pd.concat(all_state_month, ignore_index=True)
    state_half = pd.concat(all_state_half, ignore_index=True)
    state_band = pd.concat(all_state_band, ignore_index=True)
    measure_year = pd.concat(all_measure_year, ignore_index=True)
    measure_month = pd.concat(all_measure_month, ignore_index=True)
    references = pd.concat(ref_tables, ignore_index=True)
    route_split_df = pd.concat(route_split, ignore_index=True) if route_split else pd.DataFrame()

    outputs = {
        "state_reference_groups.csv": references,
        "state_transport_by_year.csv": state_year,
        "state_transport_by_month.csv": state_month,
        "state_transport_by_half.csv": state_half,
        "state_transport_by_minute_band.csv": state_band,
        "measurement_by_year.csv": measure_year,
        "measurement_by_month.csv": measure_month,
        "star50_route_reference_groups.csv": route_tables["reference"],
        "star50_route_state_by_year.csv": route_tables["year"],
        "star50_route_state_by_month.csv": route_tables["month"],
        "star50_route_state_by_half.csv": route_tables["half"],
        "star50_route_state_by_minute_band.csv": route_tables["band"],
        "star50_route_measurement_by_state_support.csv": route_split_df,
    }
    for name, frame in outputs.items(): frame.to_csv(out / name, index=False)

    summary = {
        "schema": "state_measurement_support_audit_v3.5_results",
        "future_labels_used": False,
        "risk_gate_evaluated": False,
        "symbols": list(SYMBOLS),
        "reference_years": list(REF_YEARS),
        "audit_years": list(AUDIT_YEARS),
        "state_transport_by_year": {s: compact_year_dict(state_year, s) for s in SYMBOLS},
        "measurement_by_year": {s: compact_year_dict(measure_year, s) for s in SYMBOLS},
        "star50_route_state_by_year": compact_year_dict(route_tables["year"], "000688.SH"),
        "fresh_oos": False, "read_2026": False,
        "returns_or_pnl_evaluated": False, "production_authority": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "source_audit.json").write_text(json.dumps(source_audit, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
