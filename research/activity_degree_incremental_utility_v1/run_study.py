from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLS = ("000688.SH", "000852.SH")
STATES = ("NORMAL", "UNSAFE", "RECOVERING")
AGE_BUCKETS = ("NONE", "LT15", "M15_25", "M30_40", "GE45")
SLOTS = tuple(list(range(575, 691, 5)) + list(range(785, 901, 5)))
HORIZONS = (15, 30, 60)
ENDPOINTS = ("log_future_sigma", "future_tail")
MODELS = ("C", "A", "N")
LAMBDA = 0.01
M3_MIN_HISTORY = 60
RANGE_BP = 30.0
SHOCK_SIGMA = 3.0
HIGHVOL_RATIO = 1.50
RECOVERY_NORMAL_RATIO = 1.10
RV_WINDOW = 12
BG_WINDOW = 48
SEED = 20260914
BOOTSTRAPS = 5000
FAMILY = 12
PROTOCOL_BLOB = "1972c0c5ab832e4b6e04e911cc7cebdfa21b1689"
M3_RUNNER_BLOB = "2a5f607db1451a2e4576a9bc0940b67ac02f0d2e"
M3_PROTOCOL_BLOB = "d43f5b4a2c0395d1d022a3fb5e10c58dce08de0c"
V9_RUNNER_BLOB = "ae2a7e095df58692ef9df0dfee5856cac727ca44"
SOURCE_MAIN = "a26f4a302d5f73486b3b0cd04da50e382020d28f"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_blob_bytes(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def wallclock(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str).str.slice(0, 19), errors="coerce")


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


def age_bucket(age: float) -> str:
    if not np.isfinite(age) or age < 0:
        return "NONE"
    if age <= 2:
        return "LT15"
    if age <= 5:
        return "M15_25"
    if age <= 8:
        return "M30_40"
    return "GE45"


def load_5m(root: Path, years: tuple[int, ...]) -> pd.DataFrame:
    parts = []
    for symbol in SYMBOLS:
        base = root / "data/market/5m" / symbol
        for year in years:
            p = base / f"{year}.parquet"
            if not p.exists():
                raise RuntimeError(f"missing 5m input {p}")
            x = pd.read_parquet(p, columns=["trading_day", "timestamp", "close"])
            z = pd.DataFrame({
                "symbol": symbol,
                "trading_day": pd.to_datetime(x.trading_day, errors="coerce").dt.strftime("%Y-%m-%d"),
                "bar_end": wallclock(x.timestamp),
                "close": pd.to_numeric(x.close, errors="coerce"),
            }).dropna()
            if len(z) != len(x):
                raise RuntimeError(f"invalid 5m rows {symbol} {year}")
            parts.append(z)
    p = pd.concat(parts, ignore_index=True)
    p = p.sort_values(["symbol", "bar_end"], kind="stable").reset_index(drop=True)
    if p.duplicated(["symbol", "bar_end"]).any():
        raise RuntimeError("duplicate 5m key")
    counts = p.groupby(["symbol", "trading_day"]).size()
    if not counts.eq(48).all():
        raise RuntimeError("non-48-row 5m day")
    if not np.isfinite(p.close).all() or not p.close.gt(0).all():
        raise RuntimeError("invalid 5m prices")
    p["year"] = p.bar_end.dt.year.astype(int)
    p["slot"] = (p.bar_end.dt.hour * 60 + p.bar_end.dt.minute).astype(int)
    p["afternoon"] = (p.slot >= 780).astype(int)
    p["session_key"] = p.symbol + "/" + p.trading_day + "/" + p.afternoon.astype(str)
    p["session_pos"] = p.groupby("session_key", sort=False).cumcount()
    if not p.groupby("session_key").size().eq(24).all():
        raise RuntimeError("non-24-row half-session")
    p["row_id"] = np.arange(len(p), dtype=int)
    return p


