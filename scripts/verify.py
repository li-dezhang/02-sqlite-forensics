"""Check conservation, recomputed scores and published table/report agreement."""
from pathlib import Path
import argparse,csv,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from p2study.scoring import metrics,score
from p2study.corpus import sha

def read(p):return list(csv.DictReader(p.open(newline='',encoding='utf-8')))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);a=ap.parse_args()
    out=ROOT/'results'/a.run_id;per=read(out/'per_case.csv');comp=read(out/'comparison.csv')
    samples=read(out/'samples.csv');truth=read(out/'truth.csv');records=read(out/'record_matches.csv')
    for r in per:
        assert int(r['tp'])+int(r['fn'])==int(r['gold'])
        assert int(r['tp'])+int(r['fp'])==int(r['candidates'])
        assert int(r['tp'])+int(r['partial'])+int(r['not_recovered'])==int(r['gold'])
        p=[json.loads(x['values']) for x in records if x['case']==r['case'] and x['tool']==r['tool'] and x['candidate']!='']
        g=[json.loads(x['values']) for x in truth if x['case']==r['case']]
        kinds=next(x['types'].split('/') for x in samples if x['case']==r['case'])
        m,_=score(p,g,kinds)
        assert all(m[k]==int(r[k]) for k in ['tp','fp','fn','partial','not_recovered'])
    for c in comp:
        rows=[r for r in per if r['tool']==c['tool']]
        m=metrics(*[sum(int(r[k]) for r in rows) for k in ['tp','fp','fn']])
        assert len(rows)==len(samples)==int(c['completed_cases'])
        for k,v in m.items():assert abs(float(c[k])-v)<1e-12
    published=read(ROOT/'results/final-20261021/comparison.csv')
    # This report describes the named final run. New runs are compared, not rewritten.
    for c in published:
        name={'undark':'Undark 0.7.1','sqlite_dissect':'SQLite Dissect 1.0.0'}[c['tool']]
        line='| '+name+' | '+' | '.join(c[k] for k in ['tp','fp','fn'])+' | '+' | '.join(f'{float(c[k]):.2%}' for k in ['precision','recall','f1'])+' |'
        for p in ['README.md','report/RESEARCH_REPORT.md']:
            assert line in (ROOT/p).read_text(),f'{p}: comparison table mismatch'
    if comp!=published:raise SystemExit('Run is valid but differs from the published pilot. Review before updating report.')
    figures=ROOT/'figures'/a.run_id
    for name in ['performance.png','performance.svg','recall_by_case.png','recall_by_case.svg']:
        assert (figures/name).stat().st_size>0
    run=json.loads((out/'run.json').read_text());assert all(e['returncode']==0 for e in run['events'])
    for s in samples:
        db=ROOT/'data/raw/sqlite_forensic_corpus_v2.0/0C'/(s['case']+'.db')
        assert sha(db)==s['sha256']
    result={'run_id':a.run_id,'checks':'record-level rescoring, denominators, input hashes, complete executions, figure files, README/report comparison tables','passed':True,'matches_published_counts':True}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
