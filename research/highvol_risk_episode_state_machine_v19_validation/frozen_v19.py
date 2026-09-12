from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
REF_YEARS = (2020, 2021, 2022, 2023)
DEV_YEARS = (2021, 2022, 2023)
RISK_STATES = ("UNSAFE", "RECOVERING")
PRIMARY_LEAD_SECONDS = 15
HORIZONS = (15, 30, 60)

EXPECTED_V9_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
EXPECTED_V18_BLOB = "62c207badff1c3e37cbb1a8e17ef89feeea611d8"
EXPECTED_V17_BLOB = "397d80037806ba11cadf7f77717d36d55fbafc91"
EXPECTED_V16_SURFACE_BLOB = "1f88966cf5dd3fb102f0d75746d5d00434555647"

HERE = Path(__file__).resolve().parent
FROZEN_V9 = HERE / "frozen_v9.py"
FROZEN_V18 = HERE / "frozen_v18.py"
FROZEN_V17 = HERE / "frozen_v17.py"
FROZEN_V16_SURFACE = HERE / "frozen_v16_surface.json"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_frozen_authority():
    expected = {
        FROZEN_V9: EXPECTED_V9_BLOB,
        FROZEN_V18: EXPECTED_V18_BLOB,
        FROZEN_V17: EXPECTED_V17_BLOB,
        FROZEN_V16_SURFACE: EXPECTED_V16_SURFACE_BLOB,
    }
    got = {p.name: git_blob_sha(p) for p in expected}
    for path, sha in expected.items():
        if got[path.name] != sha:
            raise RuntimeError(f"frozen authority drift {path.name}: {got[path.name]} != {sha}")

    v9 = load_module(FROZEN_V9, "v19_frozen_v9")
    v9.SYMBOLS = SYMBOLS
    v9.REF_YEARS = REF_YEARS
    v9.DEV_YEARS = DEV_YEARS
    constants = (v9.RV_WINDOW, v9.BG_WINDOW, v9.HIGHVOL_RATIO, v9.RECOVERY_NORMAL_RATIO, v9.SHOCK_SIGMA)
    if constants != (12, 48, 1.5, 1.1, 3.0):
        raise RuntimeError(f"V9 constants drift: {constants}")

    surface = json.loads(FROZEN_V16_SURFACE.read_text())
    if surface.get("schema") != "highvol_horizon_adaptive_surface_v16_frozen_v1":
        raise RuntimeError("unexpected V16 frozen surface schema")
    if surface.get("adaptive_surface_supported") is not True:
        raise RuntimeError("V16 frozen surface not supported")

    adaptive = {}
    for r in surface["adaptive_surface"]:
        adaptive[(str(r["current_state"]), str(r["age_bucket"]))] = {
            h: float(r[f"p_{h}m"]) for h in HORIZONS
        }
    age_only = {}
    for r in surface["age_only_comparator"]:
        age_only[str(r["age_bucket"])] = {h: float(r[f"p_{h}m"]) for h in HORIZONS}
    if len(adaptive) != 8 or len(age_only) != 4:
        raise RuntimeError("V16 prediction map cardinality drift")
    for (state, bucket), p in adaptive.items():
        if not (p[15] <= p[30] <= p[60]):
            raise RuntimeError(f"V16 probability monotonicity drift: {state}/{bucket}")
        if abs(p[60] - age_only[bucket][60]) > 1e-15:
            raise RuntimeError(f"V16 60m anchor drift: {state}/{bucket}")
    return v9, adaptive, age_only, got


def is_risk(state) -> bool:
    return str(state) in RISK_STATES


def reference_e15_state(prev_state: str, final_state: str) -> str:
    if final_state in RISK_STATES:
        return final_state
    if prev_state in RISK_STATES:
        return prev_state
    return "NORMAL"


def machine_e15_state(prev_state: str, partial_state: str | None) -> str | None:
    if partial_state is None:
        return None
    if partial_state in RISK_STATES:
        return partial_state
    if prev_state in RISK_STATES:
        return prev_state
    return "NORMAL"