def attach_history(p: pd.DataFrame) -> pd.DataFrame:
    q = p.copy()
    q["r"] = q.groupby(["symbol", "trading_day"], sort=False).close.transform(lambda s: np.log(s).diff())
    cols = ["bg48", "last_abs", "rms3", "rms6", "rms12", "rms48", "final_rv12", "prev11_sum", "prev11_sq"]
    for c in cols:
        q[c] = np.nan
    for _, g in q.groupby("symbol", sort=False):
        v = g.r.dropna()
        q.loc[v.index, "bg48"] = v.shift(1).rolling(48, min_periods=48).std(ddof=0)
        q.loc[v.index, "last_abs"] = v.shift(1).abs()
        for k in (3, 6, 12, 48):
            q.loc[v.index, f"rms{k}"] = np.sqrt(v.pow(2).shift(1).rolling(k, min_periods=k).mean())
        q.loc[v.index, "final_rv12"] = v.rolling(12, min_periods=12).std(ddof=0)
        q.loc[v.index, "prev11_sum"] = v.shift(1).rolling(11, min_periods=11).sum()
        q.loc[v.index, "prev11_sq"] = v.pow(2).shift(1).rolling(11, min_periods=11).sum()
    q.loc[q.bg48 <= 0, "bg48"] = np.nan
    q["final_vol_ratio"] = q.final_rv12 / q.bg48
    q["final_shock_intensity"] = q.r.abs() / q.bg48
    q["final_shock"] = q.final_shock_intensity >= SHOCK_SIGMA
    state = pd.Series("NORMAL", index=q.index, dtype="object")
    recent_age = pd.Series(np.nan, index=q.index, dtype=float)
    for _, idx0 in q.groupby(["symbol", "trading_day"], sort=False).groups.items():
        idx = list(idx0)
        mode = "NORMAL"
        last_shock_pos: int | None = None
        for pos, i in enumerate(idx):
            prev_mode = mode
            if prev_mode in ("UNSAFE", "RECOVERING") and last_shock_pos is not None:
                recent_age.at[i] = float(pos - last_shock_pos)
            mode = transition(mode, q.at[i, "final_vol_ratio"], bool(q.at[i, "final_shock"]) if pd.notna(q.at[i, "final_shock"]) else False)
            state.at[i] = mode
            if bool(q.at[i, "final_shock"]) if pd.notna(q.at[i, "final_shock"]) else False:
                last_shock_pos = pos
            if mode == "NORMAL":
                last_shock_pos = None
    q["risk_state"] = state
    q["previous_state"] = q.groupby(["symbol", "trading_day"], sort=False).risk_state.shift(1).fillna("NORMAL")
    q["recent_shock_age"] = recent_age
    q.loc[q.previous_state.eq("NORMAL"), "recent_shock_age"] = np.nan
    q["age_bucket"] = q.recent_shock_age.map(lambda x: age_bucket(float(x)) if pd.notna(x) else "NONE")
    q["prev_close"] = q.groupby(["symbol", "trading_day"], sort=False).close.shift(1)
    return q


def load_3s(root: Path, symbol: str, year: int) -> pd.DataFrame:
    p = root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"
    if not p.exists():
        raise RuntimeError(f"missing 3s input {p}")
    x = pd.read_parquet(p, columns=["trading_day", "observation_time", "price", "row_index"])
    day = pd.to_datetime(x.trading_day, errors="coerce").dt.strftime("%Y-%m-%d")
    dt = pd.to_datetime(day + " " + x.observation_time.astype(str), errors="coerce")
    z = pd.DataFrame({
        "trading_day": day,
        "obs_dt": dt,
        "price": pd.to_numeric(x.price, errors="coerce"),
        "row_index": pd.to_numeric(x.row_index, errors="coerce"),
    }).dropna()
    z = z.sort_values(["trading_day", "obs_dt", "row_index"], kind="stable").reset_index(drop=True)
    if not np.isfinite(z.price).all() or not z.price.gt(0).all():
        raise RuntimeError(f"invalid 3s price {symbol} {year}")
    return z


def sample_session(times: np.ndarray, prices: np.ndarray, rows: np.ndarray) -> dict[str, np.ndarray]:
    """Exact inherited strict 15-second sampling logic, plus endpoint age for audit."""
    t = np.asarray(times, float)
    p = np.asarray(prices, float)
    r = np.asarray(rows)
    grid = np.arange(0, 7201, 15)
    value = np.full(len(grid), np.nan)
    ret = np.full(len(grid), np.nan)
    age = np.full(len(grid), np.nan)
    if not len(t):
        return {"second": grid, "price": value, "return_bp": ret, "age": age}
    order = np.lexsort((r, t))
    t, p, r = t[order], p[order], r[order]
    if np.any((np.diff(t) == 0) & (np.diff(r) == 0)):
        raise ValueError("duplicate composite source key")
    pos = np.searchsorted(t, grid, side="right") - 1
    known = pos >= 0
    age[known] = grid[known] - t[pos[known]]
    good = known & (age <= 3)
    value[good] = p[pos[good]]
    gap_prefix = np.r_[0, np.cumsum(np.diff(t) > 3)]
    for j in range(1, len(grid)):
        if np.isfinite(value[j - 1 : j + 1]).all():
            a, b = pos[j - 1], pos[j]
            if gap_prefix[b] == gap_prefix[a]:
                ret[j] = np.log(value[j] / value[j - 1]) * 1e4
    return {"second": grid, "price": value, "return_bp": ret, "age": age}


