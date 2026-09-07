#!/usr/bin/env python3
"""Frozen post-shock state calibration V2.

Consumed-history risk-state measurement only. No trading, no returns/P&L output,
no 2026 reads, no model/threshold tuning, and no online Clean promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from star50_filter.cloud_market_data import load_market_data

PROTOCOL_VERSION = "post_shock_state_calibration_v2"
SEED = 20260908
BOOTSTRAP_DRAWS = 2000
CHECKPOINTS = (5, 10, 15, 20)
HORIZONS = (5, 10)
SYMBOLS = ("000688.SH", "000852.SH")
EXPECTED_EVENTS = {"000688.SH": 52, "000852.SH": 25}
STATE_ORDER = ("LOW_CANDIDATE", "RECOVERING", "UNSAFE")
DENOM_MIN_ROWS = 10
DENOM_MIN_EVENTS = 3
ENGINE_PATH = Path("docs/research/first_shock_gate_v1/code/first_shock_gate.py")
ENGINE_SHA256 = "e67f2ecfb8ad7e38b0e38cd6abb37304a320a1972b0030739e8f602e214f1306"
ENGINE_GIT_BLOB = "18ec71c64ba441460a221dfcc59b97080a026d81"
PROTOCOL_PATH = Path("docs/research/post_shock_state_calibration_v2/FROZEN_PROTOCOL.md")


class CalibrationError(RuntimeError):
    """Fail-closed scientific intake or invariant error."""


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_frozen_engine(root: str | Path):
    root = Path(root).resolve()
    path = root / ENGINE_PATH
    if not path.is_file():
        raise CalibrationError(f"missing inherited first-shock engine: {path}")
    digest = file_sha256(path)
    if digest != ENGINE_SHA256:
        raise CalibrationError(
            f"inherited first-shock engine drift: actual={digest} expected={ENGINE_SHA256}"
        )
    name = "_frozen_first_shock_gate_v1_for_state_calibration"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CalibrationError("cannot import frozen first-shock engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def state_from_ratio(value: float) -> str | None:
    if not np.isfinite(value):
        return None
    if value < 0:
        raise CalibrationError(f"risk ratio must be non-negative, got {value}")
    if value < 1.0:
        return "LOW_CANDIDATE"
    if value < 1.5:
        return "RECOVERING"
    return "UNSAFE"


def rms_window(returns_bp: np.ndarray, end_minute: int, width: int = 5) -> float:
    """RMS of the `width` returns ending at 1-based `end_minute`.

    A window is observed only when every required return is finite. Session
    boundaries are never bridged.
    """
    r = np.asarray(returns_bp, dtype=float)
    if width < 1 or end_minute < width or end_minute > len(r):
        return float("nan")
    block = r[end_minute - width:end_minute]
    if len(block) != width or not np.isfinite(block).all():
        return float("nan")
    return float(np.sqrt(np.mean(block * block)))


def build_checkpoint_surface(root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Reconstruct the sealed 2024-2025 first-event universe and checkpoints."""
    root = Path(root).resolve()
    engine = load_frozen_engine(root)
    rows: list[dict[str, Any]] = []
    event_counts: dict[str, int] = {}

    for symbol in SYMBOLS:
        native = load_market_data(
            symbol, "1m", "2024-01-01", "2025-12-31", root=root
        )
        if native.empty:
            raise CalibrationError(f"empty bounded 1m surface for {symbol}")
        if set(native.trading_day.str[:4].astype(int)) - {2024, 2025}:
            raise CalibrationError(f"unexpected year in {symbol} bounded source")
        panel = engine.minute_panel(native, symbol)
        features = engine.make_features(panel)
        events = features.loc[
            features["first"].eq(1.0) & features["year"].isin([2024, 2025])
        ].copy()
        event_counts[symbol] = int(len(events))
        if event_counts[symbol] != EXPECTED_EVENTS[symbol]:
            raise CalibrationError(
                "inherited_checkpoint_surface_not_reproducible: "
                f"{symbol} first-event count={event_counts[symbol]} "
                f"expected={EXPECTED_EVENTS[symbol]}"
            )

        session_groups = {
            str(key): part.sort_values("minute", kind="stable").reset_index(drop=True)
            for key, part in features.groupby("session", sort=False)
        }
        for _, event in events.sort_values(["session", "minute"], kind="stable").iterrows():
            session = str(event["session"])
            g = session_groups[session]
            minute = int(event["minute"])
            sigma_pre = float(event["sigma_pre"])
            if not np.isfinite(sigma_pre) or sigma_pre <= 0:
                raise CalibrationError(f"event has invalid sigma_pre: {symbol} {session} m{minute}")
            event_id = f"{symbol}|{session}|m{minute:03d}"
            returns = g["return_bp"].to_numpy(float)
            year = int(event["year"])
            if year not in (2024, 2025):
                raise CalibrationError("event year escaped frozen 2024-2025 scope")

            for checkpoint in CHECKPOINTS:
                endpoint = minute + checkpoint
                current_rms = rms_window(returns, endpoint)
                current_ratio = (
                    float(current_rms / sigma_pre) if np.isfinite(current_rms) else float("nan")
                )
                item: dict[str, Any] = {
                    "event_id": event_id,
                    "symbol": symbol,
                    "year": year,
                    "session": session,
                    "event_minute": minute,
                    "checkpoint_min": checkpoint,
                    "sigma_pre": sigma_pre,
                    "current_ratio": current_ratio,
                    "current_state": state_from_ratio(current_ratio),
                    "current_observed": bool(np.isfinite(current_ratio)),
                }
                for horizon in HORIZONS:
                    future_rms = rms_window(returns, endpoint + horizon)
                    future_ratio = (
                        float(future_rms / sigma_pre)
                        if np.isfinite(future_rms)
                        else float("nan")
                    )
                    item[f"future_ratio_{horizon}"] = future_ratio
                    item[f"future_state_{horizon}"] = state_from_ratio(future_ratio)
                    item[f"eligible_{horizon}"] = bool(
                        np.isfinite(current_ratio) and np.isfinite(future_ratio)
                    )
                rows.append(item)

    surface = pd.DataFrame(rows)
    expected_rows = sum(EXPECTED_EVENTS.values()) * len(CHECKPOINTS)
    if len(surface) != expected_rows:
        raise CalibrationError(f"checkpoint row mismatch: {len(surface)} != {expected_rows}")
    if surface.duplicated(["event_id", "checkpoint_min"]).any():
        raise CalibrationError("duplicate (event_id, checkpoint_min)")
    if set(surface.checkpoint_min.unique()) - set(CHECKPOINTS):
        raise CalibrationError("unexpected checkpoint")
    if set(surface.year.unique()) - {2024, 2025}:
        raise CalibrationError("unexpected year in checkpoint surface")
    if set(surface.symbol.unique()) - set(SYMBOLS):
        raise CalibrationError("unexpected symbol in checkpoint surface")

    receipt = {
        "event_counts": event_counts,
        "checkpoint_rows": int(len(surface)),
        "checkpoints": list(CHECKPOINTS),
        "horizons": list(HORIZONS),
        "engine_path": str(ENGINE_PATH),
        "engine_sha256": ENGINE_SHA256,
        "engine_git_blob": ENGINE_GIT_BLOB,
    }
    return surface, receipt


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n < 0 or successes < 0 or successes > n:
        raise CalibrationError("invalid binomial counts")
    if n == 0:
        return float("nan"), float("nan")
    phat = successes / n
    den = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / den
    half = z * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n)) / den
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def _group_key_values(symbol: str | None, year: int | None) -> dict[str, Any]:
    return {
        "symbol": symbol if symbol is not None else "ALL",
        "year": int(year) if year is not None else "ALL",
    }


