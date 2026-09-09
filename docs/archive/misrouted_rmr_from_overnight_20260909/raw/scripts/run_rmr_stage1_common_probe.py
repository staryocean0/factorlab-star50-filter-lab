#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

EXPECTED_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
DEV_END = "2019-12-31"
STAB_START = "2020-01-01"
STAB_END = "2022-12-31"
HORIZON_BARS = 1200


@dataclass(frozen=True)
class Wave:
    direction: int
    start_idx: int
    end_idx: int
    confirm_idx: int
    start_price: float
    end_price: float

    @property
    def move(self) -> float:
        return self.end_price / self.start_price - 1.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def detect_waves(prices: np.ndarray, threshold: float) -> list[Wave]:
    p = np.asarray(prices, dtype=float)
    if len(p) < 3 or threshold <= 0.0:
        return []
    waves: list[Wave] = []
    mode = 0
    anchor_idx = 0
    anchor = p[0]
    extreme_idx = 0
    extreme = p[0]
    boot_min_idx = 0
    boot_min = p[0]
    boot_max_idx = 0
    boot_max = p[0]
    for i in range(1, len(p)):
        x = p[i]
        if not np.isfinite(x) or x <= 0.0:
            continue
        if mode == 0:
            if x < boot_min:
                boot_min = x
                boot_min_idx = i
            if x > boot_max:
                boot_max = x
                boot_max_idx = i
            if x / boot_min - 1.0 >= threshold:
                mode = 1
                anchor_idx = boot_min_idx
                anchor = boot_min
                extreme_idx = i
                extreme = x
            elif x / boot_max - 1.0 <= -threshold:
                mode = -1
                anchor_idx = boot_max_idx
                anchor = boot_max
                extreme_idx = i
                extreme = x
            continue
        if mode == 1:
            if x > extreme:
                extreme = x
                extreme_idx = i
            elif x / extreme - 1.0 <= -threshold:
                if extreme_idx > anchor_idx:
                    waves.append(Wave(1, anchor_idx, extreme_idx, i, float(anchor), float(extreme)))
                mode = -1
                anchor_idx = extreme_idx
                anchor = extreme
                extreme_idx = i
                extreme = x
        else:
            if x < extreme:
                extreme = x
                extreme_idx = i
            elif x / extreme - 1.0 >= threshold:
                if extreme_idx > anchor_idx:
                    waves.append(Wave(-1, anchor_idx, extreme_idx, i, float(anchor), float(extreme)))
                mode = 1
                anchor_idx = extreme_idx
                anchor = extreme
                extreme_idx = i
                extreme = x
    return waves


def parent_features(w1: Wave, w2: Wave, prices: np.ndarray) -> dict:
    denom = abs(w1.move) + abs(w2.move)
    if denom <= 0.0:
        return {}
    signed = (w2.end_price / w1.start_price - 1.0) / denom
    lo1, hi1 = sorted((w1.start_price, w1.end_price))
    lo2, hi2 = sorted((w2.start_price, w2.end_price))
    inter = max(0.0, min(hi1, hi2) - max(lo1, lo2))
    min_width = min(hi1 - lo1, hi2 - lo2)
    overlap = inter / min_width if min_width > 0.0 else 0.0
    a = max(0, w1.start_idx)
    b = min(len(prices) - 1, w2.end_idx)
    path = prices[a : b + 1]
    path_sum = float(np.nansum(np.abs(np.diff(path)))) if len(path) > 1 else np.nan
    efficiency = abs(w2.end_price - w1.start_price) / path_sum if path_sum > 0.0 else np.nan
    return {
        "signed_drift": float(signed),
        "abs_drift": float(abs(signed)),
        "overlap": float(overlap),
        "parent_eff": float(efficiency),
    }


def last_two_parent(parent_waves: list[Wave], confirm_idxs: list[int], idx: int):
    k = bisect_right(confirm_idxs, idx)
    if k < 2:
        return None
    return parent_waves[k - 2], parent_waves[k - 1]


def structural_boundary(w1: Wave, w2: Wave, parent_sign: int) -> float:
    candidates: list[tuple[int, float]] = []
    for w in (w1, w2):
        if parent_sign > 0:
            candidates.append((w.start_idx, w.start_price) if w.direction > 0 else (w.end_idx, w.end_price))
        else:
            candidates.append((w.start_idx, w.start_price) if w.direction < 0 else (w.end_idx, w.end_price))
    return max(candidates, key=lambda z: z[0])[1]


