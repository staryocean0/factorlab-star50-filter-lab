"""Reproduce the historical STAR50 baseline, without choosing by performance.

The eight registered candidates resolve missing volatility implementation details
against an already published 2021--2025 fingerprint. No 2026 observations or
results are inputs. Multiple matching implementations are explicitly retained;
the experiment must not claim unique identification when warmup erases a choice.

Reusable API: ``load_bars(data_dir)`` and ``baseline_frame(df)``. The latter's
default is the fingerprint-identified interpretation: log-close differences,
rolling 48-bar population standard deviation, current-close information.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from star50_filter.backtest import execute_next_open
from star50_filter.filters import butter_lowpass, hysteresis_positions

LAST_ALLOWED_DAY = "2025-12-31"
DEVELOPMENT_START = "2021-01-01"
YEARS = (2021, 2022, 2023, 2024, 2025)
INITIAL_UNVERIFIED_SPEC = {"ddof": 1, "sigma_shift": 0, "min_periods": 48}
DEFAULT_SPEC = {"ddof": 0, "sigma_shift": 0, "min_periods": 48}
REGISTERED_SPECS = [
    {"ddof": ddof, "sigma_shift": shift, "min_periods": minimum}
    for ddof, shift, minimum in itertools.product((0, 1), (0, 1), (24, 48))
]
# Transcribed only from the historical development columns, at the pinned source.
HISTORICAL = {
    "annual_2021_pct": 75.89881317090416,
    "annual_2022_pct": 74.03667883669753,
    "annual_2023_pct": 31.53381142994245,
    "annual_2024_pct": 240.9374924335716,
    "annual_2025_pct": 65.48712918654272,
    "cagr_pct": 86.75662509083047,
    "mdd_pct": -14.323804733417234,
}
REFERENCE_COMMIT = "bdbcf7dc2f613100ea7ceeb6968ab7fc2b5c9df9"
REFERENCE_PATH = "docs/research/one_hour_threshold_compare.csv"
MATCH_ATOL_PCT = 1e-8
MATCH_RTOL = 1e-10


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _array_hash(values: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<f8").tobytes()).hexdigest()


def _normalise_bars(df: pd.DataFrame) -> pd.DataFrame:
    required = {"trading_day", "open", "close"}
    if missing := required.difference(df.columns):
        raise ValueError(f"Missing input columns: {sorted(missing)}")
    days = df["trading_day"].astype(str).str[:10]
    # This exclusion happens before prices, returns, filters or strategy features
    # are inspected. Exported development carriers normally already end in 2025.
    out = df.loc[days <= LAST_ALLOWED_DAY].copy()
    if out.empty:
        raise ValueError("No allowed observations")
    out["trading_day"] = out["trading_day"].astype(str).str[:10]
    pd.to_datetime(out["trading_day"], format="%Y-%m-%d", errors="raise")
    if "symbol" in out and set(out["symbol"].astype(str)) != {"000688.SH"}:
        raise ValueError("The carrier must contain only 000688.SH")
    if "timestamp" in out:
        # Source labels use Z around Shanghai wall-clock times. Strip only the
        # suffix representation; do not convert these labels to Shanghai time.
        clock = out["timestamp"].astype(str).str[:19]
        out["timestamp"] = pd.to_datetime(clock, errors="raise")
        if out["timestamp"].duplicated().any():
            raise ValueError("Duplicate timestamps in a single-view carrier")
        if not (out["timestamp"].dt.strftime("%Y-%m-%d") == out["trading_day"]).all():
            raise ValueError("Timestamp labels disagree with trading_day")
        out = out.sort_values(["trading_day", "timestamp"], kind="stable")
    elif not out["trading_day"].is_monotonic_increasing:
        raise ValueError("Without timestamps, input must already be chronological")
    for column in ("open", "close"):
        out[column] = pd.to_numeric(out[column], errors="raise")
        values = out[column].to_numpy(dtype=float)
        if not (np.isfinite(values) & (values > 0)).all():
            raise ValueError(f"Nonpositive/nonfinite {column} prices")
    out = out.reset_index(drop=True)
    out["year"] = out["trading_day"].str[:4].astype(int)
    out["is_development"] = out["year"].isin(YEARS)
    return out


def load_bars(data_dir: str | Path, view: str = "5m_offset_0") -> pd.DataFrame:
    """Load one carrier, preferring Parquet and allowing CSV/CSV.gz exports."""
    directory = Path(data_dir)
    paths = [directory / f"{view}{suffix}" for suffix in (".parquet", ".csv.gz", ".csv")]
    source = next((path for path in paths if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"No {view} carrier in {directory}; tried {paths}")
    if source.suffix == ".parquet":
        raw = pd.read_parquet(source, filters=[("trading_day", "<=", LAST_ALLOWED_DAY)])
    else:
        raw = pd.read_csv(source)
    out = _normalise_bars(raw)
    out.attrs.update({
        "source_path": str(source.resolve()),
        "source_sha256": _sha256(source),
        "latest_allowed_day": LAST_ALLOWED_DAY,
        "view": view,
    })
    return out


def baseline_frame(
    df: pd.DataFrame,
    ddof: int = 0,
    sigma_shift: int = 0,
    min_periods: int = 48,
) -> pd.DataFrame:
    """Build the original next-open log-account baseline, including 2020 warmup.

    ``exec_pos[i]`` belongs to the completed open[i-1] -> open[i] interval.
    ``signal_pos[i]`` is known at close[i] and earns its first return at i+2.
    NAV and drawdown reset to 1 / 0 at the development boundary; indicator and
    signal state continue from the available pre-2021 warmup observations.
    """
    if ddof not in (0, 1) or sigma_shift not in (0, 1):
        raise ValueError("Only the preregistered ddof/shift interpretations are allowed")
    if min_periods not in (24, 48):
        raise ValueError("Only preregistered min_periods=24 or 48 is allowed")
    out = _normalise_bars(df)
    out.attrs.update(df.attrs)
    out["log_close"] = np.log(out["close"].to_numpy(dtype=float))
    out["lowpass"] = butter_lowpass(out["log_close"].to_numpy(), period_bars=12, order=1)
    differences = out["log_close"].diff()
    out["sigma"] = differences.rolling(48, min_periods=min_periods).std(ddof=ddof).shift(sigma_shift)
    out["threshold"] = out["sigma"]  # k=1; sigma is per 5m return, no sqrt(48).
    out["signal_pos"] = hysteresis_positions(out["lowpass"].to_numpy(), out["threshold"].to_numpy())
    position, pnl = execute_next_open(out["signal_pos"].to_numpy(), out["open"].to_numpy())
    out["exec_pos"] = position
    out["pnl_log"] = pnl
    out["open_log_return"] = np.r_[0.0, np.diff(np.log(out["open"].to_numpy()))]
    dev = out["is_development"]
    nav = np.exp(np.cumsum(out.loc[dev, "pnl_log"].to_numpy()))
    high_water = np.maximum.accumulate(np.r_[1.0, nav])[1:]
    out["nav"] = np.nan
    out["drawdown"] = np.nan
    out.loc[dev, "nav"] = nav
    out.loc[dev, "drawdown"] = nav / high_water - 1.0
    out.attrs["baseline_spec"] = {"ddof": ddof, "sigma_shift": sigma_shift, "min_periods": min_periods}
    return out


def fingerprint(frame: pd.DataFrame) -> dict[str, float]:
    """Calendar-year geometric metrics for the five development years only."""
    dev = frame.loc[frame["is_development"]]
    if set(dev["year"].unique()) != set(YEARS):
        raise ValueError("Fingerprint requires all five development years")
    annual_log = dev.groupby("year")["pnl_log"].sum()
    result = {f"annual_{year}_pct": float(100 * np.expm1(annual_log.loc[year])) for year in YEARS}
    result["cagr_pct"] = float(100 * np.expm1(dev["pnl_log"].sum() / 5.0))
    result["mdd_pct"] = float(100 * dev["drawdown"].min())
    return result


def _candidate_id(spec: dict[str, int]) -> str:
    return f"ddof{spec['ddof']}_shift{spec['sigma_shift']}_min{spec['min_periods']}"


def reproduce(data_dir: str | Path, output_dir: str | Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    protocol = {
        "schema": "star50_historical_baseline_reproduction@1",
        "purpose": "missing-implementation fingerprint identification; never performance ranking",
        "source_commit": REFERENCE_COMMIT,
        "historical_reference_path": REFERENCE_PATH,
        "reference_row": "vol_k1",
        "data_roles": {"2020": "warmup", "2021-2025": "consumed development", "2026": "excluded"},
        "frozen_policy": {"view": "5m_offset_0", "period_bars": 12, "butter_order": 1, "hysteresis_k": 1},
        "sigma": "rolling48 std of log-close first differences, unscaled per-bar sigma",
        "candidates": REGISTERED_SPECS,
        "historical_fingerprint": HISTORICAL,
        "match_tolerance_pct": {"atol": MATCH_ATOL_PCT, "rtol": MATCH_RTOL},
        "account": "zero-cost signed-log index-point research account",
        "execution": "close t decision; open t+1 fill; open t+2 first return booking",
        "mdd": "development-only geometric NAV, initial equity=1 included in high-water mark",
        "cagr": "exp(sum(development log pnl) / 5 calendar years) - 1",
        "initial_unverified_spec": INITIAL_UNVERIFIED_SPEC,
        "replay_default_spec": DEFAULT_SPEC,
        "equivalent_startup_convention": "Prefer the full 48-observation window only among identical matching development paths",
        "availability_assumption": "Research replay assumes each OHLC bar is available at its close; source available_at is audited separately and is not silently overwritten",
        "fresh_oos": False,
        "production_authority": False,
        "source_hashes": {str(p.relative_to(ROOT)): _sha256(p) for p in (
            Path(__file__), ROOT / "src/star50_filter/filters.py", ROOT / "src/star50_filter/backtest.py"
        )},
    }
    # Persist the candidate set before any strategy computation.
    protocol_path = output / "reproduction_protocol.json"
    protocol_path.write_text(json.dumps(protocol, indent=2) + "\n")
    df = load_bars(data_dir)
    if df["trading_day"].min() >= DEVELOPMENT_START:
        raise ValueError("Pre-2021 warmup is required for historical reproduction")
    availability = {"source_field_present": "available_at" in df,
                    "bar_close_replay_is_an_assumption": True,
                    "source_available_at_modified": False}
    if "available_at" in df and "timestamp" in df:
        available = pd.to_datetime(df["available_at"], utc=True, errors="raise").dt.tz_convert("Asia/Shanghai").dt.tz_localize(None)
        late = available > df["timestamp"]
        availability.update({
            "source_rows_available_after_assumed_decision": int(late.sum()),
            "development_rows_available_after_assumed_decision": int((late & df["is_development"]).sum()),
            "source_local_availability_clocks": sorted(available.dt.strftime("%H:%M:%S").unique().tolist()),
            "actual_source_availability_passes_bar_close_contract": not bool(late.any()),
            "status": "source_availability_gap" if late.any() else "source_field_consistent_with_assumed_decision",
        })
    rows, frames = [], {}
    for spec in REGISTERED_SPECS:
        candidate = _candidate_id(spec)
        frame = baseline_frame(df, **spec)
        observed = fingerprint(frame)
        deltas = {key: observed[key] - expected for key, expected in HISTORICAL.items()}
        tolerances = {key: MATCH_ATOL_PCT + MATCH_RTOL * abs(value) for key, value in HISTORICAL.items()}
        dev = frame.loc[frame["is_development"]]
        row = {"candidate_id": candidate, **spec, **observed,
               **{f"delta_{key}": delta for key, delta in deltas.items()},
               "matches_historical": all(abs(deltas[key]) <= tolerances[key] for key in HISTORICAL),
               "max_normalized_residual": max(abs(deltas[key]) / tolerances[key] for key in HISTORICAL),
               "development_position_sha256": _array_hash(dev["exec_pos"].to_numpy()),
               "development_pnl_sha256": _array_hash(dev["pnl_log"].to_numpy()),
               "development_invalid_sigma_count": int((~np.isfinite(dev["sigma"])).sum())}
        rows.append(row)
        frames[candidate] = frame
    matrix = pd.DataFrame(rows)
    matrix_path = output / "reproduction_fingerprints.csv"
    matrix.to_csv(matrix_path, index=False)
    matched = [row for row in rows if row["matches_historical"]]
    default_id = _candidate_id(DEFAULT_SPEC)
    matched_ids = [row["candidate_id"] for row in matched]
    path_groups = {row["development_pnl_sha256"] for row in matched}
    if not matched:
        status = "no_registered_implementation_matches"
    elif len(matched) == 1:
        status = "unique_registered_implementation_matches"
    elif len(path_groups) == 1:
        status = "multiple_implementations_same_development_path"
    else:
        status = "multiple_fingerprint_matches_different_paths"
    # Convention resolves only algebraically/account-identical matches; it never
    # selects a better-performing mismatch or breaks a different-path ambiguity.
    selected_id = None
    if len(matched) == 1:
        selected_id = matched_ids[0]
    elif matched and len(path_groups) == 1:
        selected_id = default_id if default_id in matched_ids else matched_ids[0]
    result = {
        "schema": "star50_historical_baseline_reproduction_result@1",
        "status": status,
        "registered_implementation_count": len(rows),
        "matched_candidate_ids": matched_ids,
        "matched_development_path_count": len(path_groups),
        "selected_equivalent_replay_id": selected_id,
        "default_matches_historical": default_id in matched_ids,
        "initial_unverified_spec_matches_historical": _candidate_id(INITIAL_UNVERIFIED_SPEC) in matched_ids,
        "availability_audit": availability,
        "identification_limit": "min_periods and startup details may be unidentifiable after 2020 warmup",
        "input": {**df.attrs, "rows": len(df), "first_day": df["trading_day"].min(), "last_day": df["trading_day"].max()},
        "protocol_sha256": _sha256(protocol_path),
        "fingerprints_sha256": _sha256(matrix_path),
        "fresh_oos": False,
        "production_authority": False,
    }
    if selected_id is not None:
        selected = frames[selected_id]
        # The replay artifact keeps warmup rows explicitly labelled. All prices
        # are already restricted to <=2025, including these warmup rows.
        frame_path = output / "reproduced_baseline_frame.csv.gz"
        selected.to_csv(frame_path, index=False, compression={"method": "gzip", "mtime": 0})
        result["reproduced_frame_path"] = str(frame_path)
        result["reproduced_frame_sha256"] = _sha256(frame_path)
        result["reproduced_spec"] = selected.attrs["baseline_spec"]
        result["observed_fingerprint"] = fingerprint(selected)
    (output / "reproduction_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/drawdown_conditions/baseline_reproduction")
    args = parser.parse_args()
    result = reproduce(args.data_dir, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
