"""Results-blind session-aware information-set bounds (v0.6.17).

This module deliberately does *not* reproduce DataHub bucket logic. The
DataHub export must provide explicit leg/support membership and expected step
ordinals. That makes the archived DataHub contract the authority and prevents
FactorLab from silently replacing actual support with adjacent-close or fixed-
five assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

PROTOCOL_VERSION = "session_aware_information_set_bounds_v0.6.17"
AUTHORITATIVE_SOURCE_ROWS = 349_923
UNAUTHORIZED_FACTORSOURCE_ROWS = 350_561

FORBIDDEN_RESULT_TOKENS = (
    "pnl", "profit", "loss", "return", "ret_fwd", "future_ret", "forward_ret",
    "drawdown", "mdd", "sharpe", "trade_result", "oos_result", "target_y",
)

REQUIRED_LEG_COLUMNS = {"leg_id", "expected_step_count"}
REQUIRED_SUPPORT_COLUMNS = {
    "leg_id", "step_ordinal", "observed", "open", "high", "low", "close"
}


class IntakeError(ValueError):
    """Fail-closed intake error for the frozen preanalysis."""


def _check_results_blind(columns: Iterable[str]) -> None:
    for column in columns:
        lower = str(column).lower()
        if any(token in lower for token in FORBIDDEN_RESULT_TOKENS):
            raise IntakeError(f"results-blind violation: forbidden column {column!r}")


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise IntakeError(f"{name} missing required columns: {missing}")


def file_sha256(path: str | Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@dataclass(frozen=True)
class SourceIdentity:
    rows: int
    expected_rows: int
    status: str
    sha256: str | None = None
    expected_sha256: str | None = None


def adjudicate_source_identity(
    rows: int,
    *,
    expected_rows: int = AUTHORITATIVE_SOURCE_ROWS,
    actual_sha256: str | None = None,
    expected_sha256: str | None = None,
    authoritative: bool = True,
) -> SourceIdentity:
    """Adjudicate source identity before any scientific replay."""
    status = "accepted"
    if rows != expected_rows:
        if rows == UNAUTHORIZED_FACTORSOURCE_ROWS:
            status = "rejected_factorlab_1m_official_is_not_datahub_authority"
        else:
            status = "rejected_row_count_mismatch"
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        status = "rejected_sha256_mismatch"
    identity = SourceIdentity(
        rows=int(rows), expected_rows=int(expected_rows), status=status,
        sha256=actual_sha256, expected_sha256=expected_sha256,
    )
    if authoritative and status != "accepted":
        raise IntakeError(f"authoritative source identity failed: {asdict(identity)}")
    return identity


def motion_concentration(log_prices: np.ndarray) -> float:
    """Inherited displacement-concentration statistic from ``wave_shape.py``.

    Input is a log-price path. For n steps with absolute log motions a_i,
    C = n * sum((a_i/sum(a))^2). C=1 for evenly distributed displacement and
    C=n when one step carries all displacement. Zero-motion paths are undefined.
    """
    log_prices = np.asarray(log_prices, dtype=float)
    if log_prices.ndim != 1 or len(log_prices) < 2 or not np.isfinite(log_prices).all():
        raise IntakeError("log_prices must contain at least two finite observations")
    motion = np.abs(np.diff(log_prices))
    total = float(motion.sum())
    if total <= 0:
        return float("nan")
    n = len(motion)
    share = motion / total
    return float(n * np.sum(share * share))


def universal_concentration_bounds(expected_steps: int) -> tuple[float, float]:
    if int(expected_steps) != expected_steps or expected_steps < 1:
        raise IntakeError(f"expected_step_count must be a positive integer, got {expected_steps}")
    return 1.0, float(expected_steps)


def _validate_leg_support(leg: pd.Series, support: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    expected = int(leg.expected_step_count)
    if expected < 1:
        raise IntakeError(f"leg {leg.leg_id}: expected_step_count < 1")
    if support.empty:
        return support, expected, 0
    if support.step_ordinal.isna().any():
        raise IntakeError(f"leg {leg.leg_id}: null step_ordinal")
    ordinals = support.step_ordinal.astype(int).to_numpy()
    if np.any(ordinals < 0) or np.any(ordinals >= expected):
        raise IntakeError(f"leg {leg.leg_id}: step ordinal outside [0, {expected})")
    if len(np.unique(ordinals)) != len(ordinals):
        raise IntakeError(f"leg {leg.leg_id}: duplicate step_ordinal")
    support = support.assign(step_ordinal=ordinals).sort_values("step_ordinal", kind="stable")
    observed = support.observed.astype(bool)
    observed_n = int(observed.sum())
    return support, expected, observed_n


def _support_log_path(observed: pd.DataFrame) -> np.ndarray:
    """Build actual-support log path without importing an adjacent bar close.

    Each source minute contributes one step: first source-minute open -> first
    close, then support-ordered closes. A prior-session/prior-bucket close is
    never injected. This is the v0.6.17 fix for the v0.6.15 adjacency error.
    """
    if observed.empty:
        raise IntakeError("cannot build path from empty support")
    first_open = float(observed.iloc[0].open)
    closes = observed.close.to_numpy(float)
    prices = np.r_[first_open, closes]
    if not np.isfinite(prices).all() or np.any(prices <= 0):
        raise IntakeError("supported prices must be finite and strictly positive")
    return np.log(prices)


def _ohlc_consistency(leg: pd.Series, observed: pd.DataFrame, tol: float) -> str:
    native_cols = {"native_open", "native_high", "native_low", "native_close"}
    if not native_cols.issubset(leg.index) or any(pd.isna(leg[c]) for c in native_cols):
        return "not_provided"
    if observed.empty:
        return "not_comparable"
    calc = np.array([
        float(observed.iloc[0].open),
        float(observed.high.max()),
        float(observed.low.min()),
        float(observed.iloc[-1].close),
    ])
    native = np.array([float(leg[c]) for c in ("native_open", "native_high", "native_low", "native_close")])
    scale = max(1.0, float(np.max(np.abs(native))))
    return "match" if np.max(np.abs(calc - native)) <= tol * scale else "mismatch"


def evaluate_information_set_bounds(
    legs: pd.DataFrame,
    support: pd.DataFrame,
    *,
    identity: SourceIdentity | None = None,
    ohlc_tolerance: float = 1e-10,
) -> pd.DataFrame:
    """Evaluate every frozen leg; boundary/gap legs are retained, never deleted.

    Complete actual support collapses the interval to the oracle concentration.
    Any missing/dropped support step receives the full universal [1, n] interval.
    """
    _require_columns(legs, REQUIRED_LEG_COLUMNS, "legs")
    _require_columns(support, REQUIRED_SUPPORT_COLUMNS, "support")
    _check_results_blind(legs.columns)
    _check_results_blind(support.columns)
    if legs.leg_id.duplicated().any():
        dup = legs.loc[legs.leg_id.duplicated(), "leg_id"].iloc[0]
        raise IntakeError(f"duplicate leg_id: {dup}")

    unknown_leg_ids = set(support.leg_id).difference(set(legs.leg_id))
    if unknown_leg_ids:
        raise IntakeError(f"support references unknown legs: {sorted(unknown_leg_ids)[:5]}")

    rows: list[dict] = []
    grouped = {key: value.copy() for key, value in support.groupby("leg_id", sort=False)}
    overlay_cols = [c for c in (
        "published", "strict_pair", "qualified", "offset", "session_id",
        "boundary_class", "native_bar_id"
    ) if c in legs.columns]

    for _, leg in legs.iterrows():
        leg_support = grouped.get(leg.leg_id, support.iloc[0:0].copy())
        leg_support, expected, observed_n = _validate_leg_support(leg, leg_support)
        observed_mask = leg_support.observed.astype(bool) if not leg_support.empty else pd.Series(dtype=bool)
        observed = leg_support.loc[observed_mask].copy() if not leg_support.empty else leg_support.copy()
        complete_ordinals = set(leg_support.loc[observed_mask, "step_ordinal"].astype(int)) == set(range(expected)) if not leg_support.empty else False
        finite_ohlc = (
            not observed.empty
            and np.isfinite(observed[["open", "high", "low", "close"]].to_numpy(float)).all()
            and (observed[["open", "high", "low", "close"]].to_numpy(float) > 0).all()
        )
        support_complete = bool(observed_n == expected and complete_ordinals and finite_ohlc)
        ohlc_status = _ohlc_consistency(leg, observed, ohlc_tolerance) if support_complete else "not_comparable"

        lower, upper = universal_concentration_bounds(expected)
        oracle = float("nan")
        total_motion = float("nan")
        oracle_comparable = False
        universal = True
        reason = "support_gap"

        if support_complete and ohlc_status != "mismatch":
            log_path = _support_log_path(observed)
            motion = np.abs(np.diff(log_path))
            total_motion = float(motion.sum())
            oracle = motion_concentration(log_path)
            if np.isfinite(oracle):
                lower = upper = oracle
                oracle_comparable = True
                universal = False
                reason = "complete_actual_support"
            else:
                reason = "zero_motion_undefined"
        elif support_complete and ohlc_status == "mismatch":
            reason = "data_consistency_mismatch"

        item = {
            "leg_id": leg.leg_id,
            "protocol_version": PROTOCOL_VERSION,
            "expected_step_count": expected,
            "observed_step_count": observed_n,
            "support_complete": support_complete,
            "support_gap": not support_complete,
            "ohlc_consistency": ohlc_status,
            "oracle_comparable": oracle_comparable,
            "motion_total_log": total_motion,
            "motion_concentration_oracle": oracle,
            "concentration_lower": float(lower),
            "concentration_upper": float(upper),
            "bound_width": float(upper - lower),
            "universal_bound_used": universal,
            "bound_reason": reason,
            "data_identity_status": identity.status if identity is not None else "not_attached",
        }
        for col in overlay_cols:
            item[col] = leg[col]
        rows.append(item)
    return pd.DataFrame(rows)


def summarize_bounds(bounds: pd.DataFrame) -> dict:
    """Results-blind topology/tightness summary only; no economic outcomes."""
    required = {"support_complete", "oracle_comparable", "bound_width", "universal_bound_used", "ohlc_consistency"}
    _require_columns(bounds, required, "bounds")
    n = len(bounds)
    out = {
        "protocol_version": PROTOCOL_VERSION,
        "legs": int(n),
        "support_complete": int(bounds.support_complete.sum()),
        "support_gap": int((~bounds.support_complete.astype(bool)).sum()),
        "oracle_comparable": int(bounds.oracle_comparable.sum()),
        "universal_bound_used": int(bounds.universal_bound_used.sum()),
        "ohlc_mismatch": int((bounds.ohlc_consistency == "mismatch").sum()),
        "mean_bound_width": float(bounds.bound_width.mean()) if n else None,
        "median_bound_width": float(bounds.bound_width.median()) if n else None,
        "max_bound_width": float(bounds.bound_width.max()) if n else None,
    }
    for col in ("offset", "boundary_class", "published", "strict_pair", "qualified"):
        if col in bounds.columns:
            groups = {}
            for key, part in bounds.groupby(col, dropna=False):
                groups[str(key)] = {
                    "legs": int(len(part)),
                    "support_gap": int((~part.support_complete.astype(bool)).sum()),
                    "oracle_comparable": int(part.oracle_comparable.sum()),
                    "mean_bound_width": float(part.bound_width.mean()),
                }
            out[f"by_{col}"] = groups
    return out
