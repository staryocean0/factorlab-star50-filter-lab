#!/usr/bin/env python3
"""Identity-only repair for post-shock state calibration V2.

The first V2 calibration attempt failed closed before scientific outputs because
it rebuilt first events on each index's individual minute surface. Historical
first-shock V2 instead defined operational first events after intersecting the
two indices' half-sessions and setting both minute returns Unknown whenever
either index return was missing. This wrapper restores exactly that already-
sealed support semantic and binds the rebuilt 2024-2025 event IDs to the archived
77-event historical universe before delegating all calibration statistics to the
pre-registered base implementation.

No state threshold, checkpoint, horizon, bootstrap, or adjudication rule changes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from star50_filter.cloud_market_data import load_market_data

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "state_calibration_v2.py"
UNIVERSE_PATH = Path(
    "docs/research/post_shock_state_calibration_v2/inherited_event_universe_v2.csv"
)
UNIVERSE_RECEIPT_PATH = Path(
    "docs/research/post_shock_state_calibration_v2/INHERITED_EVENT_UNIVERSE_RECEIPT.json"
)
EXPECTED_UNIVERSE_SHA256 = "08bed092f87f9f08d617c117b1d0f4584eea1006cdb390d53b353e91b07b47ff"
EXPECTED_COUNTS = {"000688.SH": 52, "000852.SH": 25}


def _load_base():
    spec = importlib.util.spec_from_file_location("_state_calibration_v2_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base runner: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_base()


def _event_id(symbol: str, session: str, minute: int) -> str:
    return f"{symbol}/{session}/{int(minute)}"


def _load_inherited_universe(root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = root / UNIVERSE_PATH
    receipt_path = root / UNIVERSE_RECEIPT_PATH
    if not path.is_file() or not receipt_path.is_file():
        raise base.CalibrationError("missing inherited V2 event-universe archive/receipt")
    actual = base.file_sha256(path)
    if actual != EXPECTED_UNIVERSE_SHA256:
        raise base.CalibrationError(
            "inherited V2 event universe drift: "
            f"actual={actual} expected={EXPECTED_UNIVERSE_SHA256}"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    archived = receipt.get("archived_exact_universe", {})
    if archived.get("sha256") != EXPECTED_UNIVERSE_SHA256 or archived.get("rows") != 77:
        raise base.CalibrationError("inherited event-universe receipt does not bind frozen 77 rows")
    universe = pd.read_csv(path)
    required = {"event_id", "symbol", "year", "session", "minute"}
    if set(universe.columns) != required:
        raise base.CalibrationError(
            f"unexpected inherited universe schema: {list(universe.columns)}"
        )
    if len(universe) != 77 or universe.event_id.duplicated().any():
        raise base.CalibrationError("inherited event universe must contain 77 unique event IDs")
    if set(universe.symbol) != set(base.SYMBOLS) or set(universe.year) - {2024, 2025}:
        raise base.CalibrationError("inherited event universe escaped frozen symbols/years")
    return universe, receipt


def build_checkpoint_surface(root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Rebuild exact sealed V2 joint-minute first events, then fixed checkpoints."""
    root = Path(root).resolve()
    engine = base.load_frozen_engine(root)
    universe, universe_receipt = _load_inherited_universe(root)

    panels: dict[str, pd.DataFrame] = {}
    for symbol in base.SYMBOLS:
        native = load_market_data(
            symbol, "1m", "2024-01-01", "2025-12-31", root=root
        )
        if native.empty:
            raise base.CalibrationError(f"empty bounded 1m surface for {symbol}")
        years = set(native.trading_day.str[:4].astype(int))
        if years - {2024, 2025}:
            raise base.CalibrationError(f"unexpected year in {symbol} bounded source: {years}")
        panels[symbol] = engine.minute_panel(native, symbol)

    common_sessions = set(panels[base.SYMBOLS[0]].session) & set(
        panels[base.SYMBOLS[1]].session
    )
    if not common_sessions:
        raise base.CalibrationError("no common half-sessions across the two indices")
    for symbol in base.SYMBOLS:
        panels[symbol] = panels[symbol].loc[
            panels[symbol].session.isin(common_sessions)
        ].reset_index(drop=True)

    alignment = ["session", "minute"]
    if not panels[base.SYMBOLS[0]][alignment].equals(
        panels[base.SYMBOLS[1]][alignment]
    ):
        raise base.CalibrationError("joint-minute panel alignment differs across indices")

    joint_known = np.isfinite(panels[base.SYMBOLS[0]].return_bp.to_numpy(float))
    joint_known &= np.isfinite(panels[base.SYMBOLS[1]].return_bp.to_numpy(float))
    joint: dict[str, pd.DataFrame] = {}
    features: dict[str, pd.DataFrame] = {}
    for symbol in base.SYMBOLS:
        joint[symbol] = panels[symbol].copy()
        joint[symbol].loc[~joint_known, "return_bp"] = np.nan
        features[symbol] = engine.make_features(joint[symbol])

    rebuilt: list[dict[str, Any]] = []
    for symbol in base.SYMBOLS:
        events = features[symbol].loc[
            features[symbol]["first"].eq(1.0)
            & features[symbol]["year"].isin([2024, 2025])
            & (features[symbol]["minute"] >= 33)
        ].copy()
        for _, event in events.iterrows():
            rebuilt.append({
                "event_id": _event_id(symbol, str(event.session), int(event.minute)),
                "symbol": symbol,
                "year": int(event.year),
                "session": str(event.session),
                "minute": int(event.minute),
            })
    rebuilt_df = pd.DataFrame(rebuilt).sort_values(
        ["symbol", "year", "session", "minute"], kind="stable"
    ).reset_index(drop=True)
    expected_df = universe.sort_values(
        ["symbol", "year", "session", "minute"], kind="stable"
    ).reset_index(drop=True)

    rebuilt_ids = set(rebuilt_df.event_id)
    expected_ids = set(expected_df.event_id)
    if rebuilt_ids != expected_ids:
        missing = sorted(expected_ids - rebuilt_ids)
        extra = sorted(rebuilt_ids - expected_ids)
        raise base.CalibrationError(
            "inherited_checkpoint_surface_not_reproducible: exact historical V2 "
            f"event IDs differ; missing={missing[:10]} extra={extra[:10]}"
        )
    pd.testing.assert_frame_equal(
        rebuilt_df[["event_id", "symbol", "year", "session", "minute"]],
        expected_df[["event_id", "symbol", "year", "session", "minute"]],
        check_dtype=False,
        check_like=False,
    )

    event_counts = rebuilt_df.groupby("symbol").size().to_dict()
    if event_counts != EXPECTED_COUNTS:
        raise base.CalibrationError(
            f"sealed V2 event counts differ: {event_counts} != {EXPECTED_COUNTS}"
        )

    rows: list[dict[str, Any]] = []
    for symbol in base.SYMBOLS:
        f = features[symbol]
        session_groups = {
            str(key): part.sort_values("minute", kind="stable").reset_index(drop=True)
            for key, part in f.groupby("session", sort=False)
        }
        events = f.loc[
            f["first"].eq(1.0)
            & f["year"].isin([2024, 2025])
            & (f["minute"] >= 33)
        ].sort_values(["session", "minute"], kind="stable")
        for _, event in events.iterrows():
            session = str(event.session)
            minute = int(event.minute)
            event_id = _event_id(symbol, session, minute)
            if event_id not in expected_ids:
                raise base.CalibrationError(f"unsealed event escaped exact universe: {event_id}")
            sigma_pre = float(event.sigma_pre)
            if not np.isfinite(sigma_pre) or sigma_pre <= 0:
                raise base.CalibrationError(f"invalid sigma_pre for {event_id}")
            g = session_groups[session]
            returns = g["return_bp"].to_numpy(float)
            year = int(event.year)

            for checkpoint in base.CHECKPOINTS:
                endpoint = minute + checkpoint
                current_rms = base.rms_window(returns, endpoint)
                current_ratio = (
                    float(current_rms / sigma_pre)
                    if np.isfinite(current_rms)
                    else float("nan")
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
                    "current_state": base.state_from_ratio(current_ratio),
                    "current_observed": bool(np.isfinite(current_ratio)),
                }
                for horizon in base.HORIZONS:
                    future_rms = base.rms_window(returns, endpoint + horizon)
                    future_ratio = (
                        float(future_rms / sigma_pre)
                        if np.isfinite(future_rms)
                        else float("nan")
                    )
                    item[f"future_ratio_{horizon}"] = future_ratio
                    item[f"future_state_{horizon}"] = base.state_from_ratio(future_ratio)
                    item[f"eligible_{horizon}"] = bool(
                        np.isfinite(current_ratio) and np.isfinite(future_ratio)
                    )
                rows.append(item)

    surface = pd.DataFrame(rows)
    expected_rows = 77 * len(base.CHECKPOINTS)
    if len(surface) != expected_rows:
        raise base.CalibrationError(
            f"checkpoint row mismatch after exact-universe gate: {len(surface)} != {expected_rows}"
        )
    if surface.duplicated(["event_id", "checkpoint_min"]).any():
        raise base.CalibrationError("duplicate (event_id, checkpoint_min)")

    receipt = {
        "event_counts": {k: int(v) for k, v in event_counts.items()},
        "checkpoint_rows": int(len(surface)),
        "checkpoints": list(base.CHECKPOINTS),
        "horizons": list(base.HORIZONS),
        "engine_path": str(base.ENGINE_PATH),
        "engine_sha256": base.ENGINE_SHA256,
        "engine_git_blob": base.ENGINE_GIT_BLOB,
        "operational_support": "sealed V2 joint-minute common-session surface",
        "joint_minute_rows": int(len(joint_known)),
        "joint_known_return_rows": int(joint_known.sum()),
        "inherited_event_universe": {
            "path": str(UNIVERSE_PATH),
            "sha256": EXPECTED_UNIVERSE_SHA256,
            "rows": 77,
            "historical_review_run": universe_receipt["historical_authority"]["v2_review_run"],
            "historical_review_artifact_digest": universe_receipt["historical_authority"]["review_artifact"]["artifact_digest"],
            "exact_event_id_match": True,
        },
    }
    return surface, receipt