def build_fine_e15(root: Path, p: pd.DataFrame, years: tuple[int, ...]) -> pd.DataFrame:
    out: list[dict] = []
    for symbol in SYMBOLS:
        ps = p[p.symbol.eq(symbol)]
        for year in years:
            sec = load_3s(root, symbol, year)
            local = sec.obs_dt
            sec["afternoon"] = (local.dt.hour >= 13).astype(int)
            sec["second_day"] = local.dt.hour * 3600 + local.dt.minute * 60 + local.dt.second
            sec["second"] = sec.second_day - np.where(sec.afternoon.eq(1), 13 * 3600, 9 * 3600 + 30 * 60)
            sec = sec[sec.second.between(0, 7200)].copy()
            groups = {(str(d), int(a)): g for (d, a), g in sec.groupby(["trading_day", "afternoon"], sort=False)}
            py = ps[ps.year.eq(year)]
            for (day, aft), bars in py.groupby(["trading_day", "afternoon"], sort=False):
                bars = bars.sort_values("bar_end", kind="stable")
                raw = groups.get((str(day), int(aft)))
                sample = sample_session(np.array([]), np.array([]), np.array([])) if raw is None else sample_session(
                    raw.second.to_numpy(float), raw.price.to_numpy(float), raw.row_index.to_numpy())
                price, r15, age = sample["price"], sample["return_bp"], sample["age"]
                start = pd.Timestamp(f"{day} {'13:00:00' if int(aft) else '09:30:00'}")
                for row in bars.itertuples(index=False):
                    decision = pd.Timestamp(row.bar_end) - pd.Timedelta(seconds=15)
                    second = int((decision - start).total_seconds())
                    if second < 0 or second > 7200 or second % 15:
                        raise RuntimeError(f"E15 not on strict grid: {symbol} {row.bar_end}")
                    j = second // 15
                    rec = {
                        "row_id": int(row.row_id), "symbol": symbol, "trading_day": str(day),
                        "year": int(year), "afternoon": int(aft), "slot": int(row.slot),
                        "decision_time": decision, "fine_complete": False, "pre5m_range_bp": np.nan,
                        "A5": np.nan, "partial_price": np.nan, "endpoint_age_seconds": np.nan,
                    }
                    if j >= 20:
                        rr = r15[j - 19 : j + 1]
                        px = price[j - 20 : j + 1]
                        complete = len(rr) == 20 and len(px) == 21 and np.isfinite(rr).all() and np.isfinite(px).all() and (px > 0).all()
                        rec["fine_complete"] = bool(complete)
                        if complete:
                            rel = np.log(px / px[0]) * 1e4
                            rec["pre5m_range_bp"] = float(rel.max() - rel.min())
                            rec["A5"] = float(np.sqrt(np.mean(rr * rr)))
                            rec["partial_price"] = float(px[-1])
                            rec["endpoint_age_seconds"] = float(age[j])
                            if rec["endpoint_age_seconds"] > 3:
                                raise RuntimeError("strict M3 endpoint age drift")
                    out.append(rec)
            del sec, groups
    z = pd.DataFrame(out)
    if z.duplicated("row_id").any():
        raise RuntimeError("duplicate E15 fine row")
    return z


def attach_m3(fine: pd.DataFrame) -> pd.DataFrame:
    z = fine.copy()
    z["M3"] = np.nan
    z["day_order"] = pd.to_datetime(z.trading_day)
    for _, ix0 in z.groupby(["symbol", "afternoon", "slot"], sort=False).groups.items():
        ix = list(ix0)
        ix.sort(key=lambda i: (z.at[i, "day_order"], i))
        prior: list[float] = []
        for i in ix:
            x = z.at[i, "A5"]
            if pd.notna(x) and np.isfinite(float(x)) and float(x) > 0:
                lx = float(np.log(float(x)))
                if len(prior) >= M3_MIN_HISTORY:
                    v = np.asarray(prior, float)
                    med = float(np.median(v))
                    mad = float(np.median(np.abs(v - med)))
                    z.at[i, "M3"] = (lx - med) / max(1.4826 * mad, 1e-8)
                prior.append(lx)
    z = z.drop(columns="day_order")
    z = z.sort_values(["symbol", "trading_day", "afternoon", "decision_time"], kind="stable")
    z["M3_lag"] = z.groupby(["symbol", "trading_day", "afternoon"], sort=False).M3.shift(1)
    return z.sort_values("row_id", kind="stable").reset_index(drop=True)


