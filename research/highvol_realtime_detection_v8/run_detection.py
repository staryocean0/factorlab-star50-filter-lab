from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
WARMUP_YEAR = 2020
DEV_YEARS = (2021, 2022, 2023)
REF_YEARS = (2020, 2021, 2022, 2023)
LEADS = (60, 30, 15, 6, 3)

RV_WINDOW = 12
BG_WINDOW = 48
HIGHVOL_RATIO = 1.50
RECOVERY_NORMAL_RATIO = 1.10
SHOCK_SIGMA = 3.00

MIN_COVERAGE = 0.95
POOLED_MIN_PRECISION = 0.90
POOLED_MIN_RECALL = 0.90
ANNUAL_MIN_PRECISION = 0.85
ANNUAL_MIN_RECALL = 0.85


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


def load_reference(root: Path, symbol: str) -> pd.DataFrame:
    base = root / "data/market/5m" / symbol
    got = sorted(p.name for p in base.glob("*.parquet"))
    exp = [f"{y}.parquet" for y in REF_YEARS]
    if got != exp:
        raise RuntimeError(f"5m physical boundary violation {symbol}: {got}")
    parts = []
    for y in REF_YEARS:
        x = pd.read_parquet(base / f"{y}.parquet")
        if "timestamp" not in x.columns or "trading_day" not in x.columns or "close" not in x.columns:
            raise RuntimeError(f"bad 5m schema {symbol} {y}")
        z = pd.DataFrame({
            "symbol": symbol,
            "trading_day": pd.to_datetime(x.trading_day, errors="coerce").dt.strftime("%Y-%m-%d"),
            "bar_end": wallclock(x.timestamp),
            "close": pd.to_numeric(x.close, errors="coerce"),
        }).dropna()
        parts.append(z)
    z = pd.concat(parts, ignore_index=True).sort_values(["trading_day", "bar_end"], kind="stable").reset_index(drop=True)
    z["block_no"] = z.groupby("trading_day", sort=False).cumcount()
    counts = z.groupby("trading_day").size()
    bad = counts[counts != 48]
    if len(bad):
        raise RuntimeError(f"reference non-48-row days {symbol}: {bad.head().to_dict()}")
    return add_reference_state(z)


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


def add_reference_state(z: pd.DataFrame) -> pd.DataFrame:
    z = z.copy()
    z["ret_5m"] = z.groupby("trading_day", sort=False).close.transform(lambda s: np.log(s).diff())
    valid = z.ret_5m.dropna()
    z["rv12"] = valid.rolling(RV_WINDOW, min_periods=RV_WINDOW).std(ddof=0).reindex(z.index)
    z["bg_vol48"] = valid.shift(1).rolling(BG_WINDOW, min_periods=BG_WINDOW).std(ddof=0).reindex(z.index)
    z.loc[z.bg_vol48 <= 0, "bg_vol48"] = np.nan
    z["vol_ratio"] = z.rv12 / z.bg_vol48
    z["shock_intensity"] = z.ret_5m.abs() / z.bg_vol48
    z["shock"] = z.shock_intensity >= SHOCK_SIGMA
    risk = pd.Series("NORMAL", index=z.index, dtype="object")
    for _, idx in z.groupby("trading_day", sort=False).groups.items():
        mode = "NORMAL"
        for i in idx:
            mode = transition(mode, z.at[i, "vol_ratio"], bool(z.at[i, "shock"]) if pd.notna(z.at[i, "shock"]) else False)
            risk.at[i] = mode
    z["risk_state"] = risk
    z["prev_state"] = z.groupby("trading_day", sort=False).risk_state.shift(1).fillna("NORMAL")
    z["prev_close"] = z.groupby("trading_day", sort=False).close.shift(1)
    z["year"] = pd.to_datetime(z.trading_day).dt.year.astype(int)
    return z


def prior_windows(z: pd.DataFrame) -> dict[int, np.ndarray]:
    valid = z.ret_5m.dropna()
    vals = valid.to_numpy(float)
    ids = list(valid.index)
    out: dict[int, np.ndarray] = {}
    for pos, idx in enumerate(ids):
        if pos >= RV_WINDOW - 1:
            out[int(idx)] = vals[pos - (RV_WINDOW - 1):pos].copy()
    return out


