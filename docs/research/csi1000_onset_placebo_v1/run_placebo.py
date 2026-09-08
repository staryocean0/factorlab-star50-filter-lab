from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOL = "000852.SH"
DEV_START, DEV_END = "2021-01-01", "2023-12-31"
VAL_START, VAL_END = "2024-01-01", "2026-08-21"
HOLD = 3
TAIL2_MIN = 0.60
TAIL1_CAP = 0.60
EXCLUSION_MIN = 10
FEATURES = ("slow30_net_bp", "net5_bp", "tail2_share", "tail1_share", "recovery_ratio")
BOOT_DRAWS = 10_000
BOOT_SEED = 20260908


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_structural_rows(minute: pd.DataFrame) -> pd.DataFrame:
    """Build past-only structural covariates plus a fixed 3m future outcome.

    The row contract mirrors the frozen CSI1000 candidate, but includes both
    fresh HighVol onsets and already-ongoing HighVol minutes.
    """
    rows: list[dict] = []
    for session, z0 in minute.groupby("session", sort=False):
        z = z0.sort_values("minute").reset_index(drop=True)
        state = z.route_state.to_numpy(object)
        close = z.close.to_numpy(float)
        op = z.open.to_numpy(float)
        valid = z.valid.to_numpy(bool)
        ratio = pd.to_numeric(z.recovery_ratio, errors="coerce").to_numpy(float)
        r = np.full(len(z), np.nan, float)
        for i in range(1, len(z)):
            if (
                valid[i]
                and valid[i - 1]
                and np.isfinite(close[i])
                and np.isfinite(close[i - 1])
                and close[i] > 0
                and close[i - 1] > 0
            ):
                r[i] = np.log(close[i] / close[i - 1]) * 1e4

        for i in range(35, len(z)):
            if state[i] != "HighVol":
                continue
            recent = r[i - 4 : i + 1]
            slow = r[i - 34 : i - 4]
            if len(recent) != 5 or len(slow) != 30:
                continue
            if not np.isfinite(recent).all() or not np.isfinite(slow).all():
                continue
            net5 = float(recent.sum())
            slow30 = float(slow.sum())
            tv5 = float(np.abs(recent).sum())
            if net5 <= 0 or slow30 <= 0 or tv5 <= 0:
                continue
            tail1 = abs(float(recent[-1])) / tv5
            tail2 = float(np.abs(recent[-2:]).sum()) / tv5
            if tail2 < TAIL2_MIN or tail1 >= TAIL1_CAP:
                continue
            if not np.isfinite(ratio[i]):
                continue

            entry = i + 1
            exit_ = entry + HOLD
            if exit_ >= len(z):
                continue
            if not valid[entry : exit_ + 1].all():
                continue
            if not (
                np.isfinite(op[entry])
                and np.isfinite(op[exit_])
                and op[entry] > 0
                and op[exit_] > 0
            ):
                continue
            gross = float(np.log(op[exit_] / op[entry]) * 1e4)
            prev = state[i - 1]
            onset = prev == "NormalVol"
            ongoing = prev == "HighVol"
            if not (onset or ongoing):
                continue
            half = int(str(session).rsplit("/", 1)[-1])
            rows.append(
                {
                    "symbol": z.symbol.iloc[0],
                    "year": int(z.year.iloc[0]),
                    "trading_day": str(z.trading_day.iloc[0])[:10],
                    "session": session,
                    "half": half,
                    "minute": int(z.minute.iloc[i]),
                    "clock_bucket15": int((int(z.minute.iloc[i]) - 1) // 15),
                    "onset_row": i,
                    "is_onset": bool(onset),
                    "is_ongoing_highvol": bool(ongoing),
                    "slow30_net_bp": slow30,
                    "net5_bp": net5,
                    "tail2_share": tail2,
                    "tail1_share": tail1,
                    "recovery_ratio": float(ratio[i]),
                    "entry_minute": int(z.minute.iloc[entry]),
                    "exit_minute": int(z.minute.iloc[exit_]),
                    "gross_3m_bp": gross,
                }
            )
    return pd.DataFrame(rows)


def select_nonoverlap_candidates(structural: pd.DataFrame) -> pd.DataFrame:
    z = structural[structural.is_onset].sort_values(
        ["trading_day", "session", "onset_row"], kind="stable"
    )
    rows = []
    for session, g in z.groupby("session", sort=False):
        next_allowed = -1
        for r in g.itertuples(index=False):
            i = int(r.onset_row)
            if i < next_allowed:
                continue
            rows.append(r._asdict())
            next_allowed = i + 1 + HOLD
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values(["trading_day", "session", "onset_row"], kind="stable").reset_index(drop=True)
        out["candidate_id"] = np.arange(len(out), dtype=int)
    return out


def exclude_near_candidates(controls: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    z = controls.copy()
    if not len(z) or not len(candidates):
        return z
    blocked: dict[str, list[int]] = {}
    for r in candidates.itertuples(index=False):
        blocked.setdefault(str(r.session), []).append(int(r.onset_row))
    keep = []
    for r in z.itertuples(index=False):
        onsets = blocked.get(str(r.session), [])
        keep.append(not any(abs(int(r.onset_row) - x) <= EXCLUSION_MIN for x in onsets))
    return z.loc[np.asarray(keep, dtype=bool)].reset_index(drop=True)


def role_mask(df: pd.DataFrame, role: str) -> pd.Series:
    day = df.trading_day.astype(str)
    if role == "Development":
        return day.between(DEV_START, DEV_END)
    if role == "Validation":
        return day.between(VAL_START, VAL_END)
    raise ValueError(role)


def _feature_standardizer(controls: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = controls.loc[:, FEATURES].astype(float).to_numpy()
    mu = np.nanmean(x, axis=0)
    sd = np.nanstd(x, axis=0, ddof=0)
    sd[~np.isfinite(sd) | (sd <= 1e-12)] = 1.0
    return mu, sd


def match_role(candidates: pd.DataFrame, controls: pd.DataFrame, role: str) -> pd.DataFrame:
    cand = candidates.loc[role_mask(candidates, role)].copy().reset_index(drop=True)
    ctrl = controls.loc[role_mask(controls, role)].copy().reset_index(drop=True)
    if not len(cand) or not len(ctrl):
        return pd.DataFrame()
    mu, sd = _feature_standardizer(ctrl)
    used: set[int] = set()
    pairs = []
    cand = cand.sort_values(["trading_day", "session", "onset_row"], kind="stable")
    for c in cand.itertuples(index=False):
        available = ctrl.loc[~ctrl.index.isin(used)]
        tier0 = available[
            (available.year == int(c.year))
            & (available.half == int(c.half))
            & (available.clock_bucket15 == int(c.clock_bucket15))
        ]
        if len(tier0):
            pool, tier = tier0, 0
        else:
            tier1 = available[(available.year == int(c.year)) & (available.half == int(c.half))]
            if not len(tier1):
                continue
            pool, tier = tier1, 1
        cv = np.asarray([getattr(c, f) for f in FEATURES], float)
        px = pool.loc[:, FEATURES].astype(float).to_numpy()
        dist = np.sqrt(np.sum(((px - cv) / sd) ** 2, axis=1))
        # Stable deterministic tie-break by dataframe index.
        order = np.lexsort((pool.index.to_numpy(), dist))
        jpos = int(order[0])
        j = int(pool.index[jpos])
        q = ctrl.loc[j]
        used.add(j)
        rec = {
            "role": role,
            "candidate_id": int(c.candidate_id),
            "candidate_day": str(c.trading_day),
            "candidate_year": int(c.year),
            "candidate_session": str(c.session),
            "candidate_minute": int(c.minute),
            "candidate_gross_3m_bp": float(c.gross_3m_bp),
            "control_day": str(q.trading_day),
            "control_year": int(q.year),
            "control_session": str(q.session),
            "control_minute": int(q.minute),
            "control_gross_3m_bp": float(q.gross_3m_bp),
            "match_tier": tier,
            "match_distance": float(dist[jpos]),
        }
        for f in FEATURES:
            rec[f"candidate_{f}"] = float(getattr(c, f))
            rec[f"control_{f}"] = float(q[f])
        rec["paired_diff_bp"] = rec["candidate_gross_3m_bp"] - rec["control_gross_3m_bp"]
        pairs.append(rec)
    return pd.DataFrame(pairs)


def pair_metrics(pairs: pd.DataFrame, candidates_total: int) -> dict:
    n = len(pairs)
    if not n:
        return {
            "candidate_count": int(candidates_total),
            "matched_count": 0,
            "coverage": 0.0,
            "candidate_mean_gross_bp": np.nan,
            "control_mean_gross_bp": np.nan,
            "mean_paired_diff_bp": np.nan,
            "median_paired_diff_bp": np.nan,
            "candidate_hit_rate": np.nan,
            "control_hit_rate": np.nan,
            "tier1_fraction": np.nan,
            "median_match_distance": np.nan,
        }
    return {
        "candidate_count": int(candidates_total),
        "matched_count": n,
        "coverage": float(n / candidates_total) if candidates_total else np.nan,
        "candidate_mean_gross_bp": float(pairs.candidate_gross_3m_bp.mean()),
        "control_mean_gross_bp": float(pairs.control_gross_3m_bp.mean()),
        "mean_paired_diff_bp": float(pairs.paired_diff_bp.mean()),
        "median_paired_diff_bp": float(pairs.paired_diff_bp.median()),
        "candidate_hit_rate": float((pairs.candidate_gross_3m_bp > 0).mean()),
        "control_hit_rate": float((pairs.control_gross_3m_bp > 0).mean()),
        "tier1_fraction": float((pairs.match_tier == 1).mean()),
        "median_match_distance": float(pairs.match_distance.median()),
    }


def day_block_bootstrap(pairs: pd.DataFrame, seed: int = BOOT_SEED, draws: int = BOOT_DRAWS) -> dict:
    if not len(pairs):
        return {"draws": 0, "q025": np.nan, "q50": np.nan, "q975": np.nan, "fraction_gt_zero": np.nan}
    groups = [g.paired_diff_bp.to_numpy(float) for _, g in pairs.groupby("candidate_day", sort=True)]
    rng = np.random.default_rng(seed)
    vals = np.empty(draws, float)
    m = len(groups)
    for b in range(draws):
        idx = rng.integers(0, m, size=m)
        vals[b] = float(np.concatenate([groups[i] for i in idx]).mean())
    q = np.quantile(vals, [0.025, 0.5, 0.975])
    return {
        "draws": int(draws),
        "candidate_days": int(m),
        "q025": float(q[0]),
        "q50": float(q[1]),
        "q975": float(q[2]),
        "fraction_gt_zero": float((vals > 0).mean()),
    }


def run(root: Path, out: Path) -> dict:
    reg = load_module(root / "docs/research/continuous_vol_regime_v1/run_continuous_vol_regime.py", "reg_placebo")
    orig = load_module(root / "docs/research/state_conditioned_frequency_v2/code/run_physical_scale_strategy.py", "orig_placebo")
    fg = load_module(root / "docs/research/state_conditioned_frequency_v2/code/fast_grid.py", "fg_placebo")

    native = orig.load_native(root, SYMBOL).copy()
    native["trading_day"] = native.trading_day.astype(str).str[:10]
    native = native[native.trading_day <= VAL_END]
    state = reg.build_continuous_state(native, SYMBOL)
    minute = fg.build_minute_grid(native, state.rename(columns={"vol_ratio": "recovery_ratio"}), SYMBOL).reset_index(drop=True)
    minute = minute[minute.trading_day.between(DEV_START, VAL_END)].reset_index(drop=True)

    structural = build_structural_rows(minute)
    candidates = select_nonoverlap_candidates(structural)
    controls = structural[structural.is_ongoing_highvol].copy().reset_index(drop=True)
    controls = exclude_near_candidates(controls, candidates)

    pairs_list = []
    summaries = []
    boots = []
    for role in ("Development", "Validation"):
        ctotal = int(role_mask(candidates, role).sum())
        p = match_role(candidates, controls, role)
        if len(p):
            pairs_list.append(p)
        rec = {"role": role, "year": "pooled", **pair_metrics(p, ctotal)}
        summaries.append(rec)
        boots.append({"role": role, **day_block_bootstrap(p, seed=BOOT_SEED + (0 if role == "Development" else 1))})
        for year in ((2021, 2022, 2023) if role == "Development" else (2024, 2025, 2026)):
            py = p[p.candidate_year == year] if len(p) else p
            cy = int(((candidates.year == year) & role_mask(candidates, role)).sum())
            summaries.append({"role": role, "year": year, **pair_metrics(py, cy)})

    pairs = pd.concat(pairs_list, ignore_index=True) if pairs_list else pd.DataFrame()
    out.mkdir(parents=True, exist_ok=True)
    structural.to_csv(out / "structural_rows.csv", index=False)
    candidates.to_csv(out / "selected_candidates.csv", index=False)
    controls.to_csv(out / "eligible_ongoing_controls.csv", index=False)
    pairs.to_csv(out / "matched_pairs.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "paired_summary.csv", index=False)
    pd.DataFrame(boots).to_csv(out / "bootstrap_summary.csv", index=False)

    counts = {
        "development_candidates": int(role_mask(candidates, "Development").sum()),
        "validation_candidates": int(role_mask(candidates, "Validation").sum()),
        "development_controls": int(role_mask(controls, "Development").sum()),
        "validation_controls": int(role_mask(controls, "Validation").sum()),
    }
    summary = {
        "schema": "csi1000_onset_placebo_v1",
        "candidate": {
            "symbol": SYMBOL,
            "slow_window": 30,
            "tail2_min": TAIL2_MIN,
            "tail1_cap": TAIL1_CAP,
            "hold_min": HOLD,
            "direction": "long",
        },
        "development": [DEV_START, DEV_END],
        "validation": [VAL_START, VAL_END],
        "blackbox_queried": False,
        "matching_uses_future_outcome": False,
        "counts": counts,
        "pooled_metrics": [r for r in summaries if r["year"] == "pooled"],
        "bootstrap": boots,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, default=str))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run(Path(args.repo_root).resolve(), Path(args.out))


if __name__ == "__main__":
    main()
