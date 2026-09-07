import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "code"))
from post_shock_state import PostShockState


def started(sigma=10.0):
    x = PostShockState()
    x.start(session="2026-01-01/0", event_minute=50, sigma_pre=sigma)
    return x


def test_first_four_completed_minutes_remain_unsafe():
    x = started()
    for m in range(51, 55):
        assert x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=1.0, quality_valid=True) == "UNSAFE"
        assert x.online_clean is False


def test_fifth_minute_enters_recovering_when_ratio_low():
    x = started()
    for m in range(51, 56):
        state = x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=5.0, quality_valid=True)
    assert state == "RECOVERING"
    assert math.isclose(x.recovery_ratio, 0.5)
    assert not x.online_clean


def test_recovering_can_reactivate_unsafe():
    x = started()
    for m in range(51, 56):
        x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=5.0, quality_valid=True)
    assert x.state == "RECOVERING"
    for m in range(56, 61):
        x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=20.0, quality_valid=True)
    assert x.state == "UNSAFE"
    assert x.recovery_ratio >= 1.5


def test_missing_does_not_become_zero_volatility():
    x = started()
    for m in range(51, 55):
        x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=1.0, quality_valid=True)
    assert x.observe_completed_minute(session="2026-01-01/0", minute=55, return_bp=None, quality_valid=False) == "UNKNOWN"
    assert x.recovery_ratio is None


def test_unknown_recovers_only_after_five_new_valid_minutes():
    x = started()
    for m in range(51, 55):
        x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=1.0, quality_valid=True)
    x.observe_completed_minute(session="2026-01-01/0", minute=55, return_bp=None, quality_valid=False)
    for m in range(56, 60):
        assert x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=1.0, quality_valid=True) == "UNKNOWN"
    assert x.observe_completed_minute(session="2026-01-01/0", minute=60, return_bp=1.0, quality_valid=True) == "RECOVERING"


def test_sigma_anchor_never_updates_from_post_shock_returns():
    x = started(sigma=8.0)
    for m, r in zip(range(51, 56), [100, 1, 1, 1, 1]):
        x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=r, quality_valid=True)
    assert x.sigma_pre == 8.0


def test_session_boundary_ends_instead_of_bridging():
    x = started()
    assert x.observe_completed_minute(session="2026-01-01/1", minute=51, return_bp=1.0, quality_valid=True) == "ENDED"
    assert not x.online_clean


def test_no_fixed_timeout_creates_clean():
    x = started()
    for m in range(51, 111):
        x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=0.1, quality_valid=True)
        assert x.state in {"RECOVERING", "UNSAFE", "UNKNOWN"}
        assert not x.online_clean


def test_rejects_noncausal_same_or_prior_minute():
    x = started()
    for m in (50, 49):
        try:
            x.observe_completed_minute(session="2026-01-01/0", minute=m, return_bp=1.0, quality_valid=True)
        except ValueError:
            pass
        else:
            raise AssertionError("must reject same/prior minute")