def load_3s_year(root: Path, symbol: str, year: int) -> pd.DataFrame:
    p = root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"
    if not p.exists():
        raise RuntimeError(f"missing 3s {p}")
    x = pd.read_parquet(p, columns=["trading_day", "observation_time", "price", "row_index", "session_phase"])
    x["trading_day"] = pd.to_datetime(x.trading_day, errors="coerce").dt.strftime("%Y-%m-%d")
    x["obs_dt"] = pd.to_datetime(x.trading_day + " " + x.observation_time.astype(str), errors="coerce")
    x["price"] = pd.to_numeric(x.price, errors="coerce")
    x["row_index"] = pd.to_numeric(x.row_index, errors="coerce")
    x = x.dropna(subset=["trading_day", "obs_dt", "price", "row_index"])
    x = x.sort_values(["trading_day", "obs_dt", "row_index"], kind="stable").reset_index(drop=True)
    return x


def select_checkpoint(obs: pd.DataFrame, start: pd.Timestamp, target: pd.Timestamp) -> tuple[float, pd.Timestamp] | None:
    if obs.empty:
        return None
    times = obs.obs_dt.to_numpy(dtype="datetime64[ns]")
    tgt = np.datetime64(target.to_datetime64())
    pos = int(np.searchsorted(times, tgt, side="right") - 1)
    if pos < 0:
        return None
    row = obs.iloc[pos]
    if row.obs_dt < start:
        return None
    return float(row.price), pd.Timestamp(row.obs_dt)