def first_passage(prices, start_idx, recovery, failure, parent_sign, horizon=HORIZON_BARS):
    end = min(len(prices) - 1, start_idx + horizon)
    for j in range(start_idx, end + 1):
        x = prices[j]
        if parent_sign > 0:
            recovered = x >= recovery
            failed = x <= failure
        else:
            recovered = x <= recovery
            failed = x >= failure
        if recovered and failed:
            return "tie", j
        if recovered:
            return "recovery", j
        if failed:
            return "failure", j
    return "censored", end


def fit_logit(train: pd.DataFrame, features: list[str]):
    x = train[features].to_numpy(float)
    y = train["y"].to_numpy(int)
    if len(train) < 20 or len(np.unique(y)) < 2:
        return None
    model = Pipeline(
        [
            ("sc", StandardScaler()),
            ("lr", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000)),
        ]
    )
    model.fit(x, y)
    return model


def eval_prob(model, frame: pd.DataFrame, features: list[str]):
    if model is None or frame.empty:
        return None
    p = model.predict_proba(frame[features].to_numpy(float))[:, 1]
    y = frame["y"].to_numpy(int)
    return {
        "n": int(len(frame)),
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "mean_p": float(np.mean(p)),
        "event_rate": float(np.mean(y)),
    }


def r1_events(prices, days, lower_waves, parent_waves, vol_ref):
    confirm = [w.confirm_idx for w in parent_waves]
    rows = []
    next_allowed = -1
    for lower in lower_waves:
        if lower.confirm_idx <= next_allowed:
            continue
        pair = last_two_parent(parent_waves, confirm, lower.confirm_idx)
        if not pair:
            continue
        pf = parent_features(*pair, prices)
        if not pf or not np.isfinite(list(pf.values())).all():
            continue
        parent_sign = 1 if pf["signed_drift"] > 0.0 else -1 if pf["signed_drift"] < 0.0 else 0
        if parent_sign == 0 or lower.direction == parent_sign:
            continue
        recovery = lower.start_price
        failure = structural_boundary(*pair, parent_sign)
        current = prices[lower.confirm_idx]
        if parent_sign > 0 and not (failure < current < recovery):
            continue
        if parent_sign < 0 and not (recovery < current < failure):
            continue
        outcome, resolved = first_passage(prices, lower.confirm_idx, recovery, failure, parent_sign)
        if outcome == "tie":
            continue
        rows.append(
            {
                "day": str(days[lower.confirm_idx]),
                "severity": abs(lower.move) / vol_ref,
                **pf,
                "outcome": outcome,
                "resolve_idx": resolved,
            }
        )
        next_allowed = resolved
    return pd.DataFrame(rows)


def local_vol_features(prices, idx):
    returns = np.diff(np.log(prices[max(0, idx - 300) : idx + 1]))
    if len(returns) < 80:
        return np.nan, np.nan
    short = float(np.std(returns[-30:], ddof=0))
    parent = float(np.std(returns[-240:], ddof=0)) if len(returns) >= 240 else float(np.std(returns, ddof=0))
    speed = abs(float(np.log(prices[idx] / prices[max(0, idx - 30)]))) / max(1, min(30, idx))
    return speed, short / parent if parent > 0.0 else np.nan


def r2_events(prices, days, parent_waves, lower_threshold, parent_threshold):
    rows = []
    next_allowed = -1
    wave_cursor = 0
    last2: list[Wave] = []
    for i, x in enumerate(prices):
        while wave_cursor < len(parent_waves) and parent_waves[wave_cursor].confirm_idx <= i:
            last2.append(parent_waves[wave_cursor])
            last2 = last2[-2:]
            wave_cursor += 1
        if i <= next_allowed or len(last2) < 2:
            continue
        pf = parent_features(last2[0], last2[1], prices)
        if not pf or not np.isfinite(list(pf.values())).all():
            continue
        points = [last2[0].start_price, last2[0].end_price, last2[1].start_price, last2[1].end_price]
        low, high = min(points), max(points)
        width = high - low
        if width <= 0.0:
            continue
        if x >= high * (1.0 + lower_threshold):
            side, edge = 1, high
        elif x <= low * (1.0 - lower_threshold):
            side, edge = -1, low
        else:
            continue
        continuation = edge * (1.0 + parent_threshold) if side > 0 else edge * (1.0 - parent_threshold)
        if (side > 0 and x >= continuation) or (side < 0 and x <= continuation):
            continue
        end = min(len(prices) - 1, i + HORIZON_BARS)
        outcome = "censored"
        resolved = end
        for j in range(i, end + 1):
            z = prices[j]
            if side > 0:
                if z <= edge:
                    outcome, resolved = "reentry", j
                    break
                if z >= continuation:
                    outcome, resolved = "continuation", j
                    break
            else:
                if z >= edge:
                    outcome, resolved = "reentry", j
                    break
                if z <= continuation:
                    outcome, resolved = "continuation", j
                    break
        speed, vol_ratio = local_vol_features(prices, i)
        outside = abs(x - edge) / edge
        rows.append(
            {
                "day": str(days[i]),
                "outside_ratio": outside / (width / edge),
                "break_speed": speed / lower_threshold if lower_threshold > 0.0 else np.nan,
                "local_vol_ratio": vol_ratio,
                **pf,
                "outcome": outcome,
                "resolve_idx": resolved,
            }
        )
        next_allowed = resolved
    return pd.DataFrame(rows)


