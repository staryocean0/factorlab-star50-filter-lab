from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
WARMUP_YEAR = 2020
DEV_YEARS = (2021, 2022, 2023)
ALL_YEARS = (2020, 2021, 2022, 2023)
OFFSETS = (1, 2, 3, 4)

RV_WINDOW = 12
BG_WINDOW = 48
HIGHVOL_RATIO = 1.50
RECOVERY_NORMAL_RATIO = 1.10
SHOCK_SIGMA = 3.00

POOLED_MIN_PRECISION = 0.90
POOLED_MIN_RECALL = 0.90
ANNUAL_MIN_PRECISION = 0.85
ANNUAL_MIN_RECALL = 0.85


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


def standardize(path: Path, symbol: str) -> pd.DataFrame:
    x = pd.read_parquet(path)
    if "trading_day" in x.columns:
        day = pd.to_datetime(x["trading_day"], errors="coerce").dt.strftime("%Y-%m-%d")
    else:
        tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
        if tcol not in x.columns:
            raise RuntimeError(f"{path}: missing trading_day/timestamp")
        day = wallclock(x[tcol]).dt.strftime("%Y-%m-%d")
    tcol = "timestamp" if "timestamp" in x.columns else "bar_end_shanghai"
    if tcol not in x.columns:
        raise RuntimeError(f"{path}: missing timestamp")
    ts = wallclock(x[tcol])
    if "close" not in x.columns:
        raise RuntimeError(f"{path}: missing close")
    out = pd.DataFrame({
        "symbol": symbol,
        "trading_day": day,
        "timestamp": ts,
        "close": pd.to_numeric(x["close"], errors="coerce"),
    }).dropna(subset=["trading_day", "timestamp", "close"])
    return out.sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True)


def load_native_5m(root: Path, symbol: str) -> pd.DataFrame:
    base = root / "data/market/5m" / symbol
    present = sorted(p.name for p in base.glob("*.parquet"))
    expected = [f"{y}.parquet" for y in ALL_YEARS]
    if present != expected:
        raise RuntimeError(f"5m physical boundary violation for {symbol}: {present}")
    return pd.concat([standardize(base / f"{y}.parquet", symbol) for y in ALL_YEARS], ignore_index=True)


def load_native_1m(root: Path, symbol: str) -> pd.DataFrame:
    base = root / "data/cross_index_risk_gate_v1/1m" / symbol
    present = sorted(p.name for p in base.glob("*.parquet"))
    expected = [f"{y}.parquet" for y in ALL_YEARS]
    if present != expected:
        raise RuntimeError(f"1m physical boundary violation for {symbol}: {present}")
    return pd.concat([standardize(base / f"{y}.parquet", symbol) for y in ALL_YEARS], ignore_index=True)


def build_partial_blocks(one: pd.DataFrame, native: pd.DataFrame, symbol: str) -> tuple[pd.DataFrame, dict]:
    rows = []
    eq_rows = []
    one_days = sorted(one.trading_day.unique())
    native_days = sorted(native.trading_day.unique())
    if one_days != native_days:
        raise RuntimeError(f"{symbol}: 1m/5m day support mismatch")

    for day in one_days:
        g = one[one.trading_day.eq(day)].sort_values("timestamp", kind="stable").reset_index(drop=True)
        n = native[native.trading_day.eq(day)].sort_values("timestamp", kind="stable").reset_index(drop=True)
        if len(g) != 240:
            raise RuntimeError(f"{symbol} {day}: expected 240 one-minute rows, got {len(g)}")
        if len(n) != 48:
            raise RuntimeError(f"{symbol} {day}: expected 48 five-minute rows, got {len(n)}")
        if g.timestamp.duplicated().any():
            raise RuntimeError(f"{symbol} {day}: duplicate 1m timestamp")

        block_no = 0
        synth_final = []
        for half_start in (0, 120):
            half = g.iloc[half_start:half_start + 120].reset_index(drop=True)
            for start in range(0, 120, 5):
                block = half.iloc[start:start + 5]
                if len(block) != 5:
                    raise RuntimeError(f"{symbol} {day}: incomplete five-minute block")
                closes = block.close.to_numpy(float)
                synth_final.append(float(closes[4]))
                rows.append({
                    "symbol": symbol,
                    "trading_day": str(day),
                    "block_no": block_no,
                    "partial_1": float(closes[0]),
                    "partial_2": float(closes[1]),
                    "partial_3": float(closes[2]),
                    "partial_4": float(closes[3]),
                    "final_1m_close": float(closes[4]),
                })
                block_no += 1

        native_close = n.close.to_numpy(float)
        synth_final = np.asarray(synth_final, float)
        diff = np.abs(native_close - synth_final)
        max_abs = float(diff.max()) if len(diff) else np.nan
        if not np.isfinite(max_abs) or max_abs > 1e-9:
            raise RuntimeError(f"{symbol} {day}: 1m->5m equivalence failed, max_abs={max_abs}")
        eq_rows.append({"symbol": symbol, "trading_day": str(day), "rows_5m": 48, "max_abs_close_diff": max_abs})

    blocks = pd.DataFrame(rows)
    eq = pd.DataFrame(eq_rows)
    summary = {
        "symbol": symbol,
        "days": int(len(eq)),
        "rows_5m": int(len(blocks)),
        "max_abs_close_diff": float(eq.max_abs_close_diff.max()) if len(eq) else None,
        "passed": bool(len(eq) > 0 and (eq.max_abs_close_diff <= 1e-9).all()),
    }
    return blocks, summary


