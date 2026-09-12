#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path

TERMS = {
  "row_count_349923": re.compile(r"349[,_ ]?923", re.I),
  "v0615": re.compile(r"v?0\.6\.15|v0615|0615", re.I),
  "leg_universe": re.compile(r"leg[-_ ]?universe|published[-_ ]?leg|strict[-_ ]?pair", re.I),
  "source_identity": re.compile(r"expected[-_ ]?source[-_ ]?(sha|hash)|source[-_ ]?(sha256|identity|hash)", re.I),
  "identity_manifest": re.compile(r"expected[-_ ]?(sha|hash)|identity[-_ ]?(receipt|manifest)|frozen[-_ ]?identity", re.I),
}
MAX_BLOB = 5_000_000

def sh(*args: str, check=True) -> str:
    p=subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode: raise RuntimeError(f"{' '.join(args)}\n{p.stderr}")
    return p.stdout

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cutoff', required=True); ap.add_argument('--output', type=Path, required=True); a=ap.parse_args()
    commits=[x for x in sh('git','rev-list','--all',f'--before={a.cutoff}').splitlines() if x]
    commit_set=set(commits)
    objects=sh('git','rev-list','--objects','--all',f'--before={a.cutoff}').splitlines()
    blobs={}
    for line in objects:
        parts=line.split(' ',1); oid=parts[0]; path=parts[1] if len(parts)>1 else ''
        if not path: continue
        typ=sh('git','cat-file','-t',oid,check=False).strip()
        if typ!='blob': continue
        size_txt=sh('git','cat-file','-s',oid,check=False).strip()
        if not size_txt: continue
        size=int(size_txt)
        if size>MAX_BLOB: continue
        blobs.setdefault(oid,set()).add(path)
    hits=[]
    for oid, paths in blobs.items():
        raw=subprocess.check_output(['git','cat-file','blob',oid])
        if b'\x00' in raw[:8192]: continue
        text=raw.decode('utf-8','replace')
        found=[]
        snippets=[]
        for name,rx in TERMS.items():
            for m in rx.finditer(text):
                found.append(name)
                line=text.count('\n',0,m.start())+1
                lo=max(0,m.start()-100); hi=min(len(text),m.end()+140)
                snippets.append({'term':name,'line':line,'snippet':text[lo:hi].replace('\n',' ')[:300]})
                break
        if found:
            path=sorted(paths)[0]
            intro=sh('git','log','--all',f'--before={a.cutoff}','--format=%H|%cI|%s',f'--find-object={oid}','--',path,check=False).splitlines()
            hits.append({'blob':oid,'paths':sorted(paths),'terms':sorted(set(found)),'snippets':snippets,'history':intro[:10]})
    # Strong candidates must mention a specific required row count or v0.6.15 together with identity/leg-universe semantics.
    strong=[]
    for h in hits:
        ts=set(h['terms'])
        if 'row_count_349923' in ts or ('v0615' in ts and ('leg_universe' in ts or 'source_identity' in ts or 'identity_manifest' in ts)):
            strong.append(h)
    out={'schema':'v0617_prior_identity_audit_v1','cutoff':a.cutoff,'commits_scanned':len(commits),'text_blobs_scanned':len(blobs),'hits':hits,'strong_candidate_hits':strong,'required_precommit_identity_recovered':bool(strong)}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'commits_scanned':len(commits),'text_blobs_scanned':len(blobs),'hit_blobs':len(hits),'strong_candidate_hits':len(strong),'required_precommit_identity_recovered':bool(strong)},indent=2))
    for h in strong: print('STRONG',h['blob'],h['paths'],h['terms'])
if __name__=='__main__': main()
