from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V11_RUNNER = HERE.parent / "highvol_recovery_survival_v11" / "run_survival.py"
YEARS = (2021, 2022, 2023)
STATES = ("UNSAFE", "RECOVERING")
RV_WINDOW = 12
FUTURE_BARS = 13
P60_BARS = 12
POST_EXPIRY_BARS = 3
MIN_STRATUM_STATE_N = 100


def load_v11():
    spec = importlib.util.spec_from_file_location("v11_for_v12", V11_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(V11_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day_name, z0 in df.groupby("trading_day", sort=False):
        year = int(str(day_name)[:4])
        if year not in YEARS:
            continue
        day = z0.sort_values("timestamp", kind="stable").reset_index(drop=True)
        prev_unsafe = day.risk_state.shift(1).eq("UNSAFE").fillna(False)
        starts = list(day.index[day.shock.fillna(False).astype(bool) & ~prev_unsafe])
        occupied = -1
        episode_no = 0
        for j0 in starts:
            j = int(j0)
            if j <= occupied:
                continue
            normals = day.index[(day.index > j) & day.risk_state.eq("NORMAL")]
            end = int(normals[0]) if len(normals) else None
            occupied = (end - 1) if end is not None else int(day.index.max())
            episode_no += 1
            last_shock = j
            for k in range(j + 1, occupied + 1):
                if bool(day.at[k, "shock"]) if pd.notna(day.at[k, "shock"]) else False:
                    last_shock = k
                    continue
                state = str(day.at[k, "risk_state"])
                if state not in STATES:
                    continue
                age = k - last_shock
                if age <= 0 or k + FUTURE_BARS > int(day.index.max()):
                    continue
                future = day.loc[k + 1:k + FUTURE_BARS].reset_index(drop=True)
                normal_steps = list(np.flatnonzero(future.risk_state.eq("NORMAL").to_numpy()) + 1)
                first_normal_step = int(normal_steps[0]) if normal_steps else None
                p60 = bool(first_normal_step is not None and first_normal_step <= P60_BARS)
                in_window = bool(age <= RV_WINDOW - 1)
                expiry_step = int(RV_WINDOW - age) if in_window else 0
                if in_window and expiry_step < 1:
                    raise RuntimeError((age, expiry_step))
                if in_window:
                    normal_before_expiry = bool(first_normal_step is not None and first_normal_step < expiry_step)
                    survived_non_normal_to_expiry = bool(first_normal_step is None or first_normal_step >= expiry_step)
                    normal_post_expiry15 = bool(
                        first_normal_step is not None
                        and expiry_step <= first_normal_step <= expiry_step + POST_EXPIRY_BARS - 1
                    )
                else:
                    normal_before_expiry = False
                    survived_non_normal_to_expiry = False
                    normal_post_expiry15 = False
                rows.append({
                    "episode_id": f"{day.at[j, 'symbol']}|{day_name}|{episode_no}",
                    "symbol": str(day.at[j, "symbol"]),
                    "year": year,
                    "trading_day": str(day_name),
                    "timestamp": str(day.at[k, "timestamp"]),
                    "current_state": state,
                    "recent_shock_age_bars": int(age),
                    "shock_in_rv12": in_window,
                    "bars_until_shock_exits": expiry_step if in_window else 0,
                    "first_normal_step": first_normal_step,
                    "normal_within_60m": p60,
                    "normal_before_expiry": normal_before_expiry,
                    "survived_non_normal_to_expiry": survived_non_normal_to_expiry,
                    "normal_in_first15m_post_expiry": normal_post_expiry15,
                })
    return pd.DataFrame(rows)


def beta_prob(successes: int, n: int) -> float:
    return float((successes + 1) / (n + 2))


def p60_table(rows: pd.DataFrame) -> list[dict]:
    out = []
    groups = [("pooled", "pooled", rows)] + [("year", str(y), rows[rows.year == y]) for y in YEARS]
    for gt, gv, base in groups:
        for inside in (True, False):
            for state in STATES:
                g = base[(base.shock_in_rv12 == inside) & (base.current_state == state)]
                n = int(len(g)); s = int(g.normal_within_60m.sum()) if n else 0
                out.append({
                    "group_type": gt,
                    "group_value": gv,
                    "shock_in_rv12": bool(inside),
                    "current_state": state,
                    "n": n,
                    "successes_60m": s,
                    "p_normal_within_60m": beta_prob(s, n) if n else None,
                })
    return out


def expiry_hazard_table(rows: pd.DataFrame) -> list[dict]:
    eligible = rows[rows.shock_in_rv12 & rows.survived_non_normal_to_expiry].copy()
    out = []
    groups = [("pooled", "pooled", eligible)] + [("year", str(y), eligible[eligible.year == y]) for y in YEARS]
    for gt, gv, base in groups:
        for state in STATES:
            g = base[base.current_state == state]
            n = int(len(g)); s = int(g.normal_in_first15m_post_expiry.sum()) if n else 0
            out.append({
                "group_type": gt,
                "group_value": gv,
                "current_state": state,
                "n_survived_to_expiry": n,
                "post_expiry15_normalizations": s,
                "p_normal_first15m_post_expiry": beta_prob(s, n) if n else None,
            })
    return out


def lookup(rows: list[dict], **kwargs) -> dict:
    return next(r for r in rows if all(r[k] == v for k, v in kwargs.items()))


def gap60(table: list[dict], gt: str, gv: str, inside: bool) -> float | None:
    u = lookup(table, group_type=gt, group_value=gv, shock_in_rv12=inside, current_state="UNSAFE")
    r = lookup(table, group_type=gt, group_value=gv, shock_in_rv12=inside, current_state="RECOVERING")
    if u["p_normal_within_60m"] is None or r["p_normal_within_60m"] is None:
        return None
    return float(r["p_normal_within_60m"] - u["p_normal_within_60m"])


def expiry_gap(table: list[dict], gt: str, gv: str) -> float | None:
    u = lookup(table, group_type=gt, group_value=gv, current_state="UNSAFE")
    r = lookup(table, group_type=gt, group_value=gv, current_state="RECOVERING")
    if u["p_normal_first15m_post_expiry"] is None or r["p_normal_first15m_post_expiry"] is None:
        return None
    return float(u["p_normal_first15m_post_expiry"] - r["p_normal_first15m_post_expiry"])


def clean(v):
    if isinstance(v, dict): return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list): return [clean(x) for x in v]
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating, float)):
        x = float(v); return x if np.isfinite(x) else None
    if isinstance(v, (np.bool_,)): return bool(v)
    return v


