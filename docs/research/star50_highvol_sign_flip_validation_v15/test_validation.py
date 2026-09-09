from pathlib import Path
import importlib.util
import json


def load_module():
    p=Path(__file__).parent/'run_validation.py'
    s=importlib.util.spec_from_file_location('v15val',p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_v15_validation_freeze():
    m=load_module()
    assert m.START=='2024-01-01' and m.END=='2026-08-21'
    assert m.YEARS==(2024,2025,2026)
    assert m.SYMBOL=='000688.SH'
    assert m.CANDIDATE_ID=='star50_v15_up_to_down_continuation_3m'
    assert m.CANDIDATE_CODE_SHA=='285a429d96dd7c92afce86d4859f111ae9b8961d'
    assert m.CONFIG_SHA256=='7053f5000ff0d04da62a82781a86c5f518cb135396d88a9d178fd95cf41cf704'
    assert m.COST_BP_PER_LEG==1.0
    assert m.MIN_YEAR_N==15 and m.GROSS_BREAK_EVEN_BP==2.0
    freeze=json.loads((Path(__file__).parents[1]/'star50_highvol_sign_flip_dev_v15'/'candidate_freeze.json').read_text())
    assert freeze['candidate_id']==m.CANDIDATE_ID
    assert freeze['candidate_code_commit_sha']==m.CANDIDATE_CODE_SHA
    assert freeze['config_sha256']==m.CONFIG_SHA256
