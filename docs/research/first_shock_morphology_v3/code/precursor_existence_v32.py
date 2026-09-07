"""V3.2 model-free quiet-first precursor existence diagnostic.

Uses frozen V3 event taxonomy and strictly e-2 features. No classifier fit,
no threshold search, no 2026 data, and no missing-observation carry-forward.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
RESEARCH = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(RESEARCH / "first_shock_seconds_v2/code"))
sys.path.insert(0, str(RESEARCH / "first_shock_gate_v1/code"))
import morphology_v3 as m3
import seconds_v2 as v2
import first_shock_gate as g

SYMBOLS = ("000688.SH", "000852.SH")
YEARS = (2022, 2023, 2024, 2025)
SEED = 20260907
FEATURES = ["primary_scale_score", "short_vs_long_vol", "max_short_move", "net5"]


def percentile_rank(value: float, controls: np.ndarray) -> float:
    c = np.asarray(controls, float)
    c = c[np.isfinite(c)]
    if not np.isfinite(value) or not len(c):
        return np.nan
    return float(((c < value).sum() + 0.5 * (c == value).sum()) / len(c))


def add_scores(frame: pd.DataFrame) -> pd.DataFrame:
    q = frame.copy()
    q["primary_scale_score"] = 0.5 * ((q.fine_log_e30 - q.fine_log_e240) +
                                      (q.fine_log_e60 - q.fine_log_e240))
    q["short_vs_long_vol"] = q.fine_log_rv5 - q.fine_log_rv15
    q["max_short_move"] = q.fine_log_max1
    q["net5"] = q.fine_abs_net5
    return q


def build_symbol_frame(root: Path, symbol: str) -> tuple[pd.DataFrame, list[dict]]:
    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data

    native = load_market_data(symbol, "1m", "2022-01-01", "2025-12-31", root=root)
    minute = g.minute_panel(native, symbol)
    feat = g.make_features(minute).reset_index(drop=True)
    fine_parts = []
    morph_rows = []
    audits = []
    for year in YEARS:
        seconds, audit = v2.read_seconds(root, symbol, year)
        groups = {s: z for s, z in seconds.groupby("session", sort=False)}
        year_feat = feat[feat.year == year]
        for session, ix in year_feat.groupby("session", sort=False).groups.items():
            ix = np.asarray(ix)
            raw = groups.get(session)
            if raw is None:
                t = np.array([]); p = np.array([]); rows = np.array([], dtype=int)
            else:
                t = raw.second.to_numpy(float); p = raw.price.to_numpy(float); rows = raw.row_index.to_numpy()
            sample = v2.sample_session(t, p, rows, 15, 15)
            fine = v2.fine_features(sample)
            fine["row_ix"] = ix
            fine_parts.append(fine)
            for local, row_ix in enumerate(ix):
                mm = m3.minute_morphology(sample, local + 1)
                morph_rows.append({"row_ix": row_ix, "quiet_pre": mm.get("quiet_pre"),
                                   "pre_support": mm.get("pre_support")})
        audits.append(audit)
        print("PRECURSOR_MEASURED", symbol, year)
    fine = pd.concat(fine_parts, ignore_index=True).set_index("row_ix").sort_index()
    morph = pd.DataFrame(morph_rows).set_index("row_ix").sort_index()
    q = pd.concat([feat, fine, morph], axis=1)
    q = add_scores(q)
    q["log_sigma_pre"] = np.log(np.maximum(q.sigma_pre.to_numpy(float), 1e-8))
    # Mark proximity to any known first-tail event inside each half-session.
    q["near_first_tail_30m"] = False
    for _, ix in q.groupby("session", sort=False).groups.items():
        ix = np.asarray(ix)
        first = q.loc[ix, "first"].to_numpy(float)
        locs = np.flatnonzero(first == 1)
        near = np.zeros(len(ix), bool)
        for j in locs:
            near[max(0, j-30):min(len(ix), j+31)] = True
        q.loc[ix, "near_first_tail_30m"] = near
    return q, audits


def event_records(q: pd.DataFrame, symbol: str) -> pd.DataFrame:
    records = []
    for ix, row in q.iterrows():
        if not (np.isfinite(row["first"]) and row["first"] == 1 and row["minute"] >= 33):
            continue
        if row["quiet_pre"] is not True:
            continue
        event_minute = int(row.minute)
        feature_minute = event_minute - 2
        f = q[(q.session == row.session) & (q.minute == feature_minute)]
        if len(f) != 1:
            continue
        f = f.iloc[0]
        records.append({"event_row_ix": int(ix), "symbol": symbol, "year": int(row.year),
                        "day": row.day, "session": row.session, "event_minute": event_minute,
                        "feature_minute": feature_minute, **{name: f[name] for name in FEATURES},
                        "match_log_sigma_pre": f.log_sigma_pre,
                        "match_log_rv480": f.log_rv480})
    return pd.DataFrame(records)


def candidate_controls(q: pd.DataFrame, event: pd.Series) -> pd.DataFrame:
    minute = int(event.event_minute)
    feature_minute = minute - 2
    # Candidate anchor itself must be quiet at the same exact clock minute and not near a tail.
    anchors = q[(q.year == event.year) & (q.afternoon == int(event.session.split('/')[-1])) &
                (q.minute == minute) & (q.quiet_pre == True) &
                (~q.near_first_tail_30m) & ~(q["first"] == 1)].copy()
    rows = []
    for _, anchor in anchors.iterrows():
        f = q[(q.session == anchor.session) & (q.minute == feature_minute)]
        if len(f) != 1:
            continue
        f = f.iloc[0]
        vals = {name: f[name] for name in FEATURES}
        vals.update({"control_session": anchor.session, "control_day": anchor.day,
                     "match_log_sigma_pre": f.log_sigma_pre, "match_log_rv480": f.log_rv480})
        if np.isfinite(np.asarray([vals[x] for x in FEATURES] +
                                  [vals["match_log_sigma_pre"], vals["match_log_rv480"]], float)).all():
            rows.append(vals)
    return pd.DataFrame(rows)


def match_event(q: pd.DataFrame, event: pd.Series, max_controls: int = 100) -> pd.DataFrame:
    c = candidate_controls(q, event)
    if len(c) < 30:
        return c
    # Standardize matching state within this event's eligible same-year control pool.
    X = c[["match_log_sigma_pre", "match_log_rv480"]].to_numpy(float)
    scale = np.std(X, axis=0)
    scale = np.maximum(scale, 1e-8)
    center = np.asarray([event.match_log_sigma_pre, event.match_log_rv480], float)
    c = c.copy()
    c["distance"] = np.sqrt(np.sum(((X-center)/scale)**2, axis=1))
    return c.sort_values(["distance", "control_day", "control_session"], kind="stable").head(max_controls)


def analyze_symbol(q: pd.DataFrame, events: pd.DataFrame, symbol: str):
    event_rows = []
    pool_rows = []
    for eid, event in events.reset_index(drop=True).iterrows():
        c = match_event(q, event)
        status = "eligible" if len(c) >= 30 else "insufficient_controls"
        rec = event.to_dict(); rec.update({"event_id": f"{symbol}/{event.session}/{int(event.event_minute)}",
                                           "control_count": len(c), "status": status})
        for name in FEATURES:
            rec[name+"_percentile"] = percentile_rank(event[name], c[name].to_numpy(float)) if len(c) else np.nan
        event_rows.append(rec)
        if len(c):
            cc = c.copy(); cc["event_id"] = rec["event_id"]; pool_rows.append(cc)
    er = pd.DataFrame(event_rows)
    pools = pd.concat(pool_rows, ignore_index=True) if pool_rows else pd.DataFrame()
    return er, pools


def monte_carlo(event_rows: pd.DataFrame, pools: pd.DataFrame, repeats: int = 10000):
    e = event_rows[event_rows.status == "eligible"].copy()
    if e.empty:
        return {"status": "no_eligible_events"}, pd.DataFrame()
    by = {eid: z for eid, z in pools.groupby("event_id", sort=False)}
    observed = float(e.primary_scale_score_percentile.mean())
    rng = np.random.default_rng(SEED)
    ref = np.empty(repeats)
    for j in range(repeats):
        ranks = []
        for _, row in e.iterrows():
            c = by[row.event_id]
            draw = c.iloc[int(rng.integers(0, len(c)))]
            ranks.append(percentile_rank(draw.primary_scale_score, c.primary_scale_score.to_numpy(float)))
        ref[j] = np.mean(ranks)
    out = {"status": "computed", "eligible_events": len(e), "observed_mean_primary_percentile": observed,
           "observed_median_primary_percentile": float(e.primary_scale_score_percentile.median()),
           "reference_quantiles": np.quantile(ref, [.025, .5, .975]).tolist(),
           "fraction_reference_mean_gte_observed_descriptive": float((ref >= observed).mean())}
    for name in FEATURES[1:]:
        out[name+"_mean_percentile"] = float(e[name+"_percentile"].mean())
    return out, pd.DataFrame({"reference_mean_primary_percentile": ref})


def leave_one_year_out(event_rows: pd.DataFrame):
    e = event_rows[event_rows.status == "eligible"].copy()
    rows = []
    for year in sorted(e.year.unique()):
        z = e[e.year != year]
        rows.append({"left_out_year": int(year), "remaining_events": len(z),
                     "mean_primary_percentile": float(z.primary_scale_score_percentile.mean()) if len(z) else None})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(); root = args.repo_root.resolve(); out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("immutable output directory")
    out.mkdir(parents=True, exist_ok=True)
    all_events = []; all_pools = []; summary = {}; audits = {}
    for symbol in SYMBOLS:
        q, audit = build_symbol_frame(root, symbol); audits[symbol] = audit
        events = event_records(q, symbol)
        er, pools = analyze_symbol(q, events, symbol)
        er.to_csv(out/f"{symbol}_quiet_event_ranks.csv", index=False)
        pools.to_csv(out/f"{symbol}_matched_control_pools.csv", index=False)
        loo = leave_one_year_out(er); loo.to_csv(out/f"{symbol}_leave_one_year_out.csv", index=False)
        result, ref = monte_carlo(er, pools); ref.to_csv(out/f"{symbol}_random_reference.csv", index=False)
        summary[symbol] = {"all_quiet_first_events": len(events),
                           "eligible_events": int((er.status == 'eligible').sum()) if len(er) else 0,
                           "excluded_insufficient_controls": int((er.status != 'eligible').sum()) if len(er) else 0,
                           "primary": result,
                           "year_counts": er.groupby('year').size().to_dict() if len(er) else {}}
        all_events.append(er); all_pools.append(pools)
    combined = pd.concat(all_events, ignore_index=True)
    eligible = combined[combined.status == "eligible"]
    combined_result = {"eligible_events": len(eligible),
        "mean_primary_percentile": float(eligible.primary_scale_score_percentile.mean()) if len(eligible) else None,
        "median_primary_percentile": float(eligible.primary_scale_score_percentile.median()) if len(eligible) else None,
        "by_symbol": eligible.groupby('symbol').primary_scale_score_percentile.mean().to_dict() if len(eligible) else {},
        "by_year": eligible.groupby('year').primary_scale_score_percentile.mean().to_dict() if len(eligible) else {}}
    combined.to_csv(out/"all_quiet_event_ranks.csv", index=False)
    g.write_json(out/"source_audit.json", audits)
    g.write_json(out/"summary.json", {"status":"completed model-free precursor existence diagnostic",
                                      "by_symbol":summary, "combined_descriptive":combined_result,
                                      "fresh_oos":False, "production_authority":False})
    print(g.json.dumps(summary, ensure_ascii=False) if hasattr(g, 'json') else summary)


if __name__ == "__main__":
    main()
