"""Frozen first-shock research engine. No trades, no downloads, no 2026 reads.

Run with --synthetic for engineering controls, or --repo-root for bounded market
research using the repository loader. Synthetic output is never market evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASE = ["log_rv5", "log_rv30", "log_rv480", "log_working_energy",
        "abs_current_standardized_return", "clock_sin", "clock_cos", "afternoon"]
SEED = 20260907


def roll_mean(x: np.ndarray, n: int, min_count: int | None = None) -> np.ndarray:
    """Trailing only. Windows must have n physical rows, even if allowing NaNs."""
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or n < 1:
        raise ValueError("expected a vector and positive window")
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = sliding_window_view(x, n)
    count = np.isfinite(w).sum(axis=1)
    need = n if min_count is None else min_count
    good = count >= need
    total = np.where(np.isfinite(w), w, 0).sum(axis=1)
    out[n - 1:] = np.divide(total, count, out=np.full(len(w), np.nan), where=good & (count > 0))
    return out


def haar_energy(r: np.ndarray, length: int, smooth: int = 15) -> np.ndarray:
    """Unit-L2, trailing Haar contrasts of returns; overlapping band proxies.

    Not an additive orthogonal spectral decomposition. Every coefficient and
    subsequent energy average uses current/past observations only.
    """
    if length < 2 or length % 2:
        raise ValueError("Haar length must be positive even >=2")
    r = np.asarray(r, dtype=float)
    c = np.full(len(r), np.nan)
    if len(r) >= length:
        w = sliding_window_view(r, length)
        h = np.r_[-np.ones(length // 2), np.ones(length // 2)] / np.sqrt(length)
        c[length - 1:] = w @ h
    return roll_mean(c * c, smooth)


def event_flags(r: np.ndarray, sigma_pre: np.ndarray) -> np.ndarray:
    """Operational tail exceedance, not a claim of an econometric jump.

    Negative labels below the absolute threshold are known even if sigma is
    warming up; large returns with unknown sigma stay unknown.
    """
    r, s = np.asarray(r, float), np.asarray(sigma_pre, float)
    if r.shape != s.shape:
        raise ValueError("shape mismatch")
    out = np.full(r.shape, np.nan)
    finite_r = np.isfinite(r)
    out[finite_r & (np.abs(r) <= 30)] = 0
    known = finite_r & np.isfinite(s)
    out[known] = ((np.abs(r[known]) > 30) &
                  (np.abs(r[known]) > 4 * np.maximum(s[known], 1))).astype(float)
    return out


def event_labels(e: np.ndarray, horizon: int = 15, quiet: int = 30) -> dict[str, np.ndarray]:
    """Run separately per half-session. Features never depend on these futures."""
    e = np.asarray(e, float)
    first = np.full(len(e), np.nan)
    for j in range(quiet, len(e)):
        before = e[j - quiet:j]
        if np.isfinite(before).all() and np.isfinite(e[j]):
            first[j] = float(e[j] == 1 and not before.any())
    quiet_now = roll_mean(e, quiet) == 0
    target = np.full(len(e), np.nan)
    for t in range(len(e) - horizon):
        future = first[t + 1:t + horizon + 1]
        if np.isfinite(future).all():
            target[t] = float(future.any())
    return {"first": first, "quiet_now": quiet_now, "target": target}


def make_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Input: one or more *complete row grids*, one symbol, no cross-session r.

    Columns: session, day, year, minute(1..120), afternoon, return_bp. Unknown
    returns are NaN. Native adapters construct the full minute grid explicitly.
    """
    required = {"session", "day", "year", "minute", "afternoon", "return_bp"}
    if not required <= set(panel):
        raise ValueError(f"missing {required - set(panel)}")
    f = panel.reset_index(drop=True).copy()
    if (f.year > 2025).any() or (f.year < 2021).any():
        raise ValueError("this experiment is bounded to 2021-2025")
    if f.duplicated(["session", "minute"]).any():
        raise ValueError("duplicate minute grid")
    for col in ["sigma_pre", "rv5", "rv30", "fast_energy", "working_energy", "event", "first", "target"]:
        f[col] = np.nan
    f["quiet_now"] = False
    for _, idx in f.groupby("session", sort=False).groups.items():
        idx = np.asarray(idx)
        mins = f.loc[idx, "minute"].to_numpy()
        if not np.array_equal(mins, np.arange(1, len(idx) + 1)) or len(idx) > 120:
            raise ValueError("session must be a prefix of the full 1..120 grid")
        r = f.loc[idx, "return_bp"].to_numpy(float)
        rv30 = roll_mean(r * r, 30)
        s = np.sqrt(np.r_[np.nan, rv30[:-1]])
        energies = [haar_energy(r, k) for k in (2, 4, 8, 16)]
        ev = event_flags(r, s)
        labels = event_labels(ev)
        for col, val in {"sigma_pre": s, "rv5": roll_mean(r*r, 5), "rv30": rv30,
                         "fast_energy": (energies[0] + energies[1])/2,
                         "working_energy": (energies[2] + energies[3])/2,
                         "event": ev, **labels}.items():
            f.loc[idx, col] = val
    r = f.return_bp.to_numpy(float)
    f["rv480"] = roll_mean(r*r, 480, 456)
    for name in ("rv5", "rv30", "rv480", "working_energy", "fast_energy"):
        f["log_" + name] = np.log(np.maximum(f[name].to_numpy(float), 1e-8))
    f["abs_current_standardized_return"] = np.abs(r) / np.maximum(f.sigma_pre.to_numpy(float), 1)
    angle = 2*np.pi*f.minute.to_numpy(float)/120
    f["clock_sin"], f["clock_cos"] = np.sin(angle), np.cos(angle)
    # Eligibility at decision t uses no target or future information.
    f["decision_ok"] = (np.isfinite(f[BASE + ["log_fast_energy"]]).all(axis=1) &
                         f.quiet_now & f.minute.between(31, 105))
    f["metric_ok"] = f.decision_ok & np.isfinite(f.target)
    return f


