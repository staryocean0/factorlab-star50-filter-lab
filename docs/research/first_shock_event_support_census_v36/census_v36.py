"""V3.6 event-support census for frozen V1 first-tail events.

No predictor is defined or evaluated. 2022-2023 provide exact-clock historical
state support only. 2024-2025 first-tail events are classified from e-2 state
and an ex-post peer-tail proximity subtype. The stopped V3.2 scale score is not
loaded or used.
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
sys.path.insert(0, str(RESEARCH / "first_shock_gate_v1/code"))
import first_shock_gate as g

SYMBOLS = ("000688.SH", "000852.SH")
PEER = {"000688.SH": "000852.SH", "000852.SH": "000688.SH"}
YEARS = (2022, 2023, 2024, 2025)
REF_YEARS = (2022, 2023)
CENSUS_YEARS = (2024, 2025)
STATE_MINUTE_LO = 31
STATE_MINUTE_HI = 118
EVENT_MINUTE_LO = 33
EVENT_MINUTE_HI = 120
K = 100
SUPPORT_Q = 0.99
STATE = ("log_sigma_pre", "log_rv480")
ORDINARY_UPPER_RANK = 0.80
MIN_ISOLATED_ORDINARY_EVENTS_PER_YEAR = 10
EVENT_BANDS = ((33, 60), (61, 90), (91, 120))


def event_band(minute: int) -> str:
    for lo, hi in EVENT_BANDS:
        if lo <= minute <= hi:
            return f"{lo}-{hi}"
    return "outside"


def past_only_state(minute: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the frozen V1 state/event definitions without future targets."""
    f = minute.reset_index(drop=True).copy()
    f["sigma_pre"] = np.nan
    f["tail_event"] = np.nan
    f["first_tail"] = np.nan
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
        f.loc[ix, "tail_event"] = event
        f.loc[ix, "first_tail"] = first
    r = f.return_bp.to_numpy(float)
    rv480 = g.roll_mean(r * r, 480, 456)
    f["log_sigma_pre"] = np.log(np.maximum(f.sigma_pre.to_numpy(float), 1e-8))
    f["log_rv480"] = np.log(np.maximum(rv480, 1e-8))
    return f


def load_symbol(root: Path, symbol: str) -> pd.DataFrame:
    sys.path.insert(0, str(root / "src"))
    from star50_filter.cloud_market_data import load_market_data
    native = load_market_data(symbol, "1m", "2022-01-01", "2025-12-31", root=root)
    q = past_only_state(g.minute_panel(native, symbol))
    q["symbol"] = symbol
    q["event_band"] = [event_band(int(m)) for m in q.minute]
    return q


def _state_scale(part: pd.DataFrame) -> np.ndarray:
    return np.maximum(np.std(part[list(STATE)].to_numpy(float), axis=0, ddof=0), 1e-8)


def reference_table(reference: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (aft, minute), part in reference.groupby(["afternoon", "minute"], sort=True):
        p = part.sort_values(["year", "session", "day"], kind="stable").reset_index(drop=True)
        x = p[list(STATE)].to_numpy(float)
        scale = _state_scale(p)
        kth = []
        if len(p) >= K + 1:
            for i in range(len(p)):
                d = np.sqrt(np.sum(((x - x[i]) / scale) ** 2, axis=1))
                d[i] = np.inf
                kth.append(float(np.partition(d, K - 1)[K - 1]))
        rows.append({
            "afternoon": int(aft),
            "minute": int(minute),
            "reference_rows": int(len(p)),
            "sigma_scale": float(scale[0]),
            "rv480_scale": float(scale[1]),
            "support_limit_q99": float(np.quantile(kth, SUPPORT_Q)) if kth else np.nan,
        })
    return pd.DataFrame(rows)


def midrank_percentile(value: float, controls: np.ndarray) -> float:
    x = np.asarray(controls, float)
    x = x[np.isfinite(x)]
    if not np.isfinite(value) or len(x) == 0:
        return float("nan")
    return float(np.mean(x < value) + 0.5 * np.mean(x == value))


def attach_eval_state(eval_rows: pd.DataFrame, reference: pd.DataFrame, ref_meta: pd.DataFrame) -> pd.DataFrame:
    refs = {
        (int(a), int(m)): p.sort_values(["year", "session", "day"], kind="stable").reset_index(drop=True)
        for (a, m), p in reference.groupby(["afternoon", "minute"], sort=False)
    }
    meta = ref_meta.set_index(["afternoon", "minute"]).to_dict("index")
    out = []
    for _, row in eval_rows.iterrows():
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
            "state_supported": bool(np.isfinite(limit) and kth <= limit),
            "kth_neighbor_distance": kth,
            "support_limit_q99": limit,
            "sigma_pct": midrank_percentile(float(row.log_sigma_pre), cal.log_sigma_pre.to_numpy(float)),
            "rv480_pct": midrank_percentile(float(row.log_rv480), cal.log_rv480.to_numpy(float)),
        })
        out.append(item)
    return pd.DataFrame(out)