def add_reference_state(df: pd.DataFrame) -> pd.DataFrame:
    z = df.sort_values(["trading_day", "timestamp"], kind="stable").reset_index(drop=True).copy()
    z["block_no"] = z.groupby("trading_day", sort=False).cumcount()
    z["ret_5m"] = z.groupby("trading_day", sort=False)["close"].transform(lambda s: np.log(s).diff())
    valid = z["ret_5m"].dropna()
    rv = valid.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=0)
    bg = valid.shift(1).rolling(BG_WINDOW, min_periods=BG_WINDOW).std(ddof=0)
    z["rv12"] = rv.reindex(z.index)
    z["bg_vol48"] = bg.reindex(z.index)
    z.loc[z.bg_vol48 <= 0, "bg_vol48"] = np.nan
    z["vol_ratio"] = z.rv12 / z.bg_vol48
    z["shock_intensity"] = z.ret_5m.abs() / z.bg_vol48
    z["shock"] = z.shock_intensity >= SHOCK_SIGMA

    risk = pd.Series("NORMAL", index=z.index, dtype="object")
    for _, idx in z.groupby("trading_day", sort=False).groups.items():
        mode = "NORMAL"
        for i in idx:
            ratio = z.at[i, "vol_ratio"]
            is_shock = bool(z.at[i, "shock"]) if pd.notna(z.at[i, "shock"]) else False
            mode = transition(mode, ratio, is_shock)
            risk.at[i] = mode
    z["risk_state"] = risk
    z["prev_state"] = z.groupby("trading_day", sort=False).risk_state.shift(1).fillna("NORMAL")
    z["prev_close"] = z.groupby("trading_day", sort=False).close.shift(1)
    z["year"] = pd.to_datetime(z.trading_day).dt.year.astype(int)
    return z


def transition(prev_state: str, ratio: float, is_shock: bool) -> str:
    if is_shock:
        return "UNSAFE"
    if prev_state == "UNSAFE":
        if pd.isna(ratio) or ratio >= HIGHVOL_RATIO:
            return "UNSAFE"
        if ratio > RECOVERY_NORMAL_RATIO:
            return "RECOVERING"
        return "NORMAL"
    if prev_state == "RECOVERING":
        if pd.isna(ratio):
            return "RECOVERING"
        if ratio >= HIGHVOL_RATIO:
            return "UNSAFE"
        if ratio > RECOVERY_NORMAL_RATIO:
            return "RECOVERING"
        return "NORMAL"
    return "NORMAL"


def prior_valid_windows(z: pd.DataFrame) -> dict[int, np.ndarray]:
    valid = z.ret_5m.dropna()
    idxs = list(valid.index)
    vals = valid.to_numpy(float)
    out: dict[int, np.ndarray] = {}
    for p, idx in enumerate(idxs):
        if p >= RV_WINDOW - 1:
            out[int(idx)] = vals[p - (RV_WINDOW - 1):p].copy()
    return out


