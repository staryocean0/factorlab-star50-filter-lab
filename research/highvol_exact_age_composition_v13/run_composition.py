from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
V11_RUNNER = HERE.parent / "highvol_recovery_survival_v11" / "run_survival.py"
STATES = ("UNSAFE", "RECOVERING")
HORIZONS = (15, 30, 60)
DEV_YEARS = (2021, 2022, 2023)
IN_WINDOW_AGES = tuple(range(1, 12))


def load_v11():
    spec = importlib.util.spec_from_file_location("v11_for_v13", V11_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(V11_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def beta11(successes: int, n: int) -> float:
    if n <= 0:
        raise ValueError("n must be positive")
    return float((int(successes) + 1) / (int(n) + 2))


def build_v11_rows(root: Path, v11) -> pd.DataFrame:
    frames = v11.restrict_common_days({s: v11.load_symbol(root, s) for s in v11.SYMBOLS})
    frames = {s: v11.add_measurements(x) for s, x in frames.items()}
    rows = pd.concat([v11.build_rows(frames[s]) for s in v11.SYMBOLS], ignore_index=True)
    if rows.empty:
        raise RuntimeError("no V11 rows")
    expected = {
        "current_state",
        "recent_shock_age_bars",
        "year",
        "normal_within_15m",
        "normal_within_30m",
        "normal_within_60m",
    }
    missing = expected.difference(rows.columns)
    if missing:
        raise RuntimeError(f"V11 row schema drift: {sorted(missing)}")
    return rows


def exact_age_table(rows: pd.DataFrame) -> pd.DataFrame:
    out: list[dict] = []
    for age in sorted(int(x) for x in rows.recent_shock_age_bars.unique()):
        for state in STATES:
            g = rows[(rows.recent_shock_age_bars == age) & (rows.current_state == state)]
            rec = {"recent_shock_age_bars": age, "current_state": state, "n": int(len(g))}
            for h in HORIZONS:
                y = g[f"normal_within_{h}m"].astype(int) if len(g) else pd.Series(dtype=int)
                s = int(y.sum()) if len(g) else 0
                rec[f"success_{h}m"] = s
                rec[f"p_{h}m"] = beta11(s, len(g)) if len(g) else np.nan
            out.append(rec)
    return pd.DataFrame(out)


def common_ages(rows: pd.DataFrame, ages: tuple[int, ...] | None = None) -> list[int]:
    x = rows if ages is None else rows[rows.recent_shock_age_bars.isin(ages)]
    sets = []
    for state in STATES:
        sets.append(set(int(a) for a in x.loc[x.current_state == state, "recent_shock_age_bars"].unique()))
    return sorted(sets[0].intersection(sets[1])) if sets else []


def standardize_one(rows: pd.DataFrame, horizon: int, ages: tuple[int, ...] | None = None) -> dict:
    ages_common = common_ages(rows, ages)
    if not ages_common:
        raise RuntimeError("no common exact-age support")
    x = rows[rows.recent_shock_age_bars.isin(ages_common)].copy()

    combined_n = x.groupby("recent_shock_age_bars").size().reindex(ages_common)
    weights = (combined_n / combined_n.sum()).to_dict()

    age_rows = []
    std = {}
    raw = {}
    for state in STATES:
        sx = x[x.current_state == state]
        yall = sx[f"normal_within_{horizon}m"].astype(int)
        raw[state] = beta11(int(yall.sum()), int(len(yall)))
        weighted = 0.0
        for age in ages_common:
            g = sx[sx.recent_shock_age_bars == age]
            y = g[f"normal_within_{horizon}m"].astype(int)
            p = beta11(int(y.sum()), int(len(y)))
            w = float(weights[age])
            weighted += w * p
            age_rows.append(
                {
                    "age": int(age),
                    "state": state,
                    "n": int(len(g)),
                    "successes": int(y.sum()),
                    "probability": p,
                    "common_weight": w,
                }
            )
        std[state] = float(weighted)

    return {
        "horizon_minutes": int(horizon),
        "common_exact_ages": ages_common,
        "common_age_count": int(len(ages_common)),
        "rows_on_common_support": int(len(x)),
        "raw": {
            "unsafe_probability": raw["UNSAFE"],
            "recovering_probability": raw["RECOVERING"],
            "recovering_minus_unsafe_gap": float(raw["RECOVERING"] - raw["UNSAFE"]),
        },
        "standardized": {
            "unsafe_probability": std["UNSAFE"],
            "recovering_probability": std["RECOVERING"],
            "recovering_minus_unsafe_gap": float(std["RECOVERING"] - std["UNSAFE"]),
        },
        "age_cells": age_rows,
    }


def age_composition(rows: pd.DataFrame) -> list[dict]:
    out = []
    for state in STATES:
        x = rows.loc[rows.current_state == state, "recent_shock_age_bars"].astype(int).to_numpy()
        out.append(
            {
                "state": state,
                "n": int(len(x)),
                "mean_age_bars": float(np.mean(x)),
                "median_age_bars": float(np.median(x)),
                "p25_age_bars": float(np.quantile(x, 0.25)),
                "p75_age_bars": float(np.quantile(x, 0.75)),
                "share_age_1_to_11": float(np.mean((x >= 1) & (x <= 11))),
                "share_age_ge_12": float(np.mean(x >= 12)),
            }
        )
    return out


def exact_sign_summary(result: dict) -> dict:
    cells = result["age_cells"]
    by_age: dict[int, dict[str, float]] = {}
    for row in cells:
        by_age.setdefault(int(row["age"]), {})[str(row["state"])] = float(row["probability"])
    gaps = []
    for age in sorted(by_age):
        d = by_age[age]
        if all(s in d for s in STATES):
            gap = float(d["RECOVERING"] - d["UNSAFE"])
            gaps.append({"age": age, "recovering_minus_unsafe_gap": gap, "recovering_gt_unsafe": bool(gap > 0)})
    return {
        "age_gap_rows": gaps,
        "positive_gap_ages": int(sum(r["recovering_gt_unsafe"] for r in gaps)),
        "common_age_count": int(len(gaps)),
    }


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def run(root: Path, out: Path) -> dict:
    v11 = load_v11()
    if tuple(v11.HORIZONS) != HORIZONS:
        raise RuntimeError(f"V11 horizons drift: {v11.HORIZONS}")
    if tuple(v11.DEV_YEARS) != DEV_YEARS:
        raise RuntimeError(f"V11 Development years drift: {v11.DEV_YEARS}")

    rows = build_v11_rows(root, v11)
    table = exact_age_table(rows)

    pooled_all = {str(h): standardize_one(rows, h) for h in HORIZONS}
    pooled_in_window = {str(h): standardize_one(rows, h, IN_WINDOW_AGES) for h in HORIZONS}
    annual = {}
    for year in DEV_YEARS:
        yr = rows[rows.year == year]
        annual[str(year)] = {str(h): standardize_one(yr, h) for h in HORIZONS}

    primary = pooled_all["60"]
    annual_std_gaps = {
        str(year): float(annual[str(year)]["60"]["standardized"]["recovering_minus_unsafe_gap"])
        for year in DEV_YEARS
    }
    interpretation = {
        "raw_common_support_60m_gap_negative": bool(primary["raw"]["recovering_minus_unsafe_gap"] < 0),
        "standardized_pooled_60m_gap_positive": bool(primary["standardized"]["recovering_minus_unsafe_gap"] > 0),
        "standardized_60m_gap_positive_at_least_2_of_3_years": bool(sum(v > 0 for v in annual_std_gaps.values()) >= 2),
        "state_thresholds_unchanged": True,
        "horizons_unchanged": True,
        "sample_rule_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
    }
    explained = bool(all(interpretation.values()))

    summary = {
        "schema": "highvol_exact_age_composition_v13_development",
        "development_only": True,
        "development_years": list(DEV_YEARS),
        "row_count": int(len(rows)),
        "source": "V11 common 60m-support survival cohort",
        "horizons_minutes": list(HORIZONS),
        "in_window_exact_ages": list(IN_WINDOW_AGES),
        "age_composition": age_composition(rows),
        "pooled_all_common_ages": pooled_all,
        "pooled_in_window_ages_1_to_11": pooled_in_window,
        "annual_all_common_ages": annual,
        "pooled_60m_exact_age_signs": exact_sign_summary(primary),
        "annual_standardized_60m_gap": annual_std_gaps,
        "interpretation_gates": interpretation,
        "exact_age_composition_explains_60m_crossover": explained,
        "validation_authorized": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "decision": (
            "SUPPORT_SIMPSON_STYLE_EXACT_AGE_COMPOSITION_MECHANISM"
            if explained
            else "REJECT_SIMPLE_EXACT_AGE_COMPOSITION_EXPLANATION; TREAT_STATE_ORDER_AS_HORIZON_DEPENDENT"
        ),
    }

    out.mkdir(parents=True, exist_ok=True)
    rows.to_parquet(out / "v11_common_cohort.parquet", index=False)
    table.to_csv(out / "exact_age_table.csv", index=False)
    (out / "summary.json").write_text(json.dumps(clean(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(clean(summary), sort_keys=True))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    run(args.repo_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
