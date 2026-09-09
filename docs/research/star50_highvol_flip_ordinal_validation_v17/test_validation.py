from pathlib import Path
import importlib.util
import json


def load_module():
    p=Path(__file__).parent/'run_validation.py'
    s=importlib.util.spec_from_file_location('v17val',p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_v17_validation_freeze():
    m=load_module()
    assert m.START=='2024-01-01' and m.END=='2026-08-21'
    assert m.YEARS==(2024,2025,2026)
    assert m.SYMBOL=='000688.SH'
    assert m.CANDIDATE_ID=='star50_v17_first_up_to_down_highvol_episode_continuation_3m'
    assert m.CANDIDATE_CODE_SHA=='5c0c173a58466ea9423750252606d6458b4fcf64'
    assert m.CONFIG_SHA256=='ba7232e4c08559486fe732c72934a4970e5d1eaae6814fa20124efdbced154de'
    assert m.MIN_YEAR_N==15 and m.GROSS_BREAK_EVEN_BP==2.0
    freeze=json.loads((Path(__file__).parents[1]/'star50_highvol_flip_ordinal_dev_v17'/'candidate_freeze.json').read_text())
    assert freeze['candidate_id']==m.CANDIDATE_ID
    assert freeze['candidate_code_commit_sha']==m.CANDIDATE_CODE_SHA
    assert freeze['config_sha256']==m.CONFIG_SHA256