def state_risk_table(surface: pd.DataFrame) -> pd.DataFrame:
    out: list[dict[str, Any]] = []
    scopes: list[tuple[str | None, int | None, pd.DataFrame]] = [(None, None, surface)]
    for (symbol, year), part in surface.groupby(["symbol", "year"], sort=True):
        scopes.append((str(symbol), int(year), part))

    for symbol, year, part in scopes:
        for horizon in HORIZONS:
            eligible = part.loc[part[f"eligible_{horizon}"].astype(bool)].copy()
            for state in STATE_ORDER:
                cell = eligible.loc[eligible.current_state.eq(state)].copy()
                future_unsafe = cell[f"future_state_{horizon}"].eq("UNSAFE")
                n = int(len(cell))
                k = int(future_unsafe.sum())
                events = int(cell.event_id.nunique())
                lo, hi = wilson_interval(k, n)
                future = cell[f"future_ratio_{horizon}"].to_numpy(float)
                row = {
                    **_group_key_values(symbol, year),
                    "horizon_min": horizon,
                    "current_state": state,
                    "n": n,
                    "distinct_events": events,
                    "future_unsafe_n": k,
                    "future_unsafe_probability": float(k / n) if n else float("nan"),
                    "wilson95_low_row_level": lo,
                    "wilson95_high_row_level": hi,
                    "future_ratio_q25": float(np.quantile(future, 0.25)) if n else float("nan"),
                    "future_ratio_median": float(np.quantile(future, 0.50)) if n else float("nan"),
                    "future_ratio_q75": float(np.quantile(future, 0.75)) if n else float("nan"),
                    "denominator_sufficient": bool(n >= DENOM_MIN_ROWS and events >= DENOM_MIN_EVENTS),
                }
                out.append(row)
    return pd.DataFrame(out)