def attach_partial_coordinates(p: pd.DataFrame, fine: pd.DataFrame) -> pd.DataFrame:
    q = p.merge(fine, on=["row_id", "symbol", "trading_day", "year", "afternoon", "slot"], how="left", validate="one_to_one")
    q["partial_return"] = np.log(q.partial_price / q.prev_close)
    q["shock_intensity"] = q.partial_return.abs() / q.bg48
    mean12 = (q.prev11_sum + q.partial_return) / 12.0
    var12 = (q.prev11_sq + q.partial_return.pow(2)) / 12.0 - mean12.pow(2)
    q["vol_ratio"] = np.sqrt(np.maximum(var12, 0.0)) / q.bg48
    history_cols = ["bg48", "last_abs", "rms3", "rms6", "rms12", "rms48", "prev11_sum", "prev11_sq", "prev_close"]
    q["base_available"] = q[history_cols].notna().all(axis=1)
    q["base_available"] &= q.previous_state.isin(STATES)
    q["base_available"] &= np.isfinite(q.shock_intensity) & np.isfinite(q.vol_ratio) & q.bg48.gt(0)
    q["strict_surface"] = q.fine_complete.fillna(False) & q.pre5m_range_bp.lt(RANGE_BP)
    q["m3_available"] = np.isfinite(q.M3) & np.isfinite(q.M3_lag)
    return q


def attach_labels(p: pd.DataFrame) -> pd.DataFrame:
    q = p.copy()
    for h in HORIZONS:
        q[f"label_ok_{h}"] = False
        q[f"sigma_{h}"] = np.nan
        q[f"log_future_sigma_{h}"] = np.nan
        q[f"future_tail_{h}"] = np.nan
    for _, ix0 in q.groupby("session_key", sort=False).groups.items():
        ix = list(ix0)
        ix.sort(key=lambda i: int(q.at[i, "session_pos"]))
        r = q.loc[ix, "r"].to_numpy(float)
        for h in HORIZONS:
            n = h // 5
            for pos in range(0, len(ix) - n):
                i = ix[pos]
                fut = r[pos + 1 : pos + n + 1]
                bg = q.at[i, "bg48"]
                if len(fut) == n and np.isfinite(fut).all() and pd.notna(bg) and float(bg) > 0:
                    sigma = float(np.sqrt(np.mean(fut * fut)))
                    q.at[i, f"label_ok_{h}"] = True
                    q.at[i, f"sigma_{h}"] = sigma
                    q.at[i, f"log_future_sigma_{h}"] = float(np.log(max(sigma, 1e-12)))
                    q.at[i, f"future_tail_{h}"] = float(np.max(np.abs(fut)) >= SHOCK_SIGMA * float(bg))
    return q


def build_table(root: Path, years_5m: tuple[int, ...], years_3s: tuple[int, ...]) -> tuple[pd.DataFrame, dict]:
    raw = load_5m(root, years_5m)
    hist = attach_history(raw)
    fine = attach_m3(build_fine_e15(root, hist, years_3s))
    feat = attach_partial_coordinates(hist, fine)
    labelled = attach_labels(feat)
    identities = {"5m": {}, "3s": {}}
    for symbol in SYMBOLS:
        for year in years_5m:
            path = root / "data/market/5m" / symbol / f"{year}.parquet"
            identities["5m"][f"{symbol}:{year}"] = sha256_file(path)
        for year in years_3s:
            path = root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"
            identities["3s"][f"{symbol}:{year}"] = sha256_file(path)
    return labelled, identities


