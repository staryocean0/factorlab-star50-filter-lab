"""Past-only multi-scale volatility forecast prototype; no trading actions."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FLOOR = 1e-12
RAW_SHOCK = 0.0029036229356317277
FEATURES = ["log_rv5", "log_rv30", "log_rv480", "body_scale", "gap_scale"] + [f"clock_{j}" for j in range(1, 8)]


def past_features(frame):
    f = frame.copy().reset_index(drop=True)
    t = pd.to_datetime(f.timestamp)
    if t.dt.tz is None or t.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError("strict increasing timezone-aware history required")
    t = t.dt.tz_convert("Asia/Shanghai")
    minutes = t.dt.hour * 60 + t.dt.minute
    slot = np.where(minutes < 720, minutes - 570, minutes - 780)
    if not np.all((slot >= 1) & (slot <= 120)):
        raise ValueError("invalid session close clock")
    f["session_slot"] = slot
    f["day"] = t.dt.strftime("%Y-%m-%d")
    f["year"] = t.dt.year
    f["session"] = (minutes >= 780).astype(int)
    f["clock"] = t.dt.strftime("%H:%M")
    square = pd.to_numeric(f.r, errors="raise").pow(2)
    for w in [5, 15, 30, 480]:
        f[f"past_var_{w}"] = square.rolling(w, min_periods=int(np.ceil(0.8 * w))).mean()
    for w in [5, 30, 480]:
        f[f"log_rv{w}"] = np.log(f[f"past_var_{w}"].clip(lower=FLOOR))
    scale = np.sqrt(f.past_var_480.clip(lower=FLOOR))
    f["body_scale"] = np.log1p(f.body.abs() / scale)
    f["gap_scale"] = np.log1p(f.gap.abs().where(f.boundary, 0) / scale)
    clock_bin = ((slot - 1) // 30) + 4 * f.session.to_numpy()
    for j in range(1, 8):
        f[f"clock_{j}"] = (clock_bin == j).astype(float)
    shock = (
        np.maximum.reduce([f.r.fillna(0).abs().to_numpy(), f.body.abs().to_numpy(), f.gap.abs().where(f.boundary, 0).fillna(0).to_numpy()])
        > RAW_SHOCK
    )
    f["recent_shock5"] = (
        pd.Series(shock.astype(float)).groupby([f.day, f.session]).transform(lambda s: s.rolling(5, min_periods=1).max()).astype(bool)
    )
    f["features_ready"] = np.isfinite(f[FEATURES].to_numpy()).all(axis=1) & (np.arange(len(f)) >= 480)
    return f


def future_variance(features, horizon):
    if horizon not in [5, 15, 30]:
        raise ValueError("unsupported horizon")
    return (
        features.r.pow(2)
        .groupby([features.day, features.session])
        .transform(lambda s: s.rolling(horizon, min_periods=horizon).mean().shift(-horizon))
    )


@dataclass
class VolatilityModel:
    symbol: str
    horizon: int
    mean: np.ndarray
    scale: np.ndarray
    coefficient: np.ndarray
    residuals: np.ndarray
    state_edges: np.ndarray
    clock_variance: dict

    def raw_log_forecast(self, features):
        x = features[FEATURES].to_numpy(float)
        z = (x - self.mean) / self.scale
        return self.coefficient[0] + z @ self.coefficient[1:]

    def predict_features(self, features):
        if set(features.symbol) != {self.symbol}:
            raise ValueError("model/instrument identity mismatch")
        valid = features.features_ready.to_numpy() & (features.session_slot.to_numpy() + self.horizon <= 120)
        mu = self.raw_log_forecast(features)
        residual = self.residuals
        smear = float(np.mean(np.exp(residual)))
        point = np.sqrt(np.exp(mu) * smear)
        lo, hi = np.quantile(residual, [0.1, 0.9])
        out = pd.DataFrame(
            {
                "timestamp": features.timestamp,
                "forecast_available": valid,
                "forecast_sigma": np.where(valid, point, np.nan),
                "sigma_p10": np.where(valid, np.exp((mu + lo) / 2), np.nan),
                "sigma_p90": np.where(valid, np.exp((mu + hi) / 2), np.nan),
            }
        )

        def probability(log_threshold):
            q = (len(residual) - np.searchsorted(residual, log_threshold - mu, side="right")) / len(residual)
            return np.where(valid, q, np.nan)

        out["p_future_high"] = probability(np.log(max(self.state_edges[1] ** 2, FLOOR)))
        past = features[f"past_var_{self.horizon}"].to_numpy(float)
        out["predicted_sigma_ratio"] = np.where(valid, point / np.sqrt(np.maximum(past, FLOOR)), np.nan)
        out["forecast_bucket"] = np.where(
            valid, np.asarray(["low", "medium", "high"])[np.searchsorted(self.state_edges, point, side="right")], "unavailable"
        )
        for k in [2, 3, 4]:
            out[f"p_amplify_{k}"] = probability(np.log(np.maximum(k * k * np.maximum(past, FLOOR), self.state_edges[1] ** 2)))
        return out

    def save(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=False)
        np.savez(
            path / "parameters.npz",
            mean=self.mean,
            scale=self.scale,
            coefficient=self.coefficient,
            residuals=self.residuals,
            state_edges=self.state_edges,
        )
        (path / "model.json").write_text(
            json.dumps(
                {
                    "schema_id": "causal_volatility_model@1.0",
                    "symbol": self.symbol,
                    "horizon": self.horizon,
                    "features": FEATURES,
                    "clock_variance": self.clock_variance,
                    "fit_years": [2021, 2022],
                    "calibration_year": 2023,
                    "production_authority": False,
                },
                indent=2,
            )
            + "\n"
        )

    @classmethod
    def load(cls, path):
        path = Path(path)
        meta = json.loads((path / "model.json").read_text())
        if meta["features"] != FEATURES or meta["production_authority"] is not False:
            raise ValueError("model contract mismatch")
        with np.load(path / "parameters.npz", allow_pickle=False) as f:
            return cls(
                meta["symbol"],
                meta["horizon"],
                f["mean"],
                f["scale"],
                f["coefficient"],
                f["residuals"],
                f["state_edges"],
                meta["clock_variance"],
            )


def fit_model(features, horizon):
    y = future_variance(features, horizon)
    valid = features.features_ready & y.notna()
    train = valid & features.year.isin([2021, 2022])
    cal = valid & (features.year == 2023)
    if train.sum() < 200 or cal.sum() < 200:
        raise ValueError("insufficient fit/calibration history")
    x = features.loc[train, FEATURES].to_numpy(float)
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    z = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    penalty = np.eye(z.shape[1])
    penalty[0, 0] = 0
    coefficient = np.linalg.solve(z.T @ z + penalty, z.T @ np.log(y.loc[train].clip(lower=FLOOR).to_numpy()))
    model = VolatilityModel(str(features.symbol.iloc[0]), horizon, mean, scale, coefficient, np.array([]), np.array([]), {})
    residual = np.log(y.loc[cal].clip(lower=FLOOR)) - model.raw_log_forecast(features.loc[cal])
    model.residuals = np.sort(residual.to_numpy())
    model.state_edges = np.sqrt(y.loc[cal]).quantile([1 / 3, 2 / 3]).to_numpy()
    tmp = pd.DataFrame({"clock": features.loc[train, "clock"], "variance": y.loc[train]})
    model.clock_variance = {str(k): float(v) for k, v in tmp.groupby("clock").variance.mean().items()}
    return model, y


def forecast_latest(history, model):
    """Research interface using a past-only prefix; refuses cross-session horizons."""
    out = model.predict_features(past_features(history)).iloc[-1]
    if not out.forecast_available:
        raise ValueError("insufficient history or horizon crosses session")
    return {"symbol": model.symbol, "horizon_minutes": model.horizon, **out.to_dict(), "production_authority": False}


def event_metrics(actual, alert):
    y = np.asarray(actual, bool)
    a = np.asarray(alert, bool)
    hit = int((y & a).sum())
    n = len(y)
    return {
        "rows": n,
        "events": int(y.sum()),
        "alerts": int(a.sum()),
        "hits": hit,
        "precision": hit / int(a.sum()) if a.any() else None,
        "recall": hit / int(y.sum()) if y.any() else None,
        "alert_time_share": float(a.mean()) if n else None,
        "false_positive_rate": float(a[~y].mean()) if (~y).any() else None,
    }