def transition_table(surface: pd.DataFrame) -> pd.DataFrame:
    out: list[dict[str, Any]] = []
    scopes: list[tuple[str | None, int | None, pd.DataFrame]] = [(None, None, surface)]
    for (symbol, year), part in surface.groupby(["symbol", "year"], sort=True):
        scopes.append((str(symbol), int(year), part))
    for symbol, year, part in scopes:
        for horizon in HORIZONS:
            eligible = part.loc[part[f"eligible_{horizon}"].astype(bool)]
            for current in STATE_ORDER:
                src = eligible.loc[eligible.current_state.eq(current)]
                denom = int(len(src))
                events = int(src.event_id.nunique())
                for future in STATE_ORDER:
                    count = int(src[f"future_state_{horizon}"].eq(future).sum())
                    out.append({
                        **_group_key_values(symbol, year),
                        "horizon_min": horizon,
                        "current_state": current,
                        "future_state": future,
                        "count": count,
                        "current_state_n": denom,
                        "distinct_events": events,
                        "transition_probability": float(count / denom) if denom else float("nan"),
                    })
    return pd.DataFrame(out)


def elapsed_time_table(surface: pd.DataFrame) -> pd.DataFrame:
    out: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        eligible = surface.loc[surface[f"eligible_{horizon}"].astype(bool)]
        for state in STATE_ORDER:
            state_rows = eligible.loc[eligible.current_state.eq(state)]
            for checkpoint in CHECKPOINTS:
                cell = state_rows.loc[state_rows.checkpoint_min.eq(checkpoint)]
                n = int(len(cell))
                events = int(cell.event_id.nunique())
                k = int(cell[f"future_state_{horizon}"].eq("UNSAFE").sum())
                lo, hi = wilson_interval(k, n)
                out.append({
                    "horizon_min": horizon,
                    "current_state": state,
                    "checkpoint_min": checkpoint,
                    "n": n,
                    "distinct_events": events,
                    "future_unsafe_n": k,
                    "future_unsafe_probability": float(k / n) if n else float("nan"),
                    "wilson95_low_row_level": lo,
                    "wilson95_high_row_level": hi,
                    "denominator_sufficient": bool(n >= DENOM_MIN_ROWS and events >= DENOM_MIN_EVENTS),
                })
    return pd.DataFrame(out)


def _prob_unsafe(frame: pd.DataFrame, horizon: int, state: str) -> float:
    cell = frame.loc[frame.current_state.eq(state)]
    if cell.empty:
        return float("nan")
    return float(cell[f"future_state_{horizon}"].eq("UNSAFE").mean())


