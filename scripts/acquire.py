"""Acquire only the public, bounded SQLite corpus; never execute corpus files."""
from pathlib import Path, PurePosixPath
import urllib.request, hashlib, json, zipfile, stat
from datetime import datetime, timezone
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
URL='https://digitalcorpora.s3.amazonaws.com/corpora/sql/sqlite_forensic_corpus_v2.0.zip'
LIMIT=20_000_000
EXPECTED_SHA='8d71ff0ca595716b60ca7b6e9f0c7789e4612383f230e3742c9fc06ad39e95d8'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def safe_extract(z,dest):
    infos=z.infolist()
    if len(infos)>5000 or sum(i.file_size for i in infos)>100_000_000: raise ValueError('Extraction budget exceeded')
    seen=set()
    for i in infos:
        p=PurePosixPath(i.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in i.filename or i.filename in seen: raise ValueError('Unsafe member')
        seen.add(i.filename)
        mode=i.external_attr>>16
        if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)): raise ValueError('Non-regular member')
        out=dest.joinpath(*p.parts)
        if not out.resolve().is_relative_to(dest.resolve()) or out.exists(): raise ValueError('Unsafe destination or existing content')
    for i in infos:
        out=dest.joinpath(*PurePosixPath(i.filename).parts)
        if i.is_dir():out.mkdir(parents=True,exist_ok=True);continue
        out.parent.mkdir(parents=True,exist_ok=True)
        with z.open(i) as src,out.open('xb') as dst:
            total=0
            while b:=src.read(65536):
                total+=len(b)
                if total>i.file_size:raise ValueError('Uncompressed size mismatch')
                dst.write(b)
        out.chmod(0o444)

def main():
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    archive=raw/'sqlite_forensic_corpus_v2.0.zip'
    if archive.exists():
        if sha(archive)!=EXPECTED_SHA:raise ValueError('Existing archive hash mismatch')
        manifest=json.loads((ROOT/'data/manifest.json').read_text())
        for f in manifest['files']:
            if sha(ROOT/f['path'])!=f['sha256']:raise ValueError('Existing extracted data mismatch')
        print('Existing archive and extracted files verified; no network request;',sha(archive));return
    temp=archive.with_suffix('.part')
    event={'started_at':datetime.now(timezone.utc).isoformat(),'url':URL,'limit_bytes':LIMIT}
    try:
        with urllib.request.urlopen(URL,timeout=30) as response,temp.open('xb') as f:
            event.update(final_url=response.url,headers=dict(response.headers),status=response.status)
            if int(response.headers.get('Content-Length',0))>LIMIT:raise ValueError('Download exceeds limit')
            n=0
            while b:=response.read(min(65536,LIMIT-n+1)):
                n+=len(b)
                if n>LIMIT:raise ValueError('Download exceeds limit')
                f.write(b)
        if not zipfile.is_zipfile(temp):raise ValueError('Not ZIP')
        if sha(temp)!=EXPECTED_SHA:raise ValueError('Official archive changed: review before acquisition continues')
        temp.rename(archive);archive.chmod(0o444)
        with zipfile.ZipFile(archive) as z:
            license_names=[i.filename for i in z.infolist() if i.filename.lower().endswith('license.txt')]
            event['license_text']={name:z.read(name).decode('utf-8',errors='replace') for name in license_names}
            if not any('CC0 1.0 Universal' in s for s in event['license_text'].values()):raise ValueError('Expected CC0 licence missing')
            print(json.dumps(event['license_text'],ensure_ascii=False))
            # Read licence before allowing scientific use. Extraction itself is non-executing inspection.
            safe_extract(z,raw)
        files=[p for p in (raw/'sqlite_forensic_corpus_v2.0').rglob('*') if p.is_file()]
        manifest={'status':'acquired','dataset_version':'2.0','source_url':URL,'retrieved_at':event['started_at'],'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'file_count':len(files),'types':dict(Counter(p.suffix for p in files)),'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]}
        (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        event.update(outcome='downloaded_and_safely_extracted',bytes=archive.stat().st_size,sha256=sha(archive))
        print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))
    except Exception as e:
        event.update(outcome='failed',error=repr(e));raise
    finally:
        (ROOT/'docs/evidence/acquisition_20261021.json').write_text(json.dumps(event,indent=2)+'\n')
if __name__=='__main__':main()
