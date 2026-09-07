"""Seal/verify the completed round without altering any historical bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from run_streak_mechanism_v1 import DOC, OUT, check_sources, sha, write


def inventory():
    protocol = check_sources()
    files = {p for p in OUT.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    files |= {p for p in DOC.rglob('*') if p.is_file()}
    files |= {ROOT/p for p in protocol['source_hashes']}
    files |= {ROOT/'scripts/render_streak_mechanism_v1.py', Path(__file__).resolve()}
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    manifest = OUT/'manifest.json'
    if args.verify:
        m = json.loads(manifest.read_text())
        assert m['files'] == inventory(), 'File bytes or inventory changed after seal'
        assert m['production_authority'] is False and m['fresh_oos'] is False
        print(json.dumps({'sealed_bundle_valid': True, 'files': len(m['files']),
                          'manifest_sha256': sha(manifest)}))
        return
    assert not manifest.exists(), 'Do not overwrite a sealed manifest'
    result = json.loads((OUT/'validation.json').read_text())
    assert result['valid'] and result['new_source_closure_passed']
    write(manifest, {'schema': 'star50_streak_mechanism_manifest@1', 'files': inventory(),
                     'source_identity': 'new_round_bound_to_recoverable_original_Git_sources',
                     'fourth_round_hash_incident_remains_open': True,
                     'mutable_navigation_excluded': ['CURRENT_RESEARCH.md', 'ai-readme.md',
                                                      'LOCAL_TAKEOVER.md', 'docs/INDEX.md'],
                     'fresh_oos': False, 'production_authority': False})
    print(json.dumps({'sealed': True, 'files': len(json.loads(manifest.read_text())['files'])}))


if __name__ == '__main__':
    main()