def transition_class(prev_state: str, final_state: str) -> str:
    if prev_state == "NORMAL" and final_state == "UNSAFE":
        return "SWITCH_ON"
    if prev_state == "RECOVERING" and final_state == "UNSAFE":
        return "REESCALATE"
    if prev_state == "UNSAFE" and final_state == "RECOVERING":
        return "UNSAFE_TO_RECOVERING"
    if prev_state == "UNSAFE" and final_state == "NORMAL":
        return "EXIT_FROM_UNSAFE"
    if prev_state == "RECOVERING" and final_state == "NORMAL":
        return "EXIT_FROM_RECOVERING"
    if prev_state == final_state:
        return f"HOLD_{final_state}"
    return f"{prev_state}_TO_{final_state}"


def build_symbol_rows(root: Path, v9, symbol: str) -> tuple[pd.DataFrame, dict]:
    ref = v9.load_reference(root, symbol).copy()
    ref["bar_pos"] = ref.groupby("trading_day", sort=False).cumcount().astype(int)
    windows = v9.prior_windows(ref)

    base = ref[ref.year.isin(DEV_YEARS)].copy()
    boundary = {
        "development_rows_before_reference_guard": int(len(base)),
        "missing_prior_window": int(sum(int(i) not in windows for i in base.index)),
        "missing_prev_close": int(base.prev_close.isna().sum()),
        "missing_bg_vol48": int(base.bg_vol48.isna().sum()),
    }
    ok = pd.Series([int(i) in windows for i in base.index], index=base.index)
    ok &= base.prev_close.notna() & base.bg_vol48.notna()
    base = base[ok].copy()
    base["global_idx"] = base.index.astype(int)

    # Causal age since the most recent finalized shock strictly before the current bar.
    prior_age = {}
    for _, day in ref.groupby("trading_day", sort=False):
        last_shock_pos = None
        for idx, r in day.iterrows():
            pos = int(r.bar_pos)
            prior_age[int(idx)] = None if last_shock_pos is None else int(pos - last_shock_pos)
            if bool(r.shock) if pd.notna(r.shock) else False:
                last_shock_pos = pos

    obs_day = {}
    for year in DEV_YEARS:
        sec = v9.load_3s(root, symbol, year)
        for day, g in sec.groupby("trading_day", sort=False):
            obs_day[(year, str(day))] = g.reset_index(drop=True)

    rows = []
    for idx, rr in base.iterrows():
        year = int(rr.year)
        day = str(rr.trading_day)
        bar_end = pd.Timestamp(rr.bar_end)
        target = bar_end - pd.Timedelta(seconds=PRIMARY_LEAD_SECONDS)
        start = bar_end - pd.Timedelta(minutes=5)
        sec = obs_day.get((year, day), pd.DataFrame())
        sel = v9.select_checkpoint(sec, start, target)

        prev_state = str(rr.prev_state)
        final_state = str(rr.risk_state)
        ref_state = reference_e15_state(prev_state, final_state)
        row = {
            "candidate_id": f"{symbol}|{day}|{bar_end.isoformat()}",
            "symbol": symbol,
            "year": year,
            "trading_day": day,
            "global_idx": int(idx),
            "bar_pos": int(rr.bar_pos),
            "bar_end": bar_end,
            "prev_state": prev_state,
            "final_state": final_state,
            "final_shock": bool(rr.shock) if pd.notna(rr.shock) else False,
            "reference_e15_state": ref_state,
            "reference_risk": is_risk(ref_state),
            "transition_class": transition_class(prev_state, final_state),
            "prior_final_shock_age_bars": prior_age.get(int(idx)),
            "checkpoint_available": sel is not None,
        }
        if sel is None:
            row.update({
                "selected_observation_time": pd.NaT,
                "staleness_seconds": np.nan,
                "partial_state": None,
                "partial_shock": False,
                "partial_vol_ratio": np.nan,
                "partial_shock_intensity": np.nan,
                "raw_partial_risk": False,
                "machine_state": None,
                "machine_risk": False,
                "machine_reason": "missing_3s_checkpoint",
            })
            rows.append(row)
            continue

        price, obs_time = sel
        pret = float(np.log(price) - np.log(float(rr.prev_close)))
        prv = float(np.std(np.concatenate([windows[int(idx)], [pret]]), ddof=0))
        ratio = prv / float(rr.bg_vol48)
        intensity = abs(pret) / float(rr.bg_vol48)
        pshock = bool(intensity >= v9.SHOCK_SIGMA)
        pstate = str(v9.transition(prev_state, ratio, pshock))
        mstate = machine_e15_state(prev_state, pstate)
        reason = "partial_risk" if pstate in RISK_STATES else ("close_confirmed_exit_latch" if prev_state in RISK_STATES else "normal")
        row.update({
            "selected_observation_time": obs_time,
            "staleness_seconds": float((target - obs_time).total_seconds()),
            "partial_state": pstate,
            "partial_shock": pshock,
            "partial_vol_ratio": ratio,
            "partial_shock_intensity": intensity,
            "raw_partial_risk": is_risk(pstate),
            "machine_state": mstate,
            "machine_risk": is_risk(mstate),
            "machine_reason": reason,
        })
        rows.append(row)

    return pd.DataFrame(rows), boundary