def design(q: pd.DataFrame, model: str) -> tuple[np.ndarray, list[str]]:
    if model not in MODELS:
        raise ValueError(model)
    values: dict[str, np.ndarray] = {}
    def oh(prefix: str, v, levels) -> None:
        a = np.asarray(v)
        for level in levels:
            values[f"{prefix}:{level}"] = (a == level).astype(float)
    oh("symbol", q.symbol, SYMBOLS)
    oh("slot", q.slot, SLOTS)
    oh("previous", q.previous_state, STATES)
    oh("age", q.age_bucket, AGE_BUCKETS)
    for k in (3, 6, 12, 48):
        values[f"log_rms{k}"] = np.log(np.maximum(q[f"rms{k}"].to_numpy(float), 1e-12))
    values["log_bg"] = np.log(q.bg48.to_numpy(float))
    values["log_previous_abs_z"] = np.log1p(q.last_abs.to_numpy(float) / q.bg48.to_numpy(float))
    a = np.log1p(q.shock_intensity.to_numpy(float))
    b = np.log(np.maximum(q.vol_ratio.to_numpy(float), 1e-12))
    for name, v in zip(("intensity", "ratio", "intensity2", "ratio2", "cross"), (a, b, a*a, b*b, a*b)):
        values[name] = v
        for state in STATES:
            values[f"{name}:{state}"] = v * q.previous_state.eq(state).to_numpy(float)
    if model in ("A", "N"):
        m = q.M3.to_numpy(float) if model == "A" else q.M3_lag.to_numpy(float)
        m2 = m * m
        values["activity"] = m
        values["activity2"] = m2
        for state in STATES:
            mask = q.previous_state.eq(state).to_numpy(float)
            values[f"activity:{state}"] = m * mask
            values[f"activity2:{state}"] = m2 * mask
    x = np.column_stack(list(values.values())).astype(float)
    if not np.isfinite(x).all():
        raise ValueError("nonfinite design")
    names = list(values)
    forbidden = ("future", "close", "final", "return", "sigma_")
    if any(any(k in name.lower() for k in forbidden) for name in names):
        raise RuntimeError("forbidden outcome/current-final field in design")
    return x, names


def fit_probe(x: np.ndarray, y: np.ndarray, names: list[str]) -> dict:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-14] = 1.0
    z = (x - mean) / scale
    intercept = float(np.mean(y))
    beta = np.linalg.solve(z.T @ z / len(z) + LAMBDA * np.eye(z.shape[1]), z.T @ (y - intercept) / len(z))
    return {"names": names, "mean": mean.tolist(), "scale": scale.tolist(), "beta": beta.tolist(), "intercept": intercept, "n": int(len(y))}


def predict(q: pd.DataFrame, model: str, probe: dict, endpoint: str) -> np.ndarray:
    x, names = design(q, model)
    if names != probe["names"]:
        raise RuntimeError("feature schema drift")
    value = ((x - np.asarray(probe["mean"])) / np.asarray(probe["scale"])) @ np.asarray(probe["beta"]) + float(probe["intercept"])
    return np.clip(value, 0, 1) if endpoint == "future_tail" else value


def cohort(frame: pd.DataFrame, years: tuple[int, ...], h: int) -> tuple[pd.DataFrame, dict]:
    y = frame.year.isin(years)
    base = y & frame.base_available & frame.strict_surface & frame[f"label_ok_{h}"].fillna(False)
    final = base & frame.m3_available
    z = frame.loc[final].copy().reset_index(drop=True)
    z["sigma"] = z[f"sigma_{h}"]
    z["log_future_sigma"] = z[f"log_future_sigma_{h}"]
    z["future_tail"] = z[f"future_tail_{h}"]
    counts = {
        "all_e15_rows": int(y.sum()),
        "base_history_and_iv": int((y & frame.base_available).sum()),
        "strict_path_complete": int((y & frame.base_available & frame.fine_complete.fillna(False)).sum()),
        "known_low_amplitude_surface": int((y & frame.base_available & frame.strict_surface).sum()),
        "future_feasible_on_surface": int(base.sum()),
        "m3_current_and_lag_available": int(final.sum()),
        "coverage": float(final.sum() / base.sum()) if base.sum() else 0.0,
    }
    return z, counts


def block_stats(q: pd.DataFrame, gain: np.ndarray, days_per_block: int) -> pd.DataFrame:
    d = pd.DataFrame({"day": q.trading_day.to_numpy(), "year": q.year.to_numpy(), "gain": gain, "n": 1})
    days = d[["year", "day"]].drop_duplicates().sort_values(["year", "day"])
    days["block"] = days.groupby("year").cumcount() // days_per_block
    d = d.merge(days, on=["year", "day"], validate="many_to_one")
    return d.groupby(["year", "block"], as_index=False)[["gain", "n"]].sum()


def interval(blocks: pd.DataFrame) -> dict:
    rng = np.random.default_rng(SEED)
    gains = np.zeros(BOOTSTRAPS)
    count = np.zeros(BOOTSTRAPS)
    for _, g in blocks.groupby("year", sort=True):
        ix = rng.integers(0, len(g), size=(BOOTSTRAPS, len(g)))
        gains += g.gain.to_numpy()[ix].sum(axis=1)
        count += g.n.to_numpy()[ix].sum(axis=1)
    a = 0.05 / (2 * FAMILY)
    lo, hi = np.quantile(gains / count, [a, 1-a])
    return {"low": float(lo), "high": float(hi), "blocks": int(len(blocks)), "repetitions": BOOTSTRAPS}