def prepare_binary(frame: pd.DataFrame, positive_label: str):
    negative = "failure" if positive_label == "recovery" else "continuation"
    out = frame[frame["outcome"].isin([positive_label, negative])].copy()
    out["y"] = (out["outcome"] == positive_label).astype(int)
    return out.replace([np.inf, -np.inf], np.nan).dropna()


def lane_logit_summary(frame, feature_sets, positive_label):
    data = prepare_binary(frame, positive_label)
    train = data[data.day <= DEV_END].copy()
    stability = data[(data.day >= STAB_START) & (data.day <= STAB_END)].copy()
    result = {
        "n_all": int(len(data)),
        "n_dev": int(len(train)),
        "n_stability": int(len(stability)),
        "dev_rate": float(train.y.mean()) if len(train) else None,
        "stability_rate": float(stability.y.mean()) if len(stability) else None,
        "models": {},
        "annual": {},
    }
    models = {}
    for name, features in feature_sets.items():
        models[name] = fit_logit(train, features)
        result["models"][name] = eval_prob(models[name], stability, features)
    for year in (2020, 2021, 2022):
        year_frame = stability[stability.day.str.startswith(str(year))]
        result["annual"][str(year)] = {
            name: eval_prob(models[name], year_frame, features) for name, features in feature_sets.items()
        }
    return result


def daily_frame(frame: pd.DataFrame, prices: np.ndarray, parent_waves: list[Wave]):
    temp = frame.copy()
    temp["clock"] = temp["timestamp"].astype(str).str[11:16]
    daily = temp[temp.clock == "15:00"].copy().sort_values("trading_day")
    daily["ret"] = daily["close"].pct_change(fill_method=None)
    daily["rv5"] = daily["ret"].rolling(5, min_periods=5).std().shift(1)
    daily["rv20"] = daily["ret"].rolling(20, min_periods=20).std().shift(1)
    confirm = [w.confirm_idx for w in parent_waves]
    rows = []
    prev_close_idx = None
    for _, row in daily.iterrows():
        idx = int(row["_idx"])
        if prev_close_idx is None:
            prev_close_idx = idx
            continue
        pair = last_two_parent(parent_waves, confirm, prev_close_idx)
        prev_close_idx = idx
        if not pair:
            continue
        pf = parent_features(*pair, prices)
        if not pf or not np.isfinite(list(pf.values())).all():
            continue
        rv20 = float(row.rv20) if pd.notna(row.rv20) else np.nan
        rv5 = float(row.rv5) if pd.notna(row.rv5) else np.nan
        if not np.isfinite(rv20) or rv20 <= 0.0 or not np.isfinite(rv5):
            continue
        rows.append(
            {
                "day": str(row.trading_day),
                "ret": float(row.ret),
                "signed_drift": pf["signed_drift"],
                "parent_eff": pf["parent_eff"],
                "short_parent_vol": rv5 / rv20,
            }
        )
    out = pd.DataFrame(rows).sort_values("day").reset_index(drop=True)
    out["next_ret"] = out["ret"].shift(-1)
    return out.dropna().reset_index(drop=True)