def attach_recovery_probabilities(detail: pd.DataFrame, v9, adaptive: dict, age_only: dict) -> pd.DataFrame:
    z = detail.copy()
    for h in HORIZONS:
        z[f"realtime_p_{h}m"] = np.nan
    z["age_bucket"] = None
    z["probability_reason"] = "unavailable"
    z["anchor_p_60m"] = np.nan

    for i, r in z.iterrows():
        if not bool(r.checkpoint_available):
            z.at[i, "probability_reason"] = "missing_3s_checkpoint"
            continue
        if bool(r.partial_shock):
            z.at[i, "probability_reason"] = "fresh_partial_shock"
            continue
        pstate = str(r.partial_state)
        if pstate not in RISK_STATES:
            z.at[i, "probability_reason"] = "provisional_normal"
            continue
        age = r.prior_final_shock_age_bars
        if pd.isna(age) or int(age) <= 0:
            z.at[i, "probability_reason"] = "no_prior_finalized_shock"
            continue
        bucket = str(v9.age_bucket(int(age)))
        z.at[i, "age_bucket"] = bucket
        z.at[i, "realtime_p_15m"] = adaptive[(pstate, bucket)][15]
        z.at[i, "realtime_p_30m"] = adaptive[(pstate, bucket)][30]
        z.at[i, "realtime_p_60m"] = age_only[bucket][60]
        z.at[i, "anchor_p_60m"] = age_only[bucket][60]
        z.at[i, "probability_reason"] = "scored"
    return z


def add_episode_ids(detail: pd.DataFrame, risk_col: str, state_col: str, out_col: str, prefix: str) -> pd.DataFrame:
    z = detail.copy()
    z[out_col] = None
    for (symbol, day), g in z.groupby(["symbol", "trading_day"], sort=False):
        g = g.sort_values("bar_pos", kind="stable")
        ep = 0
        active = False
        prev_pos = None
        current_id = None
        for idx, r in g.iterrows():
            risk = bool(r[risk_col]) and pd.notna(r[state_col])
            contiguous = prev_pos is not None and int(r.bar_pos) == int(prev_pos) + 1
            if risk and (not active or not contiguous):
                ep += 1
                current_id = f"{prefix}|{symbol}|{day}|{ep}"
            if risk:
                z.at[idx, out_col] = current_id
                active = True
            else:
                active = False
                current_id = None
            prev_pos = int(r.bar_pos)
    return z