def compare(q: pd.DataFrame, endpoint: str, base: str, probes: dict, forward_gain: float, dev_n: int, coverage: float, h: int, out: Path) -> dict:
    y = q[endpoint].to_numpy(float)
    pa = predict(q, "A", probes[f"{h}|{endpoint}|A"], endpoint)
    pb = predict(q, base, probes[f"{h}|{endpoint}|{base}"], endpoint)
    l0 = (y - pb) ** 2
    l1 = (y - pa) ** 2
    gain = l0 - l1
    absolute = float(gain.mean())
    relative = float(absolute / l0.mean())
    slices = {}
    for col in ("year", "symbol"):
        for key, inds in q.groupby(col, sort=True).indices.items():
            slices[f"{col}:{key}"] = {"n": int(len(inds)), "absolute_gain": float(gain[inds].mean()), "relative_gain": float(gain[inds].mean()/l0[inds].mean())}
    ci = {}
    for days in (5, 20):
        b = block_stats(q, gain, days)
        b.to_csv(out / f"blocks_{h}_{endpoint}_A_vs_{base}_{days}d.csv", index=False, float_format="%.17g")
        ci[str(days)] = interval(b)
    gates = {
        "sample_size": len(q) >= 10000 and dev_n >= 20000 and all(v["n"] >= 1000 for v in slices.values()),
        "positive_events": endpoint != "future_tail" or int(y.sum()) >= 100,
        "relative_at_least_one_percent": relative >= 0.01,
        "tail_absolute_at_least_0005": endpoint != "future_tail" or absolute >= 0.0005,
        "adjusted_5day_interval_positive": ci["5"]["low"] > 0,
        "annual_and_symbol_signs": all(v["absolute_gain"] >= 0 for v in slices.values()),
        "coverage": coverage >= 0.95,
        "development_2023_forward_nonnegative": forward_gain >= 0,
    }
    return {
        "horizon": h, "endpoint": endpoint, "comparison": f"A_vs_{base}", "n": int(len(q)),
        "development_n": int(dev_n), "positive_events": int(y.sum()) if endpoint == "future_tail" else None,
        "baseline_loss": float(l0.mean()), "augmented_loss": float(l1.mean()), "absolute_gain": absolute,
        "relative_gain": relative, "ci_5day": ci["5"], "ci_20day_sensitivity": ci["20"],
        "slices": slices, "development_forward_gain": float(forward_gain), "gates": gates,
        "supported": bool(all(gates.values())),
    }


def feature_identity_checks(frame: pd.DataFrame) -> dict:
    z = frame[frame.base_available & frame.m3_available & frame.strict_surface].copy()
    if z.empty:
        raise RuntimeError("no eligible feature rows")
    c, cn = design(z.head(min(100, len(z))), "C")
    a, an = design(z.head(min(100, len(z))), "A")
    n, nn = design(z.head(min(100, len(z))), "N")
    if an != nn or a.shape[1] != n.shape[1] or a.shape[1] - c.shape[1] != 8:
        raise RuntimeError("complexity-match invariant failed")
    if not (set(cn).issubset(set(an)) and len(an) == len(cn) + 8):
        raise RuntimeError("A schema invariant failed")
    return {
        "base_columns": int(c.shape[1]), "augmented_columns": int(a.shape[1]),
        "lag_control_columns": int(n.shape[1]), "A_N_schema_identical": True,
        "augmentation_columns": 8,
    }