def r3_summary(data: pd.DataFrame):
    features = ["signed_drift", "parent_eff", "short_parent_vol"]
    train = data[data.day <= DEV_END].copy()
    stability = data[(data.day >= STAB_START) & (data.day <= STAB_END)].copy()
    conditional = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
    conditional.fit(train[features], train.ret)
    unconditional_mean = float(train.ret.mean())
    for frame in (train, stability):
        frame["expected_cond"] = conditional.predict(frame[features])
        frame["resid_cond"] = frame.ret - frame.expected_cond
        frame["resid_uncond"] = frame.ret - unconditional_mean
    linear_cond = LinearRegression().fit(train[["resid_cond"]], train.next_ret)
    linear_uncond = LinearRegression().fit(train[["resid_uncond"]], train.next_ret)

    def snapshot(frame):
        corr_u = float(np.corrcoef(-frame.resid_uncond, frame.next_ret)[0, 1]) if len(frame) > 2 else np.nan
        corr_c = float(np.corrcoef(-frame.resid_cond, frame.next_ret)[0, 1]) if len(frame) > 2 else np.nan
        pred_u = linear_uncond.predict(frame[["resid_uncond"]])
        pred_c = linear_cond.predict(frame[["resid_cond"]])
        return {
            "n": int(len(frame)),
            "corr_reversion_unconditional": corr_u,
            "corr_reversion_conditional": corr_c,
            "mse_unconditional_linear": float(np.mean((frame.next_ret - pred_u) ** 2)),
            "mse_conditional_linear": float(np.mean((frame.next_ret - pred_c) ** 2)),
        }

    return {
        "n_dev": int(len(train)),
        "n_stability": int(len(stability)),
        "pooled": snapshot(stability),
        "annual": {
            str(year): snapshot(stability[stability.day.str.startswith(str(year))]) for year in (2020, 2021, 2022)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-sha", action="store_true")
    args = parser.parse_args()

    actual_sha = sha256(args.parquet)
    if not args.skip_sha and actual_sha != EXPECTED_SHA:
        raise RuntimeError(f"source SHA mismatch: {actual_sha}")

    columns = ["symbol", "trading_day", "timestamp", "close"]
    frame = pd.read_parquet(args.parquet, columns=columns, filters=[("trading_day", "<=", STAB_END)])
    frame = frame[frame.symbol.astype(str) == "000852.SH"].copy()
    frame["trading_day"] = frame.trading_day.astype(str)
    if frame.empty or frame.trading_day.max() > STAB_END:
        raise RuntimeError("STAGE1 stability boundary violated")
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    frame["_idx"] = np.arange(len(frame))
    prices = pd.to_numeric(frame.close, errors="coerce").to_numpy(float)
    days = frame.trading_day.to_numpy(str)
    if not np.isfinite(prices).all() or (prices <= 0.0).any():
        raise RuntimeError("invalid close values")

    clocks = frame.timestamp.astype(str).str[11:16]
    daily = frame[clocks.eq("15:00")][["trading_day", "close"]].drop_duplicates("trading_day").sort_values("trading_day")
    daily["ret"] = daily.close.pct_change(fill_method=None)
    daily["rv20"] = daily.ret.rolling(20, min_periods=20).std().shift(1)
    vol_ref = float(daily[daily.trading_day <= DEV_END].rv20.dropna().median())
    if not np.isfinite(vol_ref) or vol_ref <= 0.0:
        raise RuntimeError("invalid DEV volatility reference")

    thresholds = {"S1": 0.25 * vol_ref, "S2": 0.50 * vol_ref, "S3": 1.00 * vol_ref}
    waves = {name: detect_waves(prices, threshold) for name, threshold in thresholds.items()}
    pairings = [("S1", "S2"), ("S2", "S3")]

    receipt = {
        "schema_id": "factorlab_rmr_stage1_common_probe_receipt@1.0",
        "source_sha256": actual_sha,
        "source_rows_loaded_through_2022": int(len(frame)),
        "source_min_day": str(frame.trading_day.min()),
        "source_max_day": str(frame.trading_day.max()),
        "scientifically_fresh": False,
        "reserve_2023_2025_opened": False,
        "vol_ref_dev_median_rvol20": vol_ref,
        "directional_change_thresholds": thresholds,
        "wave_counts": {name: int(len(value)) for name, value in waves.items()},
        "R1": {},
        "R2": {},
        "R3": {},
    }

    for lower, parent in pairings:
        r1 = r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        r1_features = {
            "severity_only": ["severity"],
            "parent_state_only": ["abs_drift", "overlap", "parent_eff"],
            "parent_plus_severity": ["severity", "abs_drift", "overlap", "parent_eff"],
        }
        receipt["R1"][f"{lower}_inside_{parent}"] = lane_logit_summary(r1, r1_features, "recovery")

        r2 = r2_events(prices, days, waves[parent], thresholds[lower], thresholds[parent])
        r2_features = {
            "excursion_size_only": ["outside_ratio"],
            "parent_range_state_only": ["abs_drift", "overlap", "parent_eff"],
            "parent_plus_excursion_state": [
                "outside_ratio",
                "abs_drift",
                "overlap",
                "parent_eff",
                "break_speed",
                "local_vol_ratio",
            ],
        }
        receipt["R2"][f"{lower}_outside_{parent}"] = lane_logit_summary(r2, r2_features, "reentry")

    for parent in ("S2", "S3"):
        residual_frame = daily_frame(frame, prices, waves[parent])
        receipt["R3"][parent] = r3_summary(residual_frame)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
