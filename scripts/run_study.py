"""Run both tools, validate inputs, retain raw outputs, and score every candidate."""
from pathlib import Path
import argparse,csv,hashlib,json,os,platform,subprocess,sys,time
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from p2study.corpus import read_case,publisher_checksums,sha
from p2study.scoring import normalize,row_equal,score,metrics

def write_csv(path,rows,fields=None):
    if not rows and fields is None:raise ValueError('No columns')
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cases',nargs='+');ap.add_argument('--run-id')
    args=ap.parse_args();started=datetime.now(timezone.utc)
    runid=args.run_id or started.strftime('%Y%m%dT%H%M%S%fZ')
    run=ROOT/'data/interim/runs'/runid;run.mkdir(parents=True,exist_ok=False)
    out=ROOT/'results'/runid;out.mkdir(parents=True,exist_ok=False)
    corpus=ROOT/'data/raw/sqlite_forensic_corpus_v2.0'
    verified=publisher_checksums(corpus)
    paths=sorted((corpus/'0C').glob('*.db'))
    if args.cases:paths=[p for p in paths if p.stem in args.cases];assert len(paths)==len(set(args.cases))
    cases=[read_case(p) for p in paths];assert cases
    samples=[];scores=[];matches=[];events=[];truth=[]
    for c in cases:
        samples.append(dict(case=c['case'],eligibility='Eligible',reason='XML counts, SQL DELETE IDs, live rows, schema and checksums agree',tables=len(c['tables']),columns=len(c['kinds']),types='/'.join(c['kinds']),condition=c['condition'],live=len(c['live']),deleted=len(c['gold']),bytes=c['bytes'],sha256=c['sha256'],xml_sha256=c['xml_sha256'],sql_sha256=c['sql_sha256']))
        for j,g in enumerate(c['gold']):truth.append(dict(case=c['case'],gold_index=j,table=g['table'],values=json.dumps(g['values'],ensure_ascii=False)))
        for tool in ['undark','sqlite_dissect']:
            d=run/c['case']/tool;d.mkdir(parents=True)
            db=str(c['db'].relative_to(ROOT))
            if tool=='undark':cmd=['tools/undark/undark','-i',db]
            else:
                # Use the environment executing this script, not an older .venv.
                executable=Path(sys.executable).parent/'sqlite_dissect'
                if not executable.is_file():raise RuntimeError('Install requirements in the active Python environment')
                command_path=str(executable.relative_to(ROOT)) if executable.is_relative_to(ROOT) else str(executable)
                cmd=[command_path,db,'-n','-c','-f','-e','csv','-d',str((d/'csv').relative_to(ROOT))]
            t=time.monotonic();timeout=False
            try:
                with (d/'stdout.txt').open('wb') as so,(d/'stderr.txt').open('wb') as se:
                    proc=subprocess.run(cmd,cwd=ROOT,stdout=so,stderr=se,timeout=60,env=dict(os.environ,PYTHONHASHSEED='0'))
                rc=proc.returncode
            except subprocess.TimeoutExpired:rc=None;timeout=True
            event=dict(case=c['case'],tool=tool,command=cmd,returncode=rc,timeout=timeout,seconds=time.monotonic()-t,stdout=str((d/'stdout.txt').relative_to(ROOT)),stderr=str((d/'stderr.txt').relative_to(ROOT)))
            events.append(event)
            if rc!=0:
                event['status']='execution_failed_not_scored';continue
            records=[];allocated=0
            if tool=='undark':
                with (d/'stdout.txt').open(encoding='utf-8',errors='replace',newline='') as f:
                    for n,row in enumerate(csv.reader(f)):
                        if not row:continue
                        records.append(dict(values=row[1:],provenance=f'CSV row {n+1}; rowid={row[0]}'))
            else:
                for p in sorted((d/'csv').glob('*.csv')):
                    with p.open(encoding='utf-8-sig',errors='replace',newline='') as f:
                        reader=csv.reader(f);header=next(reader)
                        assert header[:9]==['File Source','Version','Page Version','Cell Source','Page Number','Location','Operation','File Offset','Row ID']
                        for row in reader:
                            assert len(row)==len(header),'Malformed exported CSV'
                            if row[6]!='Carved':allocated+=1;continue
                            records.append(dict(values=row[9:],provenance=f'{p.name}; offset={row[7]}; {row[5]}'))
            preds=[];excluded=0
            for r in records:
                v=r['values']
                r['values']=[normalize(x,k) for x,k in zip(v,c['kinds'])] if len(v)==len(c['kinds']) else v
                if any(row_equal(r['values'],v,c['kinds']) for v in c['live']):excluded+=1;continue
                preds.append(r)
            m,labels=score([r['values'] for r in preds],[g['values'] for g in c['gold']],c['kinds'])
            scores.append(dict(case=c['case'],tool=tool,condition=c['condition'],status='completed',gold=len(c['gold']),candidates=len(preds),allocated_rows_ignored=allocated,live_matches_excluded=excluded,**m))
            for n,(r,label) in enumerate(zip(preds,labels)):
                j=label['gold_index'];g=c['gold'][j] if j is not None else None
                matches.append(dict(case=c['case'],tool=tool,candidate=n,**label,values=json.dumps(r['values'],ensure_ascii=False),gold_values=json.dumps(g['values'],ensure_ascii=False) if g else '',provenance=r['provenance']))
            matched={l['gold_index'] for l in labels if l['gold_index'] is not None}
            for j,g in enumerate(c['gold']):
                if j not in matched:matches.append(dict(case=c['case'],tool=tool,candidate='',outcome='not_recovered',gold_index=j,values='',gold_values=json.dumps(g['values'],ensure_ascii=False),provenance='XML reference'))
            event.update(status='completed',candidates=len(preds),output_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(d.rglob('*')) if p.is_file()})
            assert sha(c['db'])==c['sha256'],'Tool modified original input'
    write_csv(out/'samples.csv',samples);write_csv(out/'truth.csv',truth)
    if scores:write_csv(out/'per_case.csv',scores)
    if matches:write_csv(out/'record_matches.csv',matches)
    aggregate=[]
    for tool in ['undark','sqlite_dissect']:
        s=[r for r in scores if r['tool']==tool]
        if s:aggregate.append(dict(tool=tool,completed_cases=len(s),eligible_cases=len(cases),**metrics(*[sum(r[k] for r in s) for k in ['tp','fp','fn']]),partial=sum(r['partial'] for r in s),not_recovered=sum(r['not_recovered'] for r in s),incorrect_or_unattributed=sum(r['incorrect_or_unattributed'] for r in s)))
    if aggregate:write_csv(out/'comparison.csv',aggregate)
    manifest=dict(run_id=runid,started_at=started.isoformat(),finished_at=datetime.now(timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),sqlite_version=__import__('sqlite3').sqlite_version,publisher_checksums_verified=verified,events=events,source_hashes={str(p.relative_to(ROOT)):sha(p) for folder in ['src','scripts'] for p in sorted((ROOT/folder).rglob('*.py'))},tools=json.loads((ROOT/'docs/tool_versions.json').read_text()))
    (out/'run.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(aggregate,indent=2));print('Saved',out.relative_to(ROOT))
    if any(e['status']!='completed' for e in events):sys.exit('Some executions failed; not scored. Inspect run.json.')
if __name__=='__main__':main()