def forward_and_fit(frame: pd.DataFrame, out: Path, identities: dict) -> None:
    feature_check = feature_identity_checks(frame)
    probes: dict[str, dict] = {}
    forward: dict[str, dict] = {}
    coverage = {}
    for h in HORIZONS:
        dev, cov = cohort(frame, (2021, 2022, 2023), h)
        train = dev[dev.year.le(2022)].reset_index(drop=True)
        hold = dev[dev.year.eq(2023)].reset_index(drop=True)
        if train.empty or hold.empty:
            raise RuntimeError(f"empty Development forward split h={h}: {len(train)} {len(hold)}")
        coverage[str(h)] = cov
        for endpoint in ENDPOINTS:
            fwd_probes = {}
            for model in MODELS:
                x, names = design(train, model)
                fwd_probes[model] = fit_probe(x, train[endpoint].to_numpy(float), names)
                xx, nn = design(dev, model)
                probes[f"{h}|{endpoint}|{model}"] = fit_probe(xx, dev[endpoint].to_numpy(float), nn)
            y = hold[endpoint].to_numpy(float)
            pa = predict(hold, "A", fwd_probes["A"], endpoint)
            for base in ("C", "N"):
                pb = predict(hold, base, fwd_probes[base], endpoint)
                l0, l1 = (y-pb)**2, (y-pa)**2
                gain = l0-l1
                forward[f"{h}|{endpoint}|{base}"] = {
                    "n": int(len(hold)), "absolute_gain": float(gain.mean()),
                    "relative_gain": float(gain.mean()/l0.mean()),
                }
    payload = {
        "schema": "activity_degree_incremental_utility_v1_frozen_models",
        "source_main": SOURCE_MAIN,
        "protocol_git_blob": PROTOCOL_BLOB,
        "m3_runner_git_blob": M3_RUNNER_BLOB,
        "m3_protocol_git_blob": M3_PROTOCOL_BLOB,
        "v9_runner_git_blob": V9_RUNNER_BLOB,
        "ridge_lambda": LAMBDA,
        "models": probes,
        "development_forward": forward,
        "development_coverage": coverage,
        "feature_identity": feature_check,
        "input_sha256": identities,
        "training_years": [2021, 2022, 2023],
        "validation_scored": False,
        "validation_reused": True,
        "fresh_oos": False,
        "blackbox_queried": False,
        "pnl_computed": False,
        "production_authority": False,
    }
    model_path = out / "FROZEN_MODELS.json"
    dump_json(model_path, payload)
    model_sha = sha256_file(model_path)
    (out / "MODEL_SHA256.txt").write_text(model_sha + "\n", encoding="utf-8")
    dump_json(out / "FIT_RECEIPT.json", {
        "model_sha256": model_sha, "feature_identity": feature_check, "development_forward": forward,
        "development_coverage": coverage, "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
        "git_sha": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
        "validation_scored": False, "blackbox_queried": False, "production_authority": False,
    })
    print(json.dumps({"fit_complete": True, "model_sha256": model_sha, "forward": forward}, indent=2), flush=True)


def descriptive_outputs(q: pd.DataFrame, probes: dict, h: int, out: Path) -> dict:
    corr = q[["M3", "M3_lag", "shock_intensity", "vol_ratio"]].corr().to_dict()
    rows = []
    slice_rows = []
    for endpoint in ENDPOINTS:
        pc = predict(q, "C", probes[f"{h}|{endpoint}|C"], endpoint)
        pa = predict(q, "A", probes[f"{h}|{endpoint}|A"], endpoint)
        pn = predict(q, "N", probes[f"{h}|{endpoint}|N"], endpoint)
        target = q[endpoint].to_numpy(float)
        cdec = pd.qcut(pd.Series(pc), 10, labels=False, duplicates="drop")
        mdec = pd.qcut(q.M3, 10, labels=False, duplicates="drop")
        tmp = pd.DataFrame({"c_decile": cdec, "m3_decile": mdec, "target": target, "sigma": q.sigma.to_numpy(float), "tail": q.future_tail.to_numpy(float)})
        for (cd, md), g in tmp.groupby(["c_decile", "m3_decile"], dropna=False, sort=True):
            rows.append({"horizon": h, "endpoint": endpoint, "c_decile": None if pd.isna(cd) else int(cd), "m3_decile": None if pd.isna(md) else int(md),
                         "n": int(len(g)), "target_mean": float(g.target.mean()), "sigma_mean": float(g.sigma.mean()), "tail_rate": float(g.tail.mean())})
        for base, pb in (("C", pc), ("N", pn)):
            gain = (target-pb)**2 - (target-pa)**2
            for col in ("previous_state", "year", "symbol", "slot"):
                for key, inds in q.groupby(col, sort=True).indices.items():
                    slice_rows.append({"horizon": h, "endpoint": endpoint, "comparison": f"A_vs_{base}", "slice_type": col,
                                       "slice": str(key), "n": int(len(inds)), "absolute_gain": float(gain[inds].mean())})
    pd.DataFrame(rows).to_csv(out / f"decile_grid_{h}.csv", index=False)
    pd.DataFrame(slice_rows).to_csv(out / f"slice_gains_{h}.csv", index=False)
    return {"correlations": corr, "n": int(len(q))}