def paired_state_table(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Build e-2-capable synchronized state descriptors for both indices."""
    attached: dict[str, pd.DataFrame] = {}
    for symbol, q in frames.items():
        base = q[
            q.minute.between(STATE_MINUTE_LO, STATE_MINUTE_HI)
            & np.isfinite(q[list(STATE)]).all(axis=1)
        ].copy()
        ref = base[base.year.isin(REF_YEARS)].copy()
        meta = reference_table(ref)
        ev = base[base.year.isin(CENSUS_YEARS)].copy()
        z = attach_eval_state(ev, ref, meta)
        attached[symbol] = z

    keys = ["year", "day", "afternoon", "minute"]
    cols = keys + ["session", "state_supported", "kth_neighbor_distance", "support_limit_q99", "sigma_pct", "rv480_pct"]
    a = attached[SYMBOLS[0]][cols].copy()
    b = attached[SYMBOLS[1]][cols].copy()
    if a[keys].duplicated().any() or b[keys].duplicated().any():
        raise RuntimeError("state key is not unique")
    a = a.rename(columns={c: f"s0_{c}" for c in a.columns if c not in keys})
    b = b.rename(columns={c: f"s1_{c}" for c in b.columns if c not in keys})
    paired = a.merge(b, on=keys, how="outer", validate="one_to_one", indicator=True)
    return paired.sort_values(keys, kind="stable").reset_index(drop=True), attached


def peer_tail_nearby(peer_frame: pd.DataFrame, day: str, afternoon: int, event_minute: int) -> bool:
    p = peer_frame[
        (peer_frame.day.astype(str) == str(day))
        & (peer_frame.afternoon.astype(int) == int(afternoon))
        & peer_frame.minute.between(event_minute - 2, event_minute + 2)
    ]
    return bool((p.tail_event.fillna(0).to_numpy(float) == 1.0).any())


def support_class(target_supported, peer_supported, available: bool) -> str:
    if not available or pd.isna(target_supported) or pd.isna(peer_supported):
        return "peer_or_target_state_unavailable"
    t, p = bool(target_supported), bool(peer_supported)
    if t and p:
        return "both_supported"
    if (not t) and p:
        return "target_extrapolated_only"
    if t and (not p):
        return "peer_extrapolated_only"
    return "both_extrapolated"


def upper_state_bin(rank: float) -> str:
    if not np.isfinite(rank):
        return "unavailable"
    if rank <= 0.50:
        return "q00_50"
    if rank <= 0.80:
        return "q50_80"
    if rank <= 0.95:
        return "q80_95"
    return "q95_100"


def build_event_table(frames: dict[str, pd.DataFrame], paired: pd.DataFrame) -> pd.DataFrame:
    keys = ["year", "day", "afternoon", "minute"]
    paired_lookup = paired.set_index(keys, drop=False)
    rows = []
    for target in SYMBOLS:
        peer = PEER[target]
        target_prefix = "s0_" if target == SYMBOLS[0] else "s1_"
        peer_prefix = "s1_" if target == SYMBOLS[0] else "s0_"
        events = frames[target][
            frames[target].year.isin(CENSUS_YEARS)
            & (frames[target].first_tail.fillna(0).to_numpy(float) == 1.0)
            & frames[target].minute.between(EVENT_MINUTE_LO, EVENT_MINUTE_HI)
        ].copy()
        for _, event in events.iterrows():
            e = int(event.minute)
            key = (int(event.year), str(event.day), int(event.afternoon), e - 2)
            state_available = key in paired_lookup.index
            if state_available:
                ps = paired_lookup.loc[key]
                if isinstance(ps, pd.DataFrame):
                    raise RuntimeError(f"nonunique paired state key {key}")
                t_supported = ps.get(target_prefix + "state_supported", np.nan)
                p_supported = ps.get(peer_prefix + "state_supported", np.nan)
                values = [
                    ps.get(target_prefix + "sigma_pct", np.nan),
                    ps.get(target_prefix + "rv480_pct", np.nan),
                    ps.get(peer_prefix + "sigma_pct", np.nan),
                    ps.get(peer_prefix + "rv480_pct", np.nan),
                ]
                available = bool(ps.get("_merge") == "both" and np.isfinite(np.asarray(values, float)).all())
                joint = float(np.max(values)) if available else float("nan")
            else:
                t_supported = p_supported = np.nan
                available = False
                values = [np.nan] * 4
                joint = float("nan")
            sc = support_class(t_supported, p_supported, available)
            peer_near = peer_tail_nearby(frames[peer], str(event.day), int(event.afternoon), e)
            ordinary = bool(sc == "both_supported" and np.isfinite(joint) and joint <= ORDINARY_UPPER_RANK)
            rows.append({
                "event_id": f"{target}/{event.day}/{int(event.afternoon)}/{e}",
                "target_symbol": target,
                "peer_symbol": peer,
                "year": int(event.year),
                "day": str(event.day),
                "afternoon": int(event.afternoon),
                "event_minute": e,
                "event_band": event_band(e),
                "state_minute_e_minus_2": e - 2,
                "target_state_supported": t_supported,
                "peer_state_supported": p_supported,
                "support_class": sc,
                "target_sigma_pct": values[0],
                "target_rv480_pct": values[1],
                "peer_sigma_pct": values[2],
                "peer_rv480_pct": values[3],
                "joint_upper_state_rank": joint,
                "joint_upper_state_bin": upper_state_bin(joint),
                "ordinary_common_state": ordinary,
                "peer_tail_nearby_pm2": peer_near,
                "isolated_first_tail": not peer_near,
                "ordinary_isolated_first_tail": ordinary and not peer_near,
            })
    return pd.DataFrame(rows).sort_values(["target_symbol", "year", "day", "afternoon", "event_minute"], kind="stable").reset_index(drop=True)


def counts(frame: pd.DataFrame, group_cols: list[str], value_name: str = "events") -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=[*group_cols, value_name])
    return frame.groupby(group_cols, dropna=False, sort=True).size().rename(value_name).reset_index()


def raw_event_counts(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for symbol, q in frames.items():
        for year in YEARS:
            p = q[q.year == year]
            raw = int((p.first_tail.fillna(0).to_numpy(float) == 1.0).sum())
            precursor = int(((p.first_tail.fillna(0).to_numpy(float) == 1.0) & p.minute.between(EVENT_MINUTE_LO, EVENT_MINUTE_HI)).sum())
            rows.append({"symbol": symbol, "year": year, "raw_first_tail_events": raw, "precursor_eligible_events": precursor})
    return pd.DataFrame(rows)


def admission(event_table: pd.DataFrame) -> dict:
    checks = []
    for symbol in SYMBOLS:
        per_year = {}
        ok = True
        for year in CENSUS_YEARS:
            n = int(((event_table.target_symbol == symbol) & (event_table.year == year) & event_table.ordinary_isolated_first_tail).sum())
            per_year[str(year)] = n
            ok = ok and n >= MIN_ISOLATED_ORDINARY_EVENTS_PER_YEAR
        checks.append({
            "target_symbol": symbol,
            "ordinary_isolated_first_tail_by_year": per_year,
            "minimum_required_each_year": MIN_ISOLATED_ORDINARY_EVENTS_PER_YEAR,
            "model_free_residual_precursor_existence_may_open": bool(ok),
        })
    return {
        "classifier_or_gate_model": "prohibited",
        "target_checks": checks,
        "next_step_if_pass": "preregister one new cross-index residual precursor score; event-vs-matched-control existence only",
        "next_step_if_fail": "do not fit sparse-event predictor on consumed 2024-2025 history",
    }


def sync_diagnostics(paired: pd.DataFrame) -> dict:
    by_year = {}
    for year in CENSUS_YEARS:
        p = paired[paired.year == year]
        by_year[str(year)] = {
            "paired_rows": int(len(p)),
            "both_indices_present": int((p._merge == "both").sum()),
            "both_indices_present_fraction": float((p._merge == "both").mean()) if len(p) else None,
        }
    return by_year


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(); root = args.repo_root.resolve(); out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("immutable output directory")
    out.mkdir(parents=True, exist_ok=True)

    frames = {s: load_symbol(root, s) for s in SYMBOLS}
    paired, _ = paired_state_table(frames)
    event_table = build_event_table(frames, paired)
    raw = raw_event_counts(frames)

    tables = {
        "raw_event_counts.csv": raw,
        "events.csv": event_table,
        "events_by_support_class.csv": counts(event_table, ["target_symbol", "year", "support_class"]),
        "events_by_upper_state_bin.csv": counts(event_table[event_table.support_class == "both_supported"], ["target_symbol", "year", "joint_upper_state_bin"]),
        "ordinary_events_by_peer_subtype.csv": counts(event_table[event_table.ordinary_common_state], ["target_symbol", "year", "isolated_first_tail"]),
        "events_by_half.csv": counts(event_table, ["target_symbol", "year", "afternoon", "ordinary_common_state", "isolated_first_tail"]),
        "events_by_event_band.csv": counts(event_table, ["target_symbol", "year", "event_band", "ordinary_common_state", "isolated_first_tail"]),
    }
    for name, table in tables.items():
        table.to_csv(out / name, index=False)

    summary = {
        "schema": "first_shock_event_support_census_v3.6_results",
        "symbols": list(SYMBOLS),
        "historical_state_reference_years": list(REF_YEARS),
        "primary_census_years": list(CENSUS_YEARS),
        "future_predictor_defined": False,
        "v32_scale_score_used": False,
        "raw_event_counts": raw.to_dict("records"),
        "sync_diagnostics": sync_diagnostics(paired),
        "event_counts_primary": {
            symbol: {
                str(year): {
                    "precursor_eligible_events": int(((event_table.target_symbol == symbol) & (event_table.year == year)).sum()),
                    "both_supported": int(((event_table.target_symbol == symbol) & (event_table.year == year) & (event_table.support_class == "both_supported")).sum()),
                    "ordinary_common_state": int(((event_table.target_symbol == symbol) & (event_table.year == year) & event_table.ordinary_common_state).sum()),
                    "ordinary_isolated_first_tail": int(((event_table.target_symbol == symbol) & (event_table.year == year) & event_table.ordinary_isolated_first_tail).sum()),
                    "peer_tail_nearby_pm2": int(((event_table.target_symbol == symbol) & (event_table.year == year) & event_table.peer_tail_nearby_pm2).sum()),
                }
                for year in CENSUS_YEARS
            }
            for symbol in SYMBOLS
        },
        "downstream_admission": admission(event_table),
        "fresh_oos": False,
        "read_2026": False,
        "returns_or_pnl_evaluated": False,
        "production_authority": False,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
