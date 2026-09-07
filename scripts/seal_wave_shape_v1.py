"""Seal bounded research delivery, without rewriting old manifests."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/wave_shape_v1p2'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


frozen = json.loads((OUT / 'freeze.json').read_text())
for n, h in frozen['sources'].items():
    assert sha(ROOT / n) == h
assert sha(ROOT / frozen['input_path']) == frozen['input_sha256']
files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'delivery_manifest.json']
files += [ROOT / n for n in frozen['sources']]
files += [ROOT / 'scripts/report_wave_shape_v1.py', Path(__file__),
          ROOT / 'docs/research/wave_shape_v1/report.md']
manifest = {'scope': 'wave_shape_v1p2 research delivery, no strategy authority',
            'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}}
target = OUT / 'delivery_manifest.json'
if target.exists():
    assert json.loads(target.read_text()) == manifest, 'Sealed delivery drift; do not silently rebind'
else:
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('Delivery verified:', len(manifest['files']), 'files')
