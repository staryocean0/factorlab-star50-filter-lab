from pathlib import Path
import importlib.util
import json


def load_module():
    p=Path(__file__).parent/'run_validation.py'
    s=importlib.util.spec_from_file_location('v16val',p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_v16_validation_freeze():
    m=load_module()
    assert m.START=='2024-01-01' and m.END=='2026-08-21'
    assert m.YEARS==(2024,2025,2026)
    assert m.STAR=='000688.SH' and m.CSI=='000852.SH'
    assert m.CANDIDATE_ID=='star50_v16_up_to_down_csi_normal_continuation_3m'
    assert m.CANDIDATE_CODE_SHA=='358430c30a207e083e04e7cdfd8215aee8711411'
    assert m.CONFIG_SHA256=='a36b5998653a526f4b1eba8f4b5c71efa7474597006c86c0a0b6d6ac37095a9c'
    assert m.MIN_YEAR_N==15 and m.GROSS_BREAK_EVEN_BP==2.0
    freeze=json.loads((Path(__file__).parents[1]/'star50_cross_state_sign_flip_dev_v16'/'candidate_freeze.json').read_text())
    assert freeze['candidate_id']==m.CANDIDATE_ID
    assert freeze['candidate_code_commit_sha']==m.CANDIDATE_CODE_SHA
    assert freeze['config_sha256']==m.CONFIG_SHA256