def build_detection_rows(native: pd.DataFrame, blocks: pd.DataFrame) -> pd.DataFrame:
    z = add_reference_state(native)
    z = z.merge(blocks, on=["symbol", "trading_day", "block_no"], how="left", validate="one_to_one")
    if z[[f"partial_{o}" for o in OFFSETS]].isna().any().any():
        raise RuntimeError("partial-bar alignment produced missing values")

    prev_windows = prior_valid_windows(z)
    rows = []
    for i, r in z.iterrows():
        if int(r.year) not in DEV_YEARS:
            continue
        if pd.isna(r.prev_close) or pd.isna(r.bg_vol48) or i not in prev_windows:
            continue
        prev11 = prev_windows[int(i)]
        if len(prev11) != 11:
            continue
        final_state = str(r.risk_state)
        prev_state = str(r.prev_state)
        final_unsafe = final_state == "UNSAFE"
        final_recovering = final_state == "RECOVERING"
        final_shock = bool(r.shock) if pd.notna(r.shock) else False
        final_onset = final_unsafe and prev_state != "UNSAFE"
        base = {
            "symbol": str(r.symbol),
            "trading_day": str(r.trading_day),
            "year": int(r.year),
            "block_no": int(r.block_no),
            "final_state": final_state,
            "prev_state": prev_state,
            "final_unsafe": final_unsafe,
            "final_recovering": final_recovering,
            "final_shock": final_shock,
            "final_unsafe_onset": final_onset,
        }
        for offset in OFFSETS:
            pc = float(r[f"partial_{offset}"])
            pret = float(np.log(pc) - np.log(float(r.prev_close)))
            prv = float(np.std(np.concatenate([prev11, [pret]]), ddof=0))
            ratio = prv / float(r.bg_vol48)
            shock_intensity = abs(pret) / float(r.bg_vol48)
            pshock = bool(shock_intensity >= SHOCK_SIGMA)
            pstate = transition(prev_state, ratio, pshock)
            rows.append({
                **base,
                "offset": int(offset),
                "lead_minutes": int(5 - offset),
                "partial_ret_5m": pret,
                "partial_vol_ratio": ratio,
                "partial_shock_intensity": shock_intensity,
                "partial_shock": pshock,
                "partial_state": pstate,
                "partial_unsafe": pstate == "UNSAFE",
                "partial_recovering": pstate == "RECOVERING",
                "partial_unsafe_onset": pstate == "UNSAFE" and prev_state != "UNSAFE",
            })
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("no V7 detection rows")
    return out