def build_rows_for_symbol(root: Path, symbol: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ref = load_reference(root, symbol)
    windows = prior_windows(ref)
    detail = []
    coverage = []
    for year in DEV_YEARS:
        sec = load_3s_year(root, symbol, year)
        by_day = {d: g.reset_index(drop=True) for d, g in sec.groupby("trading_day", sort=False)}
        rr = ref[ref.year.eq(year)]
        for i, r in rr.iterrows():
            if pd.isna(r.prev_close) or pd.isna(r.bg_vol48) or int(i) not in windows:
                continue
            prev11 = windows[int(i)]
            if len(prev11) != 11:
                continue
            dayobs = by_day.get(str(r.trading_day), pd.DataFrame())
            start = pd.Timestamp(r.bar_end) - pd.Timedelta(minutes=5)
            base = {
                "symbol": symbol,
                "trading_day": str(r.trading_day),
                "year": year,
                "block_no": int(r.block_no),
                "bar_end": pd.Timestamp(r.bar_end),
                "final_state": str(r.risk_state),
                "prev_state": str(r.prev_state),
                "final_unsafe": str(r.risk_state) == "UNSAFE",
                "final_recovering": str(r.risk_state) == "RECOVERING",
                "final_shock": bool(r.shock) if pd.notna(r.shock) else False,
                "final_unsafe_onset": str(r.risk_state) == "UNSAFE" and str(r.prev_state) != "UNSAFE",
            }
            for lead in LEADS:
                target = pd.Timestamp(r.bar_end) - pd.Timedelta(seconds=lead)
                sel = select_checkpoint(dayobs, start, target)
                coverage.append({"symbol": symbol, "trading_day": str(r.trading_day), "year": year, "block_no": int(r.block_no), "lead_seconds": lead, "available": sel is not None})
                if sel is None:
                    continue
                price, obs_time = sel
                pret = float(np.log(price) - np.log(float(r.prev_close)))
                prv = float(np.std(np.concatenate([prev11, [pret]]), ddof=0))
                ratio = prv / float(r.bg_vol48)
                pint = abs(pret) / float(r.bg_vol48)
                pshock = bool(pint >= SHOCK_SIGMA)
                pstate = transition(str(r.prev_state), ratio, pshock)
                detail.append({
                    **base,
                    "lead_seconds": lead,
                    "checkpoint": target,
                    "selected_observation_time": obs_time,
                    "staleness_seconds": float((target - obs_time).total_seconds()),
                    "selected_price": price,
                    "partial_ret_5m": pret,
                    "partial_vol_ratio": ratio,
                    "partial_shock_intensity": pint,
                    "partial_shock": pshock,
                    "partial_state": pstate,
                    "partial_unsafe": pstate == "UNSAFE",
                    "partial_recovering": pstate == "RECOVERING",
                    "partial_unsafe_onset": pstate == "UNSAFE" and str(r.prev_state) != "UNSAFE",
                })
    return pd.DataFrame(detail), pd.DataFrame(coverage)


def pr_metrics(truth: pd.Series, pred: pd.Series) -> dict:
    y = truth.astype(bool).to_numpy(); p = pred.astype(bool).to_numpy()
    tp = int(np.sum(y & p)); fp = int(np.sum(~y & p)); fn = int(np.sum(y & ~p)); tn = int(np.sum(~y & ~p))
    return {
        "n": int(len(y)), "true_n": int(y.sum()), "pred_n": int(p.sum()), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": float(tp/(tp+fp)) if tp+fp else None,
        "recall": float(tp/(tp+fn)) if tp+fn else None,
    }


def summarize_group(detail: pd.DataFrame, cov: pd.DataFrame, lead: int, gt: str, gv: str) -> dict:
    d = detail[detail.lead_seconds.eq(lead)]
    c = cov[cov.lead_seconds.eq(lead)]
    normal = d.final_state.eq("NORMAL")
    st = d.staleness_seconds.to_numpy(float)
    return {
        "lead_seconds": lead, "group_type": gt, "group_value": gv,
        "eligible_reference_bars": int(len(c)), "available_bars": int(c.available.sum()),
        "coverage": float(c.available.mean()) if len(c) else None,
        "median_staleness_seconds": float(np.median(st)) if len(st) else None,
        "p95_staleness_seconds": float(np.quantile(st, .95)) if len(st) else None,
        "exact_state_accuracy": float(d.partial_state.eq(d.final_state).mean()) if len(d) else None,
        "unsafe": pr_metrics(d.final_unsafe, d.partial_unsafe),
        "recovering": pr_metrics(d.final_recovering, d.partial_recovering),
        "shock": pr_metrics(d.final_shock, d.partial_shock),
        "unsafe_onset": pr_metrics(d.final_unsafe_onset, d.partial_unsafe_onset),
        "unsafe_false_alarms_per_1000_final_normal": float(1000*(normal & d.partial_unsafe).sum()/normal.sum()) if normal.sum() else None,
    }


def summaries(detail: pd.DataFrame, cov: pd.DataFrame) -> list[dict]:
    out=[]
    for lead in LEADS:
        out.append(summarize_group(detail,cov,lead,"pooled","pooled"))
        for y in DEV_YEARS:
            out.append(summarize_group(detail[detail.year.eq(y)],cov[cov.year.eq(y)],lead,"year",str(y)))
        for s in SYMBOLS:
            out.append(summarize_group(detail[detail.symbol.eq(s)],cov[cov.symbol.eq(s)],lead,"symbol",s))
    return out


def onset_leads(detail: pd.DataFrame, cov: pd.DataFrame) -> list[dict]:
    keys=["symbol","trading_day","block_no","year"]
    true_keys=detail[detail.final_unsafe_onset][keys].drop_duplicates()
    if true_keys.empty: return []
    grid=true_keys.merge(cov,on=keys,how="left")
    hit=detail[detail.final_unsafe_onset][keys+["lead_seconds","partial_unsafe"]]
    grid=grid.merge(hit,on=keys+["lead_seconds"],how="left")
    grid["partial_unsafe"]=grid.partial_unsafe.fillna(False).astype(bool)
    out=[]
    groups=[("pooled","pooled",grid)] + [("year",str(y),grid[grid.year.eq(y)]) for y in DEV_YEARS] + [("symbol",s,grid[grid.symbol.eq(s)]) for s in SYMBOLS]
    order=list(LEADS)
    for gt,gv,g in groups:
        ids=g[keys].drop_duplicates()
        first=[]; persistent=[]
        for _,krow in ids.iterrows():
            mask=np.ones(len(g),dtype=bool)
            for k in keys: mask &= g[k].eq(krow[k]).to_numpy()
            gg=g.loc[mask].set_index("lead_seconds")
            hits={lead: bool(gg.at[lead,"partial_unsafe"]) if lead in gg.index else False for lead in order}
            leads_hit=[lead for lead in order if hits[lead]]
            first.append(max(leads_hit) if leads_hit else 0)
            p=0
            for j,lead in enumerate(order):
                if hits[lead] and all(hits[q] for q in order[j:]):
                    p=lead; break
            persistent.append(p)
        if len(ids):
            out.append({"group_type":gt,"group_value":gv,"true_onsets":int(len(ids)),"median_earliest_lead_seconds":float(np.median(first)),"median_persistent_lead_seconds":float(np.median(persistent)),**{f"detected_by_{lead}s_fraction":float(np.mean(np.asarray(first)>=lead)) for lead in order}})
    return out


def get_metric(rows:list[dict], lead:int, gt:str, gv:str)->dict:
    return next(r for r in rows if r["lead_seconds"]==lead and r["group_type"]==gt and r["group_value"]==gv)


def clean(v):
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list): return [clean(x) for x in v]
    if isinstance(v,(float,np.floating)): return float(v) if np.isfinite(v) else None
    if isinstance(v,np.integer): return int(v)
    return v