def run(root: str | Path, out: str | Path) -> dict[str, Any]:
    # Delegate all pre-registered statistics/adjudication to the original V2
    # implementation after replacing only its failed event-surface builder.
    base.build_checkpoint_surface = build_checkpoint_surface
    result = base.run(root, out)

    root = Path(root).resolve()
    out = Path(out).resolve()
    receipt_path = out / "execution_receipt_v2.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["identity_repair"] = {
        "status": "sealed_joint_support_restored_before_scientific_outcomes",
        "wrapper_path": str(Path(__file__).resolve().relative_to(root)),
        "wrapper_sha256": base.file_sha256(Path(__file__)),
        "base_runner_path": str(BASE_PATH.resolve().relative_to(root)),
        "base_runner_sha256": base.file_sha256(BASE_PATH),
        "inherited_universe_path": str(UNIVERSE_PATH),
        "inherited_universe_sha256": EXPECTED_UNIVERSE_SHA256,
        "inherited_universe_receipt_path": str(UNIVERSE_RECEIPT_PATH),
        "inherited_universe_receipt_sha256": base.file_sha256(root / UNIVERSE_RECEIPT_PATH),
        "changed_scientific_parameters": [],
        "changed_only": "operational event support inheritance: individual -> sealed V2 joint-minute surface",
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


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