def minute_panel(native: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Bounded repository 1m adapter. Does not synthesize an OHLC product.

    Constructs an analysis index only: absent/repair prices stay NaN. Timestamps
    follow this source's documented Shanghai wall-clock convention, NOT UTC.
    """
    required = {"symbol", "timestamp", "trading_day", "close", "causal_flat_fill",
                "high_frequency_analysis_eligible"}
    if not required <= set(native):
        raise ValueError(f"missing mandatory quality/source columns: {required-set(native)}")
    x = native.copy()
    if set(x.symbol) != {symbol} or symbol not in {"000688.SH", "000852.SH"}:
        raise ValueError("unexpected instrument")
    x["ts"] = pd.to_datetime(x.timestamp.str[:19])
    if not (x.ts.dt.strftime("%Y-%m-%d") == x.trading_day).all():
        raise ValueError("calendar-clock mismatch")
    if (x.ts.dt.year > 2025).any() or (x.ts.dt.year < 2021).any():
        raise ValueError("outside experiment years")
    if x.ts.duplicated().any():
        raise ValueError("minute timestamps are not unique")
    eligible = x.high_frequency_analysis_eligible.eq(True) & x.causal_flat_fill.eq(False)
    close = pd.to_numeric(x.close, errors="coerce")
    x["analysis_close"] = close.where(eligible & (close > 0))
    parts = []
    for day, group in x.groupby("trading_day", sort=True):
        by_time = group.set_index("ts").analysis_close
        for afternoon, opening in enumerate(("09:30:00", "13:00:00")):
            grid = pd.date_range(f"{day} {opening}", periods=121, freq="min")[1:]
            p = by_time.reindex(grid).to_numpy(float)
            r = np.r_[np.nan, np.diff(np.log(p))] * 1e4
            parts.append(pd.DataFrame({"session": f"{day}/{afternoon}", "day": day,
                "year": int(day[:4]), "minute": np.arange(1,121), "afternoon": afternoon,
                "return_bp": r, "source_valid": np.isfinite(p)}))
    return pd.concat(parts, ignore_index=True)


def snapshot_grid(seconds: pd.DataFrame, grid: pd.DatetimeIndex,
                  max_age_seconds: float = 3) -> pd.DataFrame:
    """Measurement helper only, not wired to v1's minute market hypothesis test.

    One half-session per call. Tied timestamps use greatest source row_index,
    explicitly; source rows are unmodified. No interpolation. A return crossing
    any source gap >max_age is unknown, even when both endpoints look fresh.
    """
    if grid.empty or not grid.is_monotonic_increasing or grid.has_duplicates:
        raise ValueError("need sorted unique nonempty grid")
    if grid.normalize().nunique() != 1 or (grid[-1]-grid[0]).total_seconds() > 7200:
        raise ValueError("one half-session only")
    if grid[0].hour < 12 <= grid[-1].hour:
        raise ValueError("do not cross lunch")
    need = {"observation_datetime", "row_index", "price"}
    if not need <= set(seconds):
        raise ValueError(f"missing snapshot columns: {need-set(seconds)}")
    s = seconds.copy()
    s["ts"] = pd.to_datetime(s.observation_datetime.str[:19])
    if s.duplicated(["ts", "row_index"]).any():
        raise ValueError("duplicate source composite key")
    s = s.sort_values(["ts", "row_index"], kind="stable")
    # Only observations in the specified session may supply a grid endpoint.
    opening = grid[0].normalize() + pd.Timedelta(hours=13 if grid[0].hour>=12 else 9,
                                                minutes=0 if grid[0].hour>=12 else 30)
    s = s[(s.ts >= opening) & (s.ts <= grid[-1])]
    ts = s.ts.to_numpy(dtype="datetime64[ns]").astype("int64")
    target = grid.to_numpy(dtype="datetime64[ns]").astype("int64")
    pos = np.searchsorted(ts, target, side="right")-1
    price = np.full(len(grid), np.nan); age = np.full(len(grid), np.nan)
    row = np.full(len(grid), np.nan); returns = np.full(len(grid), np.nan)
    for j, k in enumerate(pos):
        if k >= 0:
            age[j] = (target[j]-ts[k])/1e9
            p = float(s.price.iloc[k])
            if age[j] <= max_age_seconds and np.isfinite(p) and p>0:
                price[j], row[j] = p, s.row_index.iloc[k]
        if j and np.isfinite(price[j-1:j+1]).all():
            a, b = pos[j-1], k
            gaps = np.diff(ts[a:b+1])/1e9
            if not len(gaps) or np.max(gaps) <= max_age_seconds:
                returns[j] = np.log(price[j]/price[j-1])*1e4
    return pd.DataFrame({"time": grid, "price": price, "age_seconds": age,
                         "chosen_row_index": row, "return_bp": returns})


@dataclass
class PairModels:
    residualizer: Any
    residual_scale: float
    baseline: Any
    enhanced: Any
    thresholds: dict[str, dict[str, float]]

    def scores(self, f: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        b = f[BASE].to_numpy(float)
        d = (f.log_fast_energy.to_numpy(float)-self.residualizer.predict(b))/self.residual_scale
        return (self.baseline.predict_proba(b)[:,1],
                self.enhanced.predict_proba(np.c_[b,d])[:,1], d)


def fit_pair(train: pd.DataFrame, calibration: pd.DataFrame) -> PairModels:
    a, c = train.loc[train.metric_ok], calibration.loc[calibration.metric_ok]
    if len(a)<100 or len(c)<20 or a.target.nunique()!=2:
        raise ValueError("insufficient training/calibration support or only one class")
    b, y = a[BASE].to_numpy(float), a.target.to_numpy(int)
    residualizer = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    residualizer.fit(b, a.log_fast_energy.to_numpy(float))
    residual = a.log_fast_energy.to_numpy(float)-residualizer.predict(b)
    scale = max(float(np.std(residual)), 1e-8)
    baseline = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight=None,
                            max_iter=2000, solver="lbfgs", random_state=SEED))
    enhanced = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight=None,
                            max_iter=2000, solver="lbfgs", random_state=SEED))
    baseline.fit(b,y); enhanced.fit(np.c_[b,residual/scale],y)
    pair = PairModels(residualizer,scale,baseline,enhanced,{})
    pb,pe,_ = pair.scores(c)
    pair.thresholds = {name: {str(budget):float(np.quantile(p,1-budget)) for budget in (.1,.2,.3)}
                       for name,p in (("baseline",pb),("enhanced",pe))}
    return pair


def ratio(num: float, den: float) -> float | None:
    return float(num/den) if den else None


def metrics(y: np.ndarray, p: np.ndarray, alarm: np.ndarray) -> dict[str, Any]:
    y,p,alarm = np.asarray(y,int),np.asarray(p,float),np.asarray(alarm,bool)
    if not len(y):
        return {"n":0}
    clean = ~alarm
    return {"n":len(y), "events_windows":int(y.sum()), "risk_time":float(alarm.mean()),
            "clean_coverage":float(clean.mean()), "risk_inside_clean":ratio(y[clean].sum(),clean.sum()),
            "event_window_miss_share":ratio(y[clean].sum(),y.sum()),
            "window_recall":ratio(y[alarm].sum(),y.sum()),
            "window_precision":ratio(y[alarm].sum(),alarm.sum()),
            "brier":float(brier_score_loss(y,p)),
            "log_loss":float(log_loss(y,np.c_[1-p,p],labels=[0,1])),
            "auc":float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None}


def budget_alarm(p: np.ndarray, budget: float) -> np.ndarray:
    """Evaluation-only exact quota, stable chronological tie break."""
    a = np.zeros(len(p),bool)
    n = int(np.floor(len(p)*budget))
    if n:
        a[np.argsort(-np.asarray(p),kind="stable")[:n]] = True
    return a


def match_events(f: pd.DataFrame, alarm: np.ndarray, min_lead: int = 1,
                 horizon: int = 15) -> tuple[dict[str, Any], pd.DataFrame]:
    """Unique event matching; denominator includes unknown/uncovered events.

    Minute return closed at e started no later than e-1. Alarm t is acceptable
    only if e-1-t >= min_lead. Earliest and latest valid leads are both retained.
    """
    if len(f)!=len(alarm):
        raise ValueError("alarm length mismatch")
    q=f.reset_index(drop=True); alarm=np.asarray(alarm,bool)
    records=[]; alarm_segments=[]
    for session,idx in q.groupby("session",sort=False).groups.items():
        idx=np.asarray(idx); sub=q.loc[idx]; mins=sub.minute.to_numpy(int)
        valid=sub.decision_ok.to_numpy(bool)
        local_alarm=alarm[idx]&valid
        for epos in np.flatnonzero(sub["first"].to_numpy(float)==1):
            e=mins[epos]
            if e<33:  # no ordinary decision with >=1 min pre-onset lead is possible
                continue
            candidates=(mins>=e-horizon)&(mins<=e-1-min_lead)
            eligible=candidates&valid
            hits=mins[candidates&local_alarm]
            records.append({"session":session,"day":sub.day.iloc[epos],"minute":int(e),
                "amplitude_bp":float(abs(sub.return_bp.iloc[epos])),
                "eligible":bool(eligible.any()),"warned":bool(len(hits)),
                "earliest_lead":float(e-1-hits.min()) if len(hits) else None,
                "latest_lead":float(e-1-hits.max()) if len(hits) else None})
        # Episode begins anew after a false/unknown/noncontiguous decision.
        start=None;last=None
        for j,m in enumerate(mins):
            if local_alarm[j]:
                if start is None or m != last+1:
                    if start is not None: alarm_segments.append((session,start,last))
                    start=m
                last=m
            elif start is not None:
                alarm_segments.append((session,start,last));start=None
        if start is not None: alarm_segments.append((session,start,last))
    events=pd.DataFrame.from_records(records,columns=["session","day","minute","amplitude_bp",
                         "eligible","warned","earliest_lead","latest_lead"])
    # Greedy one-to-one episode/event matching, not unlimited duplicates.
    matched=set(); matched_episodes=0
    for session,start,end in alarm_segments:
        for k,e in events[events.session==session].iterrows():
            if k not in matched and max(start,int(e.minute)-horizon)<=min(end,int(e.minute)-1-min_lead):
                matched.add(k);matched_episodes+=1;break
    if events.empty:
        return {"unique_first_events":0,"alarm_episodes":len(alarm_segments)},events
    hit=events.warned.to_numpy(bool);elig=events.eligible.to_numpy(bool)
    amp=events.amplitude_bp.to_numpy(float)
    return {"unique_first_events":len(events),"eligible_first_events":int(elig.sum()),
        "unknown_or_no_eligible_warning_share":float((~elig).mean()),
        "warned_events":int(hit.sum()),"recall_all_known_events":float(hit.mean()),
        "recall_eligible_events":ratio(hit.sum(),elig.sum()),
        "amplitude_weighted_miss_share":ratio(amp[~hit].sum(),amp.sum()),
        "median_earliest_lead_minutes":float(events.loc[hit,"earliest_lead"].median()) if hit.any() else None,
        "median_latest_lead_minutes":float(events.loc[hit,"latest_lead"].median()) if hit.any() else None,
        "alarm_episodes":len(alarm_segments),"matched_episodes_one_to_one":matched_episodes,
        "episode_precision_one_to_one":ratio(matched_episodes,len(alarm_segments))},events


def moving_block_ci(values: np.ndarray, block: int = 5, repeats: int = 500,
                    seed: int = SEED) -> dict[str, Any]:
    """Paired daily sufficient statistics: [clean_y_B, clean_n_B, clean_y_E, clean_n_E]."""
    v=np.asarray(values,float)
    if v.ndim!=2 or v.shape[1]!=4 or len(v)<block:
        return {"status":"insufficient_blocks"}
    rng=np.random.default_rng(seed);n=len(v);delta=[]
    for _ in range(repeats):
        starts=rng.integers(0,n-block+1,size=int(np.ceil(n/block)))
        indices=np.concatenate([np.arange(s,s+block) for s in starts])[:n]
        a,b,c,d=v[indices].sum(axis=0)
        if b and d:delta.append(c/d-a/b)
    if not delta:return {"status":"empty_denominator"}
    return {"status":"computed","replicates":len(delta),"block_trading_days":block,
            "delta_enhanced_minus_baseline_ci95":np.quantile(delta,[.025,.975]).tolist()}


def evaluate(pair: PairModels, f: pd.DataFrame, budget: float = .2) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    q=f.reset_index(drop=True).copy();valid=q.decision_ok.to_numpy(bool)
    q["baseline_score"]=np.nan;q["enhanced_score"]=np.nan;q["decoupling"]=np.nan
    if valid.any():
        b,e,d=pair.scores(q.loc[valid])
        q.loc[valid,["baseline_score","enhanced_score","decoupling"]]=np.c_[b,e,d]
    observed=q.metric_ok.to_numpy(bool)
    result={"all_rows":len(q),"ordinary_rows":int(q.minute.between(31,105).sum()),
       "decisions":int(valid.sum()),"mature_label_decisions":int(observed.sum()),
       "unknown_future_labels":int((valid&~observed).sum()),"models":{}}
    events=[];quotas={}
    for model in ("baseline","enhanced"):
        p=q.loc[observed,model+"_score"].to_numpy(float);y=q.loc[observed,"target"].to_numpy(int)
        threshold=pair.thresholds[model][str(budget)]
        a=valid&(q[model+"_score"].to_numpy(float)>=threshold)
        summary,ev=match_events(q,a)
        ev["model"]=model;ev["threshold_mode"]="frozen_calibration";events.append(ev)
        quota=budget_alarm(q.loc[valid,model+"_score"].to_numpy(float),budget)
        aq=np.zeros(len(q),bool);aq[valid]=quota;quotas[model]=aq
        qs,qe=match_events(q,aq);qe["model"]=model;qe["threshold_mode"]="evaluation_quota";events.append(qe)
        result["models"][model]={"frozen_threshold":threshold,
            "dense_windows_frozen":metrics(y,p,a[observed]),"strict_events_frozen":summary,
            "dense_windows_matched_quota":metrics(y,p,aq[observed]),"strict_events_matched_quota":qs}
        q[model+"_alarm_frozen"]=a;q[model+"_alarm_quota"]=aq
    daily=[]
    for _,ix in q.groupby("day",sort=True).groups.items():
        ix=np.asarray(ix);ix=ix[observed[ix]];row=[]
        for model in ("baseline","enhanced"):
            ci=ix[~quotas[model][ix]]
            row += [float(q.loc[ci,"target"].sum()),len(ci)]
        daily.append(row)
    result["matched_quota_clean_risk_bootstrap"]=moving_block_ci(np.asarray(daily))
    all_events=pd.concat(events,ignore_index=True)
    evq=all_events[all_events.threshold_mode=="evaluation_quota"]
    daily_recall=[];daily_amplitude=[]
    for day in sorted(q.day.unique()):
        rr=[];aa=[]
        for model in ("baseline","enhanced"):
            z=evq[(evq.day==day)&(evq.model==model)]
            rr += [int(z.warned.sum()),len(z)]
            aa += [float(z.loc[~z.warned.astype(bool),"amplitude_bp"].sum()),float(z.amplitude_bp.sum())]
        daily_recall.append(rr);daily_amplitude.append(aa)
    result["matched_quota_event_recall_bootstrap"]=moving_block_ci(np.asarray(daily_recall))
    result["matched_quota_amplitude_miss_bootstrap"]=moving_block_ci(np.asarray(daily_amplitude))
    return result,q,all_events


def synthetic_panel(kind: str, sessions: int = 550, seed: int = SEED) -> pd.DataFrame:
    """Known-DGP controls, not market conclusions. First 220/110/220 sessions.

    Null: a random same-amplitude sign pattern independent of later shocks.
    Positive: the same pattern 3..12 minutes before a scheduled random shock.
    The generator may know future synthetic events; the feature engine may not.
    """
    if kind not in {"null","precursor"}:raise ValueError("unknown control")
    rng=np.random.default_rng(seed);parts=[]
    for j in range(sessions):
        year=2021 if j<220 else (2023 if j<330 else 2024)
        local_j = j if j<220 else (j-220 if j<330 else j-330)
        day=(pd.Timestamp(f"{year}-01-01")+pd.offsets.BDay(local_j)).strftime("%Y-%m-%d")
        scale=5*np.exp(rng.normal(0,.22))
        clock=np.arange(1,121);vol=scale*(1+.15*np.cos(clock*np.pi/60))
        r=rng.normal(size=120)*vol
        event_minute=int(rng.integers(65,116)) if rng.random()<.6 else None
        sham_end=int(rng.integers(50,106))
        end=event_minute-3 if kind=="precursor" and event_minute is not None else sham_end
        ix=np.arange(end-9,end+1)-1
        # Preserve every absolute return: only serial sign structure changes.
        r[ix]=np.abs(r[ix]) * np.where(np.arange(len(ix))%2,1,-1)
        if event_minute is not None:r[event_minute-1]=rng.choice([-1,1])*max(60,scale*12)
        r[0]=np.nan
        parts.append(pd.DataFrame({"session":f"synthetic-{j:04d}","day":day,"year":year,
               "minute":clock,"afternoon":j%2,"return_bp":r}))
    return pd.concat(parts,ignore_index=True)


def _json_clean(x: Any) -> Any:
    if isinstance(x,dict):return {str(k):_json_clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [_json_clean(v) for v in x]
    if isinstance(x,np.generic):return _json_clean(x.item())
    if isinstance(x,float) and not np.isfinite(x):return None
    return x


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(_json_clean(obj),ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def run_one(panel: pd.DataFrame, out: Path, label: str) -> dict:
    f=make_features(panel)
    pair=fit_pair(f[f.year.isin([2021,2022])],f[f.year==2023])
    output={"label":label,"thresholds":pair.thresholds,"results":{}}
    for year in sorted(set(f.year)&{2024,2025}):
        summary,points,events=evaluate(pair,f[f.year==year])
        output["results"][str(year)]=summary
        points.to_csv(out/f"{label}_{year}_decisions.csv.gz",index=False,compression="gzip")
        events.to_csv(out/f"{label}_{year}_events.csv",index=False)
    write_json(out/f"{label}_summary.json",output)
    # Exact fitted estimators retained for reproducibility, not a production model.
    import joblib
    joblib.dump(pair,out/f"{label}_estimators.joblib")
    return output


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic",action="store_true")
    mode.add_argument("--repo-root",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError("refuse to overwrite nonempty output directory")
    args.out.mkdir(parents=True,exist_ok=True)
    outputs=[]
    if args.synthetic:
        for kind in ("null","precursor"):
            outputs.append(run_one(synthetic_panel(kind),args.out,"synthetic_"+kind))
    else:
        import sys
        root=args.repo_root.resolve();sys.path.insert(0,str(root/"src"))
        from star50_filter.cloud_market_data import load_market_data
        panels={}
        for symbol in ("000688.SH","000852.SH"):
            native=load_market_data(symbol,"1m","2021-01-01","2025-12-31",root=root)
            panels[symbol]=minute_panel(native,symbol)
        common=set(panels["000688.SH"].session)&set(panels["000852.SH"].session)
        # Paired source support: a repair/missing return in either series is
        # unknown in BOTH primary series. Keep counts to expose coverage cost.
        a=panels["000688.SH"];b=panels["000852.SH"]
        a=a[a.session.isin(common)].reset_index(drop=True);b=b[b.session.isin(common)].reset_index(drop=True)
        if not a[["session","minute"]].equals(b[["session","minute"]]):
            raise ValueError("unpaired timestamp support")
        jointly_valid=np.isfinite(a.return_bp)&np.isfinite(b.return_bp)
        audit={"common_sessions":len(common),"paired_rows":len(a),
               "jointly_valid_returns":int(jointly_valid.sum()),"source":{},
               "sensitivity_individual_support":"not run; no scientific promotion"}
        for symbol,x in (("000688.SH",a),("000852.SH",b)):
            audit["source"][symbol]={"valid_returns_before_pairing":int(np.isfinite(x.return_bp).sum())}
            x.loc[~jointly_valid,"return_bp"]=np.nan
            outputs.append(run_one(x,args.out,symbol))
        write_json(args.out/"paired_support.json",audit)
    import sklearn
    receipt={"mode":"synthetic_only" if args.synthetic else "bounded_consumed_market_development",
             "market_evidence":not args.synthetic,"production_authority":False,"fresh_oos":False,
             "python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
             "sklearn":sklearn.__version__,"script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "summary_files":[x["label"]+"_summary.json" for x in outputs]}
    write_json(args.out/"run_receipt.json",receipt)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=="__main__":
    main()
