from __future__ import annotations

import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def test_frozen_candidate_identity():
    f=json.loads((HERE/'FROZEN_CALIBRATION_V4.json').read_text())
    assert f['candidate_id']=='shared_unsafe_recovering_age_recovery_probability_v4'
    assert f['frozen_after_development_before_validation'] is True
    assert f['state_engine']['highvol_ratio']==1.5
    assert f['state_engine']['recovery_normal_ratio']==1.1
    assert f['state_engine']['shock_sigma']==3.0
    assert f['landmark_bars']==[1,3,6,9]
    assert f['future_hazard_bars']==3
    assert len(f['probability_map'])==8
    assert f['validation_preregistered']['available_native_5m_coverage']=='2024-01-01/2025-12-31'


def test_frozen_probabilities_are_valid_and_ordered():
    f=json.loads((HERE/'FROZEN_CALIBRATION_V4.json').read_text())
    m={(r['landmark_bars'],r['state']):r['probability'] for r in f['probability_map']}
    for lm in [1,3,6,9]:
        assert 0 < m[(lm,'UNSAFE')] < 1
        assert 0 < m[(lm,'RECOVERING')] < 1
        assert m[(lm,'RECOVERING')] > m[(lm,'UNSAFE')]
