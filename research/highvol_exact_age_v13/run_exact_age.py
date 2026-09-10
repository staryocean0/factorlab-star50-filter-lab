from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V12_RUNNER = HERE.parent / "highvol_shock_expiry_v12" / "run_expiry.py"
YEARS = (2021, 2022, 2023)
STATES = ("UNSAFE", "RECOVERING")
EXACT_AGES = tuple(range(1, 12))
RV_WINDOW = 12


def load_v12():
    spec = importlib.util.spec_from_file_location("v12_for_v13", V12_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(V12_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def beta_prob(successes: int, n: int) -> float:
    return float((successes + 1) / (n + 2))


def build_input(root: Path) -> pd.DataFrame:
    v12 = load_v12()
    v11 = v12.load_v11()
    if v12.RV_WINDOW != RV_WINDOW or v11.RV_WINDOW != RV_WINDOW:
        raise RuntimeError("rv12 length drift")
    if v11.HIGHVOL_RATIO != 1.50 or v11.RECOVERY_NORMAL_RATIO != 1.10 or v11.SHOCK_SIGMA != 3.0:
        raise RuntimeError("inherited state threshold drift")
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in v11.SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v12.build_rows(frames[s]) for s in v11.SYMBOLS], ignore_index=True)
    rows = rows[rows.recent_shock_age_bars.isin(EXACT_AGES)].copy()
    if rows.empty:
        raise RuntimeError("no exact-age rows")
    if not rows.shock_in_rv12.all():
        raise RuntimeError("exact-age input must all have shock inside rv12")
    return rows


def exact_table(rows: pd.DataFrame) -> list[dict]:
    out = []
    groups = [("pooled", "pooled", rows)] + [("year", str(y), rows[rows.year == y]) for y in YEARS]
    for gt, gv, base in groups:
        for age in EXACT_AGES:
            for state in STATES:
                g = base[(base.recent_shock_age_bars == age) & (base.current_state == state)]
                n = int(len(g)); s = int(g.normal_within_60m.sum()) if n else 0
                out.append({
                    "group_type": gt,
                    "group_value": gv,
                    "exact_age_bars": age,
                    "current_state": state,
                    "n": n,
                    "successes_60m": s,
                    "p60": beta_prob(s, n) if n else None,
                })
    return out


def lookup(table: list[dict], gt: str, gv: str, age: int, state: str) -> dict:
    return next(r for r in table if r["group_type"] == gt and r["group_value"] == gv and r["exact_age_bars"] == age and r["current_state"] == state)


def standardize(table: list[dict], gt: str, gv: str) -> dict:
    cells = []
    for age in EXACT_AGES:
        u = lookup(table, gt, gv, age, "UNSAFE")
        r = lookup(table, gt, gv, age, "RECOVERING")
        if u["n"] > 0 and r["n"] > 0:
            cells.append((age, u, r))
    total = sum(u["n"] + r["n"] for _, u, r in cells)
    if total <= 0:
        return {"group_type": gt, "group_value": gv, "common_ages": [], "standardized_unsafe_p60": None, "standardized_recovering_p60": None, "gap_recovering_minus_unsafe": None}
    pu = 0.0; pr = 0.0; weights = []
    for age, u, r in cells:
        w = float((u["n"] + r["n"]) / total)
        weights.append({"exact_age_bars": age, "weight": w, "unsafe_n": u["n"], "recovering_n": r["n"], "unsafe_p60": u["p60"], "recovering_p60": r["p60"], "age_gap": float(r["p60"] - u["p60"])})
        pu += w * float(u["p60"])
        pr += w * float(r["p60"])
    return {
        "group_type": gt,
        "group_value": gv,
        "common_ages": [x[0] for x in cells],
        "weights": weights,
        "standardized_unsafe_p60": pu,
        "standardized_recovering_p60": pr,
        "gap_recovering_minus_unsafe": float(pr - pu),
    }


def raw_gap(rows: pd.DataFrame) -> float:
    probs = {}
    for state in STATES:
        g = rows[rows.current_state == state]
        probs[state] = beta_prob(int(g.normal_within_60m.sum()), int(len(g)))
    return float(probs["RECOVERING"] - probs["UNSAFE"])


def clean(v):
    if isinstance(v, dict): return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list): return [clean(x) for x in v]
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating, float)):
        x = float(v); return x if np.isfinite(x) else None
    if isinstance(v, (np.bool_,)): return bool(v)
    return v


def run(root: Path, out: Path) -> dict:
    rows = build_input(root)
    table = exact_table(rows)
    pooled_std = standardize(table, "pooled", "pooled")
    annual_std = {str(y): standardize(table, "year", str(y)) for y in YEARS}
    pooled_raw = raw_gap(rows)
    annual_raw = {str(y): raw_gap(rows[rows.year == y]) for y in YEARS}
    pooled_common_all = pooled_std["common_ages"] == list(EXACT_AGES)
    annual_nonnegative = sum(v["gap_recovering_minus_unsafe"] is not None and v["gap_recovering_minus_unsafe"] >= 0 for v in annual_std.values())

    acceptance = {
        "all_exact_ages_1_to_11_have_both_states_pooled": bool(pooled_common_all),
        "raw_pooled_in_window_gap_negative": bool(pooled_raw < 0),
        "standardized_pooled_gap_nonnegative": bool(pooled_std["gap_recovering_minus_unsafe"] is not None and pooled_std["gap_recovering_minus_unsafe"] >= 0),
        "standardized_gap_nonnegative_at_least_2_of_3_years": bool(annual_nonnegative >= 2),
        "rv12_length_unchanged": True,
        "state_thresholds_unchanged": True,
        "outcome_60m_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    summary = {
        "schema": "highvol_exact_age_standardization_v13_development",
        "development_only": True,
        "development_years": list(YEARS),
        "row_count": int(len(rows)),
        "exact_ages_bars": list(EXACT_AGES),
        "exact_age_table": table,
        "raw_gap_recovering_minus_unsafe": {"pooled": pooled_raw, "annual": annual_raw},
        "standardized": {"pooled": pooled_std, "annual": annual_std},
        "acceptance": acceptance,
        "broad_bucket_composition_explanation_supported": bool(all(acceptance.values())),
        "threshold_search_performed": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
    }
    out.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(out / "exact_age_rows.parquet", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    run(a.repo_root.resolve(), a.out.resolve())


if __name__ == "__main__":
    main()