def run(root:Path,out:Path)->dict:
    ds=[]; cs=[]
    for s in SYMBOLS:
        d,c=build_rows_for_symbol(root,s); ds.append(d); cs.append(c)
    detail=pd.concat(ds,ignore_index=True); cov=pd.concat(cs,ignore_index=True)
    sm=summaries(detail,cov); leads=onset_leads(detail,cov)
    p3=get_metric(sm,3,"pooled","pooled")
    y3=[get_metric(sm,3,"year",str(y)) for y in DEV_YEARS]
    acc={
        "lead3_pooled_coverage_ge_095": bool(p3["coverage"] is not None and p3["coverage"]>=MIN_COVERAGE),
        "lead3_each_year_coverage_ge_095": bool(all(r["coverage"] is not None and r["coverage"]>=MIN_COVERAGE for r in y3)),
        "lead3_pooled_unsafe_precision_ge_090": bool(p3["unsafe"]["precision"] is not None and p3["unsafe"]["precision"]>=POOLED_MIN_PRECISION),
        "lead3_pooled_unsafe_recall_ge_090": bool(p3["unsafe"]["recall"] is not None and p3["unsafe"]["recall"]>=POOLED_MIN_RECALL),
        "lead3_each_year_unsafe_precision_ge_085": bool(all(r["unsafe"]["precision"] is not None and r["unsafe"]["precision"]>=ANNUAL_MIN_PRECISION for r in y3)),
        "lead3_each_year_unsafe_recall_ge_085": bool(all(r["unsafe"]["recall"] is not None and r["unsafe"]["recall"]>=ANNUAL_MIN_RECALL for r in y3)),
        "state_thresholds_unchanged":True,"validation_queried_false":True,"blackbox_queried_false":True,"pnl_computed_false":True,"trading_rule_created_false":True,
    }
    summary={
        "schema":"highvol_realtime_detection_v8_3s_development","development_only":True,"development_period":["2021-01-01","2023-12-31"],"warmup_year":2020,
        "symbols":list(SYMBOLS),"reference":"validated_5m_shock_reset_state_machine_v6","leads_seconds":list(LEADS),"selection":"latest same-block 3s observation at-or-before checkpoint; same timestamp greatest row_index",
        "threshold_search_performed":False,"state_thresholds_unchanged":True,"pnl_computed":False,"trading_rule_created":False,"validation_queried":False,"blackbox_queried":False,"production_authority":False,
        "available_detection_rows":int(len(detail)),"eligible_checkpoint_rows":int(len(cov)),"metrics":sm,"unsafe_onset_lead":leads,"acceptance":acc,"three_second_detector_validation_eligible":bool(all(acc.values())),
    }
    out.mkdir(parents=True,exist_ok=True)
    detail.to_csv(out/"detection_rows.csv",index=False); cov.to_csv(out/"coverage_rows.csv",index=False)
    (out/"summary.json").write_text(json.dumps(clean(summary),indent=2,allow_nan=False)+"\n")
    print(json.dumps(clean(summary),allow_nan=False)); return clean(summary)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); ap.add_argument("--out",required=True); a=ap.parse_args(); run(Path(a.repo_root).resolve(),Path(a.out))

if __name__=="__main__": main()
