"""Preserve exact upstream source bytes and seal this bounded delivery."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/three_proposals_v1'
FACTORLAB = Path('/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab')


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


frozen = json.loads((OUT / 'freeze.json').read_text())
for group, root, hashes in [('star50', ROOT, frozen['sources']),
                            ('factorlab', FACTORLAB, frozen['external_sources'])]:
    for name, expected in hashes.items():
        assert sha(root / name) == expected, name
        backup = OUT / 'frozen_sources' / group / name
        if not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, backup)
        assert sha(backup) == expected
for name, expected in frozen['inputs'].items():
    assert sha(ROOT / name) == expected
files = [p for p in OUT.rglob('*') if p.is_file() and 'isolated' not in p.relative_to(OUT).parts
         and p.name != 'delivery_manifest.json']
files += [ROOT / n for n in frozen['sources']]
files += [ROOT / 'scripts' / n for n in ['report_three_proposals_v1.py', 'replay_three_proposals_v1.py',
                                       'render_three_proposals_v1.py', 'seal_three_proposals_v1.py']]
files += [ROOT / 'docs/research/three_proposals_v1/report.md']
manifest = {'scope': 'bounded research; original full-unit index account, not actual ETF/options approval',
            'files': {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}}
target = OUT / 'delivery_manifest.json'
if target.exists():
    assert json.loads(target.read_text()) == manifest, 'Existing sealed delivery drifted'
else:
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('Verified sealed delivery:', len(manifest['files']), 'files')