def cluster_bootstrap_contrasts(surface: pd.DataFrame) -> pd.DataFrame:
    """Event-cluster bootstrap for pooled state-risk contrasts."""
    rng = np.random.default_rng(SEED)
    out: list[dict[str, Any]] = []
    for horizon in HORIZONS:
        eligible = surface.loc[surface[f"eligible_{horizon}"].astype(bool)].copy()
        event_ids = np.array(sorted(eligible.event_id.unique()), dtype=object)
        if len(event_ids) < 2:
            raise CalibrationError("insufficient distinct events for cluster bootstrap")
        points = {
            "UNSAFE-minus-LOW_CANDIDATE": _prob_unsafe(eligible, horizon, "UNSAFE") - _prob_unsafe(eligible, horizon, "LOW_CANDIDATE"),
            "RECOVERING-minus-LOW_CANDIDATE": _prob_unsafe(eligible, horizon, "RECOVERING") - _prob_unsafe(eligible, horizon, "LOW_CANDIDATE"),
        }
        draws = {key: [] for key in points}
        grouped = {key: value for key, value in eligible.groupby("event_id", sort=False)}
        for _ in range(BOOTSTRAP_DRAWS):
            sampled = rng.choice(event_ids, size=len(event_ids), replace=True)
            boot = pd.concat([grouped[event_id] for event_id in sampled], ignore_index=True)
            p_low = _prob_unsafe(boot, horizon, "LOW_CANDIDATE")
            p_rec = _prob_unsafe(boot, horizon, "RECOVERING")
            p_unsafe = _prob_unsafe(boot, horizon, "UNSAFE")
            if np.isfinite(p_low) and np.isfinite(p_unsafe):
                draws["UNSAFE-minus-LOW_CANDIDATE"].append(p_unsafe - p_low)
            if np.isfinite(p_low) and np.isfinite(p_rec):
                draws["RECOVERING-minus-LOW_CANDIDATE"].append(p_rec - p_low)
        for contrast, values in draws.items():
            arr = np.asarray(values, dtype=float)
            out.append({
                "horizon_min": horizon,
                "contrast": contrast,
                "point_difference": float(points[contrast]),
                "bootstrap_draws_requested": BOOTSTRAP_DRAWS,
                "bootstrap_draws_valid": int(len(arr)),
                "cluster_unit": "event_id",
                "seed": SEED,
                "bootstrap95_low": float(np.quantile(arr, 0.025)) if len(arr) else float("nan"),
                "bootstrap95_high": float(np.quantile(arr, 0.975)) if len(arr) else float("nan"),
            })
    return pd.DataFrame(out)


def _monotone_probabilities(rows: pd.DataFrame) -> bool:
    keyed = {str(r.current_state): float(r.future_unsafe_probability) for _, r in rows.iterrows()}
    if any(state not in keyed or not np.isfinite(keyed[state]) for state in STATE_ORDER):
        return False
    return bool(keyed["LOW_CANDIDATE"] <= keyed["RECOVERING"] <= keyed["UNSAFE"])


def adjudicate(risk: pd.DataFrame, elapsed: pd.DataFrame) -> dict[str, Any]:
    pooled_checks = []
    for horizon in HORIZONS:
        rows = risk.loc[(risk.symbol == "ALL") & (risk.year == "ALL") & (risk.horizon_min == horizon)]
        pooled_checks.append({
            "horizon_min": horizon,
            "monotone": _monotone_probabilities(rows),
            "all_states_present": bool((rows.n > 0).all() and len(rows) == len(STATE_ORDER)),
        })

    strata: list[dict[str, Any]] = []
    nonpooled = risk.loc[~((risk.symbol == "ALL") & (risk.year == "ALL"))]
    for (symbol, year, horizon), rows in nonpooled.groupby(["symbol", "year", "horizon_min"], sort=True):
        sufficient = {
            str(r.current_state): bool(r.denominator_sufficient) for _, r in rows.iterrows()
        }
        all_sufficient = all(sufficient.get(state, False) for state in STATE_ORDER)
        strata.append({
            "symbol": str(symbol),
            "year": int(year),
            "horizon_min": int(horizon),
            "all_three_states_denominator_sufficient": bool(all_sufficient),
            "monotone_if_testable": _monotone_probabilities(rows) if all_sufficient else None,
        })

    pooled_ok = all(item["monotone"] and item["all_states_present"] for item in pooled_checks)
    every_stratum_testable = bool(strata) and all(item["all_three_states_denominator_sufficient"] for item in strata)
    any_nonmonotone_testable = any(
        item["all_three_states_denominator_sufficient"] and item["monotone_if_testable"] is False
        for item in strata
    )
    if not pooled_ok:
        status = "state_calibration_not_supported"
    elif every_stratum_testable and not any_nonmonotone_testable:
        status = "state_calibration_supported"
    else:
        status = "state_calibration_partially_supported"

    residual: list[dict[str, Any]] = []
    for (horizon, state), rows in elapsed.groupby(["horizon_min", "current_state"], sort=True):
        usable = rows.loc[rows.denominator_sufficient.astype(bool) & rows.future_unsafe_probability.notna()]
        if len(usable) >= 2:
            spread = float(usable.future_unsafe_probability.max() - usable.future_unsafe_probability.min())
        else:
            spread = float("nan")
        residual.append({
            "horizon_min": int(horizon),
            "current_state": str(state),
            "sufficient_checkpoint_cells": int(len(usable)),
            "max_minus_min_future_unsafe_probability": spread,
            "residual_descriptive_information": bool(np.isfinite(spread) and spread >= 0.10),
        })

    return {
        "protocol_version": PROTOCOL_VERSION,
        "adjudication": status,
        "pooled_monotonicity": pooled_checks,
        "symbol_year_stability": strata,
        "elapsed_time_secondary": residual,
        "clean_transition_validated": False,
        "morphology_replication_status_changed": False,
    }


