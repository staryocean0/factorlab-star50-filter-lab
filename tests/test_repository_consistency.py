"""Adversarial maintenance regressions: do not mistake green CI for promotion."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('repository_consistency', ROOT / 'scripts/repository_consistency.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_current_semantics_match_all_frozen_states():
    state = m.read_json(ROOT, m.STATE)
    assert m.validate_semantics(ROOT, state) == []


@pytest.mark.parametrize('field', ['production_authority', 'd6_started', 'v20_started', 'blackbox_query_authorized', 'new_research_authorized', 'raw_market_rows_read_by_maintenance', 'd5_external_consumer_accepted'])
def test_escalation_is_rejected(field):
    state = deepcopy(m.read_json(ROOT, m.STATE))
    state[field] = True
    assert m.validate_semantics(ROOT, state)


def test_stale_latest_state_is_rejected():
    state = deepcopy(m.read_json(ROOT, m.STATE))
    state['latest_scientific_decision'] = 'SIGNED_RETURN_ASYMMETRY_INCREMENTAL_UTILITY_NOT_SUPPORTED'
    assert m.validate_semantics(ROOT, state)


def test_hold_cannot_disappear():
    state = deepcopy(m.read_json(ROOT, m.STATE))
    state['research_hold'] = False
    assert m.validate_semantics(ROOT, state)


def test_all_entrypoints_are_generated_from_one_state():
    rendered = m.render_documents(ROOT, m.read_json(ROOT, m.STATE))
    for path in m.ENTRYPOINTS:
        assert m.DECISION in rendered[path]
        assert m.PROGRAM in rendered[path]
        assert (ROOT / path).read_text() == rendered[path]


def test_legacy_storage_name_is_not_data_role():
    text = m.render_documents(ROOT, m.read_json(ROOT, m.STATE))['docs/WHITEPAPER.md']
    assert '2026-08-21' in text and '2021–2025' in text
    assert '目录名不授予训练权' in text


def test_changed_frozen_state_source_is_rejected(tmp_path):
    state = m.read_json(ROOT, m.STATE)
    for row in state['scientific_sources']:
        dest = tmp_path / row['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / row['path'], dest)
    path = tmp_path / m.LATEST / 'PROGRAM_STATE.json'
    path.write_text(path.read_text() + ' ')
    assert m.validate_semantics(tmp_path, state)


def test_all_original_files_have_preserved_identity_and_role():
    c = m.read_json(ROOT, m.CATALOG)
    assert c['baseline_file_count'] == len(c['preserved']) == 5187
    assert len({r['original'] for r in c['preserved']}) == 5187
    assert all(len(r['git_blob']) == 40 and r['role'] for r in c['preserved'])
    assert sum(r['original'].startswith('.codex/') for r in c['preserved']) == 4


def test_every_research_suite_is_registered_and_raw_integration_explicit():
    reg = m.read_json(ROOT, 'docs/governance/TEST_REGISTRY.json')
    actual = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob('research/*/test*.py')) + sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob('docs/research/*/test*.py'))
    assert reg['research_suites'] == actual and len(actual) == 25
    assert reg['manual_integration'] == ['tests/integration/test_legacy_market_integrity.py']
    assert 'test_exact_l3_prefix' in reg['external_dependency_skip']


def test_blob_identity_changes_with_one_byte():
    assert m.blob(b'x') != m.blob(b'x\n')