def pr_metrics(truth: pd.Series, pred: pd.Series) -> dict:
    y = truth.astype(bool).to_numpy()
    p = pred.astype(bool).to_numpy()
    tp = int(np.sum(y & p))
    fp = int(np.sum(~y & p))
    fn = int(np.sum(y & ~p))
    tn = int(np.sum(~y & ~p))
    precision = float(tp / (tp + fp)) if tp + fp else None
    recall = float(tp / (tp + fn)) if tp + fn else None
    return {
        "n": int(len(y)), "true_n": int(y.sum()), "pred_n": int(p.sum()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall,
    }


def metric_row(g: pd.DataFrame, offset: int, group_type: str, group_value: str) -> dict:
    x = g[g.offset.eq(offset)]
    normal = x.final_state.eq("NORMAL")
    unsafe_false_alarm = int((normal & x.partial_unsafe).sum())
    normal_n = int(normal.sum())
    return {
        "offset": offset,
        "lead_minutes": 5 - offset,
        "group_type": group_type,
        "group_value": str(group_value),
        "n": int(len(x)),
        "exact_state_accuracy": float(x.partial_state.eq(x.final_state).mean()) if len(x) else None,
        "unsafe": pr_metrics(x.final_unsafe, x.partial_unsafe),
        "recovering": pr_metrics(x.final_recovering, x.partial_recovering),
        "shock": pr_metrics(x.final_shock, x.partial_shock),
        "unsafe_onset": pr_metrics(x.final_unsafe_onset, x.partial_unsafe_onset),
        "unsafe_false_alarms_per_1000_final_normal": float(1000.0 * unsafe_false_alarm / normal_n) if normal_n else None,
    }


def summarize(rows: pd.DataFrame) -> list[dict]:
    out = []
    for offset in OFFSETS:
        out.append(metric_row(rows, offset, "pooled", "pooled"))
        for year in DEV_YEARS:
            out.append(metric_row(rows[rows.year.eq(year)], offset, "year", str(year)))
        for symbol in SYMBOLS:
            out.append(metric_row(rows[rows.symbol.eq(symbol)], offset, "symbol", symbol))
    return out


def lead_summary(rows: pd.DataFrame) -> list[dict]:
    wide = rows[rows.final_unsafe_onset].pivot_table(
        index=["symbol", "trading_day", "block_no", "year"],
        columns="offset", values="partial_unsafe", aggfunc="first"
    ).reset_index()
    if wide.empty:
        return []
    for o in OFFSETS:
        if o not in wide.columns:
            wide[o] = False
        wide[o] = wide[o].fillna(False).astype(bool)

    first = []
    persistent = []
    for _, r in wide.iterrows():
        hits = [o for o in OFFSETS if bool(r[o])]
        first.append(min(hits) if hits else 5)
        pk = 5
        for o in OFFSETS:
            if all(bool(r[q]) for q in range(o, 5)):
                pk = o
                break
        persistent.append(pk)
    wide["first_hit_offset"] = first
    wide["persistent_hit_offset"] = persistent
    wide["first_lead_minutes"] = 5 - wide.first_hit_offset
    wide["persistent_lead_minutes"] = 5 - wide.persistent_hit_offset

    groups = [("pooled", "pooled", wide)]
    groups += [("year", str(y), wide[wide.year.eq(y)]) for y in DEV_YEARS]
    groups += [("symbol", s, wide[wide.symbol.eq(s)]) for s in SYMBOLS]
    out = []
    for gt, gv, g in groups:
        if not len(g):
            continue
        row = {
            "group_type": gt, "group_value": gv, "true_onsets": int(len(g)),
            "median_first_lead_minutes": float(g.first_lead_minutes.median()),
            "median_persistent_lead_minutes": float(g.persistent_lead_minutes.median()),
        }
        for lead in (4, 3, 2, 1):
            row[f"first_detected_at_least_{lead}m_early_fraction"] = float((g.first_lead_minutes >= lead).mean())
            row[f"persistent_detected_at_least_{lead}m_early_fraction"] = float((g.persistent_lead_minutes >= lead).mean())
        out.append(row)
    return out


def nested_get(metric_rows: list[dict], *, offset: int, group_type: str, group_value: str, field: str) -> dict:
    row = next(r for r in metric_rows if r["offset"] == offset and r["group_type"] == group_type and r["group_value"] == group_value)
    return row[field]


def finite_clean(v):
    if isinstance(v, dict):
        return {k: finite_clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [finite_clean(x) for x in v]
    if isinstance(v, (float, np.floating)):
        return float(v) if np.isfinite(v) else None
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def run(root: Path, out: Path) -> dict:
    eq = []
    frames = []
    for symbol in SYMBOLS:
        native = load_native_5m(root, symbol)
        one = load_native_1m(root, symbol)
        blocks, eq_s = build_partial_blocks(one, native, symbol)
        eq.append(eq_s)
        frames.append(build_detection_rows(native, blocks))
    rows = pd.concat(frames, ignore_index=True)
    metrics = summarize(rows)
    leads = lead_summary(rows)

    pooled4 = nested_get(metrics, offset=4, group_type="pooled", group_value="pooled", field="unsafe")
    annual4 = [nested_get(metrics, offset=4, group_type="year", group_value=str(y), field="unsafe") for y in DEV_YEARS]
    acceptance = {
        "equivalence_2020_2023_both_symbols": bool(all(r["passed"] for r in eq)),
        "offset4_pooled_unsafe_precision_ge_090": bool(pooled4["precision"] is not None and pooled4["precision"] >= POOLED_MIN_PRECISION),
        "offset4_pooled_unsafe_recall_ge_090": bool(pooled4["recall"] is not None and pooled4["recall"] >= POOLED_MIN_RECALL),
        "offset4_each_year_unsafe_precision_ge_085": bool(all(r["precision"] is not None and r["precision"] >= ANNUAL_MIN_PRECISION for r in annual4)),
        "offset4_each_year_unsafe_recall_ge_085": bool(all(r["recall"] is not None and r["recall"] >= ANNUAL_MIN_RECALL for r in annual4)),
        "state_thresholds_unchanged": True,
        "validation_queried_false": True,
        "blackbox_queried_false": True,
        "pnl_computed_false": True,
        "trading_rule_created_false": True,
    }
    summary = {
        "schema": "highvol_realtime_detection_v7_development",
        "development_only": True,
        "development_period": ["2021-01-01", "2023-12-31"],
        "warmup_year": 2020,
        "symbols": list(SYMBOLS),
        "reference": "validated_5m_shock_reset_state_machine_v6",
        "detector": "same_5m_state_machine_with_current_bar_partial_close_at_1m_offsets",
        "threshold_search_performed": False,
        "state_thresholds_unchanged": True,
        "pnl_computed": False,
        "trading_rule_created": False,
        "validation_queried": False,
        "blackbox_queried": False,
        "production_authority": False,
        "equivalence": eq,
        "detection_rows": int(len(rows)),
        "unique_reference_bars": int(rows[["symbol", "trading_day", "block_no"]].drop_duplicates().shape[0]),
        "metrics": metrics,
        "unsafe_onset_lead": leads,
        "acceptance": acceptance,
        "one_minute_partial_detector_validation_eligible": bool(all(acceptance.values())),
    }
    out.mkdir(parents=True, exist_ok=True)
    rows.to_csv(out / "detection_rows.csv", index=False)
    pd.DataFrame(metrics).to_json(out / "metrics.json", orient="records", indent=2)
    pd.DataFrame(leads).to_csv(out / "unsafe_onset_lead.csv", index=False)
    clean = finite_clean(summary)
    (out / "summary.json").write_text(json.dumps(clean, indent=2, allow_nan=False) + "\n")
    print(json.dumps(clean, allow_nan=False))
    return clean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run(Path(a.repo_root).resolve(), Path(a.out))


if __name__ == "__main__":
    main()