def run(root: Path, out: Path) -> dict:
    v11 = load_v11()
    if v11.RV_WINDOW != RV_WINDOW or v11.HIGHVOL_RATIO != 1.50 or v11.RECOVERY_NORMAL_RATIO != 1.10 or v11.SHOCK_SIGMA != 3.0:
        raise RuntimeError("V11/V12 inherited state constants drift")
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in v11.SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([build_rows(frames[s]) for s in v11.SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("no V12 rows")

    p60 = p60_table(rows)
    expiry = expiry_hazard_table(rows)
    pooled_in = gap60(p60, "pooled", "pooled", True)
    pooled_out = gap60(p60, "pooled", "pooled", False)
    annual_in = {str(y): gap60(p60, "year", str(y), True) for y in YEARS}
    annual_out = {str(y): gap60(p60, "year", str(y), False) for y in YEARS}
    pooled_expiry = expiry_gap(expiry, "pooled", "pooled")
    annual_expiry = {str(y): expiry_gap(expiry, "year", str(y)) for y in YEARS}

    pooled_ns = {}
    for inside in (True, False):
        label = "in_window" if inside else "expired"
        pooled_ns[label] = {state: lookup(p60, group_type="pooled", group_value="pooled", shock_in_rv12=inside, current_state=state)["n"] for state in STATES}

    acceptance = {
        "both_states_n_ge_100_in_both_structural_strata": bool(all(n >= MIN_STRATUM_STATE_N for d in pooled_ns.values() for n in d.values())),
        "pooled_in_window_60m_gap_negative": bool(pooled_in is not None and pooled_in < 0),
        "pooled_expired_60m_gap_positive": bool(pooled_out is not None and pooled_out > 0),
        "in_window_negative_gap_at_least_2_of_3_years": bool(sum(v is not None and v < 0 for v in annual_in.values()) >= 2),
        "expired_positive_gap_at_least_2_of_3_years": bool(sum(v is not None and v > 0 for v in annual_out.values()) >= 2),
        "pooled_unsafe_post_expiry15_hazard_gt_recovering": bool(pooled_expiry is not None and pooled_expiry > 0),
        "unsafe_post_expiry15_hazard_gt_recovering_at_least_2_of_3_years": bool(sum(v is not None and v > 0 for v in annual_expiry.values()) >= 2),
        "rv12_length_unchanged": True,
        "state_thresholds_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    summary = {
        "schema": "highvol_shock_expiry_mechanism_v12_development",
        "development_only": True,
        "development_years": list(YEARS),
        "row_count": int(len(rows)),
        "future_support_bars": FUTURE_BARS,
        "rv_window_bars": RV_WINDOW,
        "structural_cutoff": "shock_in_rv12 iff recent_shock_age_bars <= 11; expired iff >=12",
        "p60_table": p60,
        "expiry_hazard_table": expiry,
        "pooled_60m_gap_recovering_minus_unsafe": {"shock_in_rv12": pooled_in, "shock_expired": pooled_out},
        "annual_60m_gap_recovering_minus_unsafe": {"shock_in_rv12": annual_in, "shock_expired": annual_out},
        "pooled_post_expiry15_gap_unsafe_minus_recovering": pooled_expiry,
        "annual_post_expiry15_gap_unsafe_minus_recovering": annual_expiry,
        "pooled_stratum_state_counts": pooled_ns,
        "acceptance": acceptance,
        "shock_expiry_mechanism_supported": bool(all(acceptance.values())),
        "threshold_search_performed": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
    }
    out.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(out / "expiry_rows.parquet", index=False)
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