def relevant_manifest_entries(root: Path) -> tuple[str, list[dict[str, Any]]]:
    manifest_path = root / "data/cross_index_risk_gate_v1/manifest.json"
    if not manifest_path.is_file():
        raise CalibrationError("missing bounded 1m manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = []
    for item in manifest.get("files", []):
        if item.get("symbol") in SYMBOLS and item.get("frequency") == "1m":
            first = str(item.get("first_day", ""))
            last = str(item.get("last_day", ""))
            if last >= "2024-01-01" and first <= "2025-12-31":
                entries.append({key: item.get(key) for key in (
                    "symbol", "frequency", "first_day", "last_day", "path", "sha256", "rows"
                ) if key in item})
    if not entries:
        raise CalibrationError("no relevant 2024-2025 1m manifest entries")
    return file_sha256(manifest_path), entries


def run(root: str | Path, out_dir: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    out_dir = Path(out_dir).resolve()
    protocol = root / PROTOCOL_PATH
    if not protocol.is_file():
        raise CalibrationError("frozen protocol missing")

    surface, inherited = build_checkpoint_surface(root)
    risk = state_risk_table(surface)
    transitions = transition_table(surface)
    elapsed = elapsed_time_table(surface)
    bootstrap = cluster_bootstrap_contrasts(surface)
    summary = adjudicate(risk, elapsed)

    manifest_sha, input_entries = relevant_manifest_entries(root)
    summary.update({
        "results_blind": True,
        "data_years": [2024, 2025],
        "symbols": list(SYMBOLS),
        "checkpoint_rows": int(len(surface)),
        "distinct_events": int(surface.event_id.nunique()),
        "event_counts": inherited["event_counts"],
        "eligible_rows_by_horizon": {
            str(h): int(surface[f"eligible_{h}"].sum()) for h in HORIZONS
        },
        "censored_or_unobserved_rows_by_horizon": {
            str(h): int((~surface[f"eligible_{h}"].astype(bool)).sum()) for h in HORIZONS
        },
        "fresh_oos": False,
        "read_2026": False,
        "trading_or_economic_outcomes_evaluated": False,
    })

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "checkpoint_surface": out_dir / "checkpoint_surface_v2.csv",
        "state_risk": out_dir / "state_risk_v2.csv",
        "transitions": out_dir / "transition_matrix_v2.csv",
        "elapsed": out_dir / "elapsed_time_audit_v2.csv",
        "bootstrap": out_dir / "cluster_bootstrap_v2.csv",
        "summary": out_dir / "summary_v2.json",
    }
    surface.to_csv(paths["checkpoint_surface"], index=False)
    risk.to_csv(paths["state_risk"], index=False)
    transitions.to_csv(paths["transitions"], index=False)
    elapsed.to_csv(paths["elapsed"], index=False)
    bootstrap.to_csv(paths["bootstrap"], index=False)
    paths["summary"].write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "protocol_version": PROTOCOL_VERSION,
        "status": "completed_results_blind_state_calibration",
        "execution_commit": os.environ.get("GITHUB_SHA") or os.environ.get("GIT_COMMIT"),
        "frozen_protocol": {
            "path": str(PROTOCOL_PATH),
            "sha256": file_sha256(protocol),
        },
        "inherited_first_shock_engine": inherited,
        "bounded_1m_manifest": {
            "path": "data/cross_index_risk_gate_v1/manifest.json",
            "sha256": manifest_sha,
            "relevant_entries": input_entries,
        },
        "outputs": {
            name: {"path": str(path), "sha256": file_sha256(path)}
            for name, path in paths.items()
        },
        "results_blind": True,
        "fresh_oos": False,
        "read_2026": False,
        "clean_transition_validated": False,
        "trading_or_economic_outcomes_evaluated": False,
    }
    receipt_path = out_dir / "execution_receipt_v2.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"summary": summary, "receipt": receipt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.out)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
