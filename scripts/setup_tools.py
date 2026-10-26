"""Build pinned Undark and apply an explicit hashing-only Dissect compatibility patch."""
from pathlib import Path
import difflib,hashlib,importlib.metadata,json,subprocess,sys,urllib.request
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if not Path(sys.prefix).resolve().is_relative_to(ROOT):raise SystemExit('Use the project .venv Python')
    versions=json.loads((ROOT/'docs/tool_versions.json').read_text())
    folder=ROOT/'tools/undark';folder.mkdir(parents=True,exist_ok=True)
    commit=versions['undark']['commit']
    for name in ['undark.c','varint.c','varint.h','LICENSE']:
        p=folder/name;expected=versions['hashes']['tools/undark/'+name]
        if not p.exists():
            url=f'https://raw.githubusercontent.com/inflex/undark/{commit}/{name}'
            with urllib.request.urlopen(url,timeout=30) as r:payload=r.read(200_001)
            if len(payload)>200_000 or hashlib.sha256(payload).hexdigest()!=expected:raise ValueError('Source hash mismatch')
            p.write_bytes(payload)
        if sha(p)!=expected:raise ValueError('Existing source hash mismatch: '+name)
    original=(folder/'undark.c').read_text();assert original.count('ntohll')==2
    portable=original.replace('ntohll','undark_ntohll')
    (folder/'undark.portable.c').write_text(portable)
    compiler=subprocess.check_output(['clang','--version'],text=True)
    proc=subprocess.run(['clang',str(folder/'undark.portable.c'),str(folder/'varint.c'),'-o',str(folder/'undark')],capture_output=True,text=True)
    logdir=ROOT/'data/interim/tool-setup'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    logdir.mkdir(parents=True,exist_ok=False)
    (logdir/'undark_build.txt').write_text(proc.stdout+proc.stderr)
    proc.check_returncode()
    import sqlite_dissect
    dist=importlib.metadata.distribution('sqlite_dissect')
    direct=json.loads(dist.read_text('direct_url.json'))
    expected_source=versions['sqlite_dissect']
    if 'vcs_info' in direct:
        assert direct['vcs_info']['commit_id']==expected_source['commit']
    else:
        assert direct['url']==expected_source['archive_url']
        assert direct['archive_info']['hashes']['sha256']==expected_source['archive_sha256']
    p=Path(sqlite_dissect.__file__).parent/'carving/carved_cell.py'
    text=p.read_text()
    if sha(p)==versions['sqlite_dissect']['upstream_carved_cell_sha256']:
        patched=text.replace('record_column_md5_hash_strings = [""]','record_column_md5_hash_strings = [b""]')
        patched=patched.replace('record_column_md5_hash_strings[column_index] = ""','record_column_md5_hash_strings[column_index] = b""')
        assert patched!=text
        patch=''.join(difflib.unified_diff(text.splitlines(True),patched.splitlines(True),fromfile='upstream/carved_cell.py',tofile='local/carved_cell.py'))
        assert patch==(ROOT/'docs/evidence/dissect_bytes_compatibility.patch').read_text()
        p.write_text(patched)
    expected=next(v for k,v in versions['hashes'].items() if k.endswith('carved_cell.py'))
    assert sha(p)==expected,'Unexpected local Dissect source; refusing to modify'
    # These describe this local build; experiment manifests snapshot them per run.
    versions['compiler']=compiler;versions['hashes']['tools/undark/undark']=sha(folder/'undark')
    versions['hashes']['tools/undark/undark.portable.c']=sha(folder/'undark.portable.c')
    (ROOT/'docs/tool_versions.json').write_text(json.dumps(versions,indent=2)+'\n')
    print('Pinned sources verified; Undark built; Dissect compatibility patch verified. Build log:',logdir.relative_to(ROOT))
if __name__=='__main__':main()