def classification_summary(x: pd.DataFrame) -> dict:
    available = x.checkpoint_available.astype(bool)
    z = x[available].copy()
    y = z.reference_risk.astype(bool)
    p = z.machine_risk.astype(bool)
    raw = z.raw_partial_risk.astype(bool)

    tp = int((y & p).sum())
    fp = int((~y & p).sum())
    fn = int((y & ~p).sum())
    tn = int((~y & ~p).sum())
    rtp = int((y & raw).sum())
    rfp = int((~y & raw).sum())
    rfn = int((y & ~raw).sum())
    rtn = int((~y & ~raw).sum())

    def safe_div(a, b):
        return float(a / b) if b else None

    return {
        "candidate_rows": int(len(x)),
        "checkpoint_available_rows": int(available.sum()),
        "checkpoint_coverage": safe_div(int(available.sum()), len(x)),
        "reference_risk_rows": int(y.sum()),
        "machine_risk_rows": int(p.sum()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "risk_precision": safe_div(tp, tp + fp),
        "risk_recall": safe_div(tp, tp + fn),
        "false_positive_rate": safe_div(fp, fp + tn),
        "exact_three_state_agreement": float(z.machine_state.eq(z.reference_e15_state).mean()) if len(z) else None,
        "raw_partial": {
            "tp": rtp, "fp": rfp, "fn": rfn, "tn": rtn,
            "risk_precision": safe_div(rtp, rtp + rfp),
            "risk_recall": safe_div(rtp, rtp + rfn),
            "false_positive_rate": safe_div(rfp, rfp + rtn),
            "exact_three_state_agreement": float(z.partial_state.eq(z.reference_e15_state).mean()) if len(z) else None,
        },
    }


def transition_summary(x: pd.DataFrame) -> dict:
    z = x[x.checkpoint_available].copy()

    def recall_for(label: str, wanted: str) -> dict:
        q = z[z.transition_class.eq(label)]
        hit = int(q.machine_state.eq(wanted).sum())
        return {"rows": int(len(q)), "hits": hit, "recall": float(hit / len(q)) if len(q) else None}

    exits = z[z.transition_class.isin(["EXIT_FROM_UNSAFE", "EXIT_FROM_RECOVERING"])]
    premature = int(exits.machine_state.eq("NORMAL").sum())
    raw_premature = int(exits.partial_state.eq("NORMAL").sum())
    return {
        "switch_on": recall_for("SWITCH_ON", "UNSAFE"),
        "re_escalation": recall_for("REESCALATE", "UNSAFE"),
        "unsafe_to_recovering": recall_for("UNSAFE_TO_RECOVERING", "RECOVERING"),
        "close_confirmed_exit": {
            "rows": int(len(exits)),
            "premature_normal_rows": premature,
            "premature_normal_rate": float(premature / len(exits)) if len(exits) else None,
            "raw_partial_normal_rows": raw_premature,
            "raw_partial_normal_rate": float(raw_premature / len(exits)) if len(exits) else None,
        },
    }


def episode_tables(detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    ref_rows = []
    for ep_id, g in detail.dropna(subset=["reference_episode_id"]).groupby("reference_episode_id", sort=False):
        g = g.sort_values("bar_pos", kind="stable")
        first = g.iloc[0]
        machine_ids = sorted(set(str(v) for v in g.machine_episode_id.dropna().tolist()))
        machine_hits = g[g.machine_risk & g.checkpoint_available]
        left_censored = bool(int(first.bar_pos) > 0 and str(first.prev_state) in RISK_STATES)
        right_censored = bool(int(g.iloc[-1].bar_pos) == 47 and bool(g.iloc[-1].reference_risk))
        ref_rows.append({
            "reference_episode_id": ep_id,
            "symbol": str(first.symbol),
            "year": int(first.year),
            "trading_day": str(first.trading_day),
            "start_bar_pos": int(first.bar_pos),
            "end_bar_pos": int(g.iloc[-1].bar_pos),
            "checkpoint_count": int(len(g)),
            "left_censored": left_censored,
            "right_censored": right_censored,
            "captured": bool(len(machine_ids) > 0),
            "overlapping_machine_episode_count": int(len(machine_ids)),
            "fragmented": bool(len(machine_ids) > 1),
            "same_checkpoint_onset": bool(first.checkpoint_available and first.machine_risk),
            "onset_lag_checkpoints": int(machine_hits.index.get_indexer([machine_hits.index[0]])[0]) if False else None,
        })
    ref_ep = pd.DataFrame(ref_rows)

    # Replace onset lag with ordinal within each reference episode.
    if len(ref_ep):
        lags = {}
        for ep_id, g in detail.dropna(subset=["reference_episode_id"]).groupby("reference_episode_id", sort=False):
            g = g.sort_values("bar_pos", kind="stable").reset_index(drop=True)
            hits = g.index[g.machine_risk & g.checkpoint_available]
            lags[ep_id] = int(hits[0]) if len(hits) else None
        ref_ep["onset_lag_checkpoints"] = ref_ep.reference_episode_id.map(lags)

    mach_rows = []
    for ep_id, g in detail.dropna(subset=["machine_episode_id"]).groupby("machine_episode_id", sort=False):
        g = g.sort_values("bar_pos", kind="stable")
        first = g.iloc[0]
        ref_ids = sorted(set(str(v) for v in g.reference_episode_id.dropna().tolist()))
        mach_rows.append({
            "machine_episode_id": ep_id,
            "symbol": str(first.symbol),
            "year": int(first.year),
            "trading_day": str(first.trading_day),
            "start_bar_pos": int(first.bar_pos),
            "end_bar_pos": int(g.iloc[-1].bar_pos),
            "checkpoint_count": int(len(g)),
            "overlapping_reference_episode_count": int(len(ref_ids)),
            "false_episode": bool(len(ref_ids) == 0),
        })
    mach_ep = pd.DataFrame(mach_rows)

    def summarize_ref(q: pd.DataFrame) -> dict:
        if q.empty:
            return {
                "reference_episodes": 0, "captured": 0, "capture_rate": None,
                "fragmented": 0, "fragmentation_rate": None,
                "uncensored_reference_episodes": 0, "same_checkpoint_onset": 0,
                "same_checkpoint_onset_rate": None,
            }
        u = q[~q.left_censored]
        return {
            "reference_episodes": int(len(q)),
            "captured": int(q.captured.sum()),
            "capture_rate": float(q.captured.mean()),
            "fragmented": int(q.fragmented.sum()),
            "fragmentation_rate": float(q.fragmented.mean()),
            "uncensored_reference_episodes": int(len(u)),
            "same_checkpoint_onset": int(u.same_checkpoint_onset.sum()),
            "same_checkpoint_onset_rate": float(u.same_checkpoint_onset.mean()) if len(u) else None,
            "onset_lag_p50": float(pd.to_numeric(u.onset_lag_checkpoints, errors="coerce").dropna().median()) if pd.to_numeric(u.onset_lag_checkpoints, errors="coerce").notna().any() else None,
            "onset_lag_max": int(pd.to_numeric(u.onset_lag_checkpoints, errors="coerce").dropna().max()) if pd.to_numeric(u.onset_lag_checkpoints, errors="coerce").notna().any() else None,
        }

    def summarize_mach(q: pd.DataFrame) -> dict:
        if q.empty:
            return {"machine_episodes": 0, "false_episodes": 0, "false_episode_rate": None}
        return {
            "machine_episodes": int(len(q)),
            "false_episodes": int(q.false_episode.sum()),
            "false_episode_rate": float(q.false_episode.mean()),
        }

    pooled = {**summarize_ref(ref_ep), **summarize_mach(mach_ep)}
    yearly = {}
    for y in DEV_YEARS:
        yearly[str(y)] = {
            **summarize_ref(ref_ep[ref_ep.year.eq(y)] if len(ref_ep) else ref_ep),
            **summarize_mach(mach_ep[mach_ep.year.eq(y)] if len(mach_ep) else mach_ep),
        }
    return ref_ep, mach_ep, {"pooled": pooled, "yearly": yearly}


def probability_integrity(detail: pd.DataFrame) -> dict:
    z = detail[detail.probability_reason.eq("scored")].copy()
    if z.empty:
        return {
            "scored_rows": 0,
            "coverage_of_machine_risk_rows": 0.0,
            "monotone_all_rows": False,
            "max_abs_60m_anchor_diff": None,
            "sixty_minute_anchor_exact": False,
            "reason_counts": detail.probability_reason.value_counts().to_dict(),
        }
    mono = (z.realtime_p_15m <= z.realtime_p_30m) & (z.realtime_p_30m <= z.realtime_p_60m)
    diff = np.abs(z.realtime_p_60m.to_numpy(float) - z.anchor_p_60m.to_numpy(float))
    machine_risk_rows = int((detail.machine_risk & detail.checkpoint_available).sum())
    return {
        "scored_rows": int(len(z)),
        "coverage_of_machine_risk_rows": float(len(z) / machine_risk_rows) if machine_risk_rows else None,
        "monotone_rows": int(mono.sum()),
        "monotone_all_rows": bool(mono.all()),
        "max_abs_60m_anchor_diff": float(diff.max()),
        "sixty_minute_anchor_exact": bool(diff.max() <= 1e-15),
        "reason_counts": {str(k): int(v) for k, v in detail.probability_reason.value_counts().to_dict().items()},
    }


def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (np.floating, float)):
        x = float(v)
        return x if np.isfinite(x) else None
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return v


def run(root: Path, out: Path) -> dict:
    v9, adaptive, age_only, blob_receipt = load_frozen_authority()

    pieces = []
    boundary = {}
    for symbol in SYMBOLS:
        x, b = build_symbol_rows(root, v9, symbol)
        pieces.append(x)
        boundary[symbol] = b
    detail = pd.concat(pieces, ignore_index=True)
    if detail.candidate_id.duplicated().any():
        raise RuntimeError("candidate_id collision")

    detail = attach_recovery_probabilities(detail, v9, adaptive, age_only)
    detail = add_episode_ids(detail, "reference_risk", "reference_e15_state", "reference_episode_id", "REF")
    detail = add_episode_ids(detail, "machine_risk", "machine_state", "machine_episode_id", "MACH")

    pooled = classification_summary(detail)
    yearly = {str(y): classification_summary(detail[detail.year.eq(y)]) for y in DEV_YEARS}
    by_symbol = {s: classification_summary(detail[detail.symbol.eq(s)]) for s in SYMBOLS}
    transitions = transition_summary(detail)
    ref_ep, mach_ep, episodes = episode_tables(detail)
    prob = probability_integrity(detail)

    ep_pool = episodes["pooled"]
    acceptance = {
        "pooled_evaluable_checkpoints_ge_30000": int(len(detail)) >= 30000,
        "pooled_reference_episodes_ge_300": ep_pool["reference_episodes"] >= 300,
        "each_year_reference_episodes_ge_50": all(episodes["yearly"][str(y)]["reference_episodes"] >= 50 for y in DEV_YEARS),
        "pooled_checkpoint_coverage_ge_098": pooled["checkpoint_coverage"] is not None and pooled["checkpoint_coverage"] >= 0.98,
        "each_year_checkpoint_coverage_ge_095": all(yearly[str(y)]["checkpoint_coverage"] is not None and yearly[str(y)]["checkpoint_coverage"] >= 0.95 for y in DEV_YEARS),
        "pooled_risk_precision_ge_098": pooled["risk_precision"] is not None and pooled["risk_precision"] >= 0.98,
        "pooled_risk_recall_ge_098": pooled["risk_recall"] is not None and pooled["risk_recall"] >= 0.98,
        "pooled_false_positive_rate_le_0005": pooled["false_positive_rate"] is not None and pooled["false_positive_rate"] <= 0.005,
        "each_year_risk_precision_ge_095": all(yearly[str(y)]["risk_precision"] is not None and yearly[str(y)]["risk_precision"] >= 0.95 for y in DEV_YEARS),
        "each_year_risk_recall_ge_095": all(yearly[str(y)]["risk_recall"] is not None and yearly[str(y)]["risk_recall"] >= 0.95 for y in DEV_YEARS),
        "each_year_false_positive_rate_le_001": all(yearly[str(y)]["false_positive_rate"] is not None and yearly[str(y)]["false_positive_rate"] <= 0.01 for y in DEV_YEARS),
        "pooled_exact_three_state_agreement_ge_090": pooled["exact_three_state_agreement"] is not None and pooled["exact_three_state_agreement"] >= 0.90,
        "reference_episode_capture_rate_ge_098": ep_pool["capture_rate"] is not None and ep_pool["capture_rate"] >= 0.98,
        "false_machine_episode_rate_le_010": ep_pool["false_episode_rate"] is not None and ep_pool["false_episode_rate"] <= 0.10,
        "reference_episode_fragmentation_rate_le_005": ep_pool["fragmentation_rate"] is not None and ep_pool["fragmentation_rate"] <= 0.05,
        "uncensored_same_checkpoint_onset_rate_ge_080": ep_pool["same_checkpoint_onset_rate"] is not None and ep_pool["same_checkpoint_onset_rate"] >= 0.80,
        "each_year_uncensored_same_checkpoint_onset_rate_ge_070": all(episodes["yearly"][str(y)]["same_checkpoint_onset_rate"] is not None and episodes["yearly"][str(y)]["same_checkpoint_onset_rate"] >= 0.70 for y in DEV_YEARS),
        "switch_on_same_checkpoint_unsafe_recall_ge_080": transitions["switch_on"]["recall"] is not None and transitions["switch_on"]["recall"] >= 0.80,
        "re_escalation_same_checkpoint_unsafe_recall_ge_080": transitions["re_escalation"]["recall"] is not None and transitions["re_escalation"]["recall"] >= 0.80,
        "unsafe_to_recovering_same_checkpoint_recall_ge_080": transitions["unsafe_to_recovering"]["recall"] is not None and transitions["unsafe_to_recovering"]["recall"] >= 0.80,
        "close_confirmed_premature_normal_rate_le_002": transitions["close_confirmed_exit"]["premature_normal_rate"] is not None and transitions["close_confirmed_exit"]["premature_normal_rate"] <= 0.02,
        "recovery_probabilities_rowwise_monotone": prob["monotone_all_rows"],
        "sixty_minute_exact_frozen_age_anchor": prob["sixty_minute_anchor_exact"],
        "frozen_v9_blob_unchanged": blob_receipt["frozen_v9.py"] == EXPECTED_V9_BLOB,
        "frozen_v18_blob_unchanged": blob_receipt["frozen_v18.py"] == EXPECTED_V18_BLOB,
        "frozen_v17_blob_unchanged": blob_receipt["frozen_v17.py"] == EXPECTED_V17_BLOB,
        "frozen_v16_surface_blob_unchanged": blob_receipt["frozen_v16_surface.json"] == EXPECTED_V16_SURFACE_BLOB,
        "threshold_search_performed_false": True,
        "lead_time_search_performed_false": True,
        "persistence_length_search_performed_false": True,
        "probability_fit_performed_false": True,
        "projection_change_performed_false": True,
        "posthoc_subgroup_selection_false": True,
        "validation_queried_false": True,
        "post_2023_3s_queried_false": True,
        "queried_2026_3s_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    supported = bool(all(acceptance.values()))

    summary = {
        "schema": "highvol_risk_episode_state_machine_v19_development_v1",
        "development_only": True,
        "development_years": list(DEV_YEARS),
        "symbols": list(SYMBOLS),
        "checkpoint_seconds_before_5m_close": PRIMARY_LEAD_SECONDS,
        "machine_rule": "partial risk state immediately; provisional NORMAL while previous finalized state is risk is latched until bar close",
        "reference_rule": "current final risk state, else previous finalized risk state until close, else NORMAL",
        "frozen_blob_receipt": blob_receipt,
        "boundary_exclusions": boundary,
        "candidate_rows": int(len(detail)),
        "pooled": pooled,
        "yearly": yearly,
        "by_symbol": by_symbol,
        "transitions": transitions,
        "episodes": episodes,
        "recovery_probability_integrity": prob,
        "threshold_search_performed": False,
        "lead_time_search_performed": False,
        "persistence_length_search_performed": False,
        "probability_fit_performed": False,
        "projection_change_performed": False,
        "posthoc_subgroup_selection": False,
        "validation_queried": False,
        "queried_3s_years": list(DEV_YEARS),
        "queried_post_2023_3s": False,
        "queried_2026_3s": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "trading_rule_created": False,
        "production_authority": False,
        "acceptance": acceptance,
        "development_supported": supported,
        "validation_eligible_but_not_authorized": supported,
        "decision": "FREEZE_V19_E15S_CLOSE_CONFIRMED_RISK_EPISODE_MACHINE_AND_STOP_BEFORE_VALIDATION" if supported else "V19_DEVELOPMENT_REJECTED_OR_DIAGNOSTIC_ONLY",
    }

    out.mkdir(parents=True, exist_ok=True)
    detail.to_parquet(out / "checkpoint_detail.parquet", index=False)
    ref_ep.to_parquet(out / "reference_episodes.parquet", index=False)
    mach_ep.to_parquet(out / "machine_episodes.parquet", index=False)
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