def validate(frame: pd.DataFrame, models_path: Path, model_sha_path: Path, out: Path, identities: dict) -> None:
    expected = model_sha_path.read_text(encoding="utf-8").strip()
    actual = sha256_file(models_path)
    if actual != expected:
        raise RuntimeError("frozen model hash mismatch")
    frozen = json.loads(models_path.read_text(encoding="utf-8"))
    if frozen.get("validation_scored") is not False or frozen.get("protocol_git_blob") != PROTOCOL_BLOB:
        raise RuntimeError("frozen model identity drift")
    if frozen.get("input_sha256", {}).get("5m", {}).get("000688.SH:2020") != identities["5m"].get("000688.SH:2020"):
        raise RuntimeError("shared source identity drift")
    comparisons = []
    joint = {}
    coverage = {}
    descriptive = {}
    for h in HORIZONS:
        q, cov = cohort(frame, (2024, 2025), h)
        dev_cov = frozen["development_coverage"][str(h)]
        coverage[str(h)] = {"validation": cov, "development": dev_cov}
        descriptive[str(h)] = descriptive_outputs(q, frozen["models"], h, out)
        for endpoint in ENDPOINTS:
            for base in ("C", "N"):
                key = f"{h}|{endpoint}|{base}"
                forward_gain = frozen["development_forward"][key]["absolute_gain"]
                comparisons.append(compare(q, endpoint, base, frozen["models"], forward_gain,
                                           frozen["models"][f"{h}|{endpoint}|A"]["n"], cov["coverage"], h, out))
            subset = [x for x in comparisons if x["horizon"] == h and x["endpoint"] == endpoint]
            joint[f"{h}|{endpoint}"] = bool(len(subset) == 2 and all(x["supported"] for x in subset))
    decision = "CURRENT_M3_INCREMENTAL_UTILITY_SUPPORTED_FOR_SPECIFIED_ENDPOINTS" if any(joint.values()) else "CURRENT_M3_INCREMENTAL_UTILITY_NOT_SUPPORTED"
    comp_df = pd.DataFrame([{k: v for k, v in x.items() if k not in ("gates", "slices", "ci_5day", "ci_20day_sensitivity")} | {"supported": x["supported"]} for x in comparisons])
    comp_df.to_csv(out / "comparisons.csv", index=False)
    dump_json(out / "VALIDATION_RESULTS.json", {
        "schema": "activity_degree_incremental_utility_v1_validation",
        "decision": decision, "joint_endpoint_support": joint, "comparisons": comparisons,
        "coverage": coverage, "descriptive": descriptive, "model_sha256": actual,
        "input_sha256": identities, "validation_years": [2024, 2025], "validation_reused": True,
        "fresh_oos": False, "read_2026": False, "blackbox_queried": False, "pnl_computed": False,
        "candidate_nominated": False, "production_authority": False, "v20_started": False, "d6_started": False,
        "git_sha": os.getenv("GITHUB_SHA"), "run_id": os.getenv("GITHUB_RUN_ID"),
    })
    print(json.dumps({"decision": decision, "joint": joint, "comparisons": [{"comparison": x["comparison"], "horizon": x["horizon"], "endpoint": x["endpoint"], "relative_gain": x["relative_gain"], "absolute_gain": x["absolute_gain"], "supported": x["supported"], "gates": x["gates"]} for x in comparisons]}, indent=2), flush=True)


def physical_guard(root: Path, phase: str) -> None:
    if (root / "data/cross_index_risk_gate_2026_v1").exists():
        raise RuntimeError("2026 protected data present")
    if phase == "fit":
        forbidden = []
        for symbol in SYMBOLS:
            for year in (2024, 2025, 2026):
                for p in (root / "data/market/5m" / symbol / f"{year}.parquet", root / "data/cross_index_risk_gate_3s_v1" / f"{symbol}_{year}.parquet"):
                    if p.exists():
                        forbidden.append(str(p))
        if forbidden:
            raise RuntimeError(f"fit workspace contains Validation data: {forbidden[:4]}")


def run(args) -> None:
    root = args.repo_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    physical_guard(root, args.phase)
    protocol = root / "research/activity_degree_incremental_utility_v1/PROTOCOL.md"
    if git_blob_bytes(protocol.read_bytes()) != PROTOCOL_BLOB:
        raise RuntimeError("protocol blob drift")
    if args.phase == "fit":
        frame, identities = build_table(root, (2020, 2021, 2022, 2023), (2021, 2022, 2023))
        forward_and_fit(frame, out, identities)
    else:
        if args.models is None or args.model_sha is None:
            raise ValueError("validation requires --models and --model-sha")
        frame, identities = build_table(root, (2020, 2021, 2022, 2023, 2024, 2025), (2021, 2022, 2023, 2024, 2025))
        validate(frame, args.models.resolve(), args.model_sha.resolve(), out, identities)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--phase", choices=("fit", "validate"), required=True)
    ap.add_argument("--models", type=Path)
    ap.add_argument("--model-sha", type=Path)
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
