from pathlib import Path
import importlib.util


def load_module():
    p = Path(__file__).parent / 'run_cross_state.py'
    s = importlib.util.spec_from_file_location('v10', p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_v10_fixed_boundaries_and_matrix():
    m = load_module()
    assert m.START == '2021-01-01'
    assert m.END == '2023-12-31'
    assert m.YEARS == (2021, 2022, 2023)
    assert m.CODES == ('000688.SH', '000852.SH')
    assert m.CELL_ORDER == (
        'star_high|csi_high',
        'star_high|csi_normal',
        'star_normal|csi_high',
        'star_normal|csi_normal',
    )
    assert m.RELATIONS == ('all', 'same', 'opposite')
