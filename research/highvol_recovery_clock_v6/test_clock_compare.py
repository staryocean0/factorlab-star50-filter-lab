from __future__ import annotations
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load_mod():
    spec=importlib.util.spec_from_file_location('clock_v6',HERE/'run_clock_compare.py'); m=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(m); return m

def test_frozen_buckets():
    m=load_mod(); assert m.YEARS==(2021,2022,2023); assert m.STATES==('UNSAFE','RECOVERING'); assert m.BUCKETS==('LT15','M15_25','M30_40','GE45'); assert m.MIN_CELL_N==100

def test_age_bucket_edges():
    m=load_mod(); assert [m.age_bucket(x) for x in [1,2,3,5,6,8,9,20]]==['LT15','LT15','M15_25','M15_25','M30_40','M30_40','GE45','GE45']
