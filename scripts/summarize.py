"""Generate figures and secondary tables directly from a completed run's CSV files."""
from pathlib import Path
import argparse,csv,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import p2study.scoring as scoring
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from run_study import write_csv

def rows(path):return list(csv.DictReader(path.open(encoding='utf-8',newline='')))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);a=ap.parse_args()
    out=ROOT/'results'/a.run_id;fig=ROOT/'figures'/a.run_id;fig.mkdir(parents=True,exist_ok=True)
    comp=rows(out/'comparison.csv');per=rows(out/'per_case.csv');samples=rows(out/'samples.csv')
    records=rows(out/'record_matches.csv');truth=rows(out/'truth.csv')
    assert all(int(r['completed_cases'])==int(r['eligible_cases']) for r in comp),'Do not plot incomplete runs as full comparisons'
    groups=[]
    for tool in ['undark','sqlite_dissect']:
        for condition in ['partial_deletion','all_deleted']:
            r=[r for r in per if r['tool']==tool and r['condition']==condition]
            if r:groups.append(dict(tool=tool,condition=condition,cases=len(r),**scoring.metrics(*[sum(int(x[k]) for x in r) for k in ['tp','fp','fn']])))
    write_csv(out/'by_condition.csv',groups)
    sensitivity=[]
    for tol in [1e-5,1e-4,1e-3]:
        scoring.REAL_ATOL=tol
        for tool in ['undark','sqlite_dissect']:
            counts=[0,0,0]
            for sample in samples:
                case=sample['case'];kinds=sample['types'].split('/')
                g=[json.loads(r['values']) for r in truth if r['case']==case]
                p=[json.loads(r['values']) for r in records if r['case']==case and r['tool']==tool and r['candidate']!='']
                m,_=scoring.score(p,g,kinds)
                counts=[x+m[k] for x,k in zip(counts,['tp','fp','fn'])]
            sensitivity.append(dict(real_absolute_tolerance=tol,tool=tool,**scoring.metrics(*counts)))
    scoring.REAL_ATOL=1e-5
    for r in sensitivity[:2]:
        c=next(x for x in comp if x['tool']==r['tool'])
        assert all(r[k]==int(c[k]) for k in ['tp','fp','fn'])
    write_csv(out/'real_tolerance_sensitivity.csv',sensitivity)
    names={'undark':'Undark 0.7.1*','sqlite_dissect':'SQLite Dissect 1.0.0*'}
    colors=['#51677d','#087f8c']
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    f,ax=plt.subplots(figsize=(8.4,5.2))
    for i,c in enumerate(comp):
        v=[float(c[k]) for k in ['precision','recall','f1']]
        bars=ax.bar([x+(i-.5)*.34 for x in range(3)],v,width=.34,label=names[c['tool']],color=colors[i])
        ax.bar_label(bars,labels=[f'{x:.1%}' for x in v],padding=4,fontsize=10)
    ax.set(xticks=range(3),xticklabels=['Precision','Recall','F1'],ylim=(0,1),ylabel='Micro-averaged score',title='Strict complete-record recovery | 10 synthetic 0C databases')
    ax.legend(loc='upper right',frameon=False)
    f.text(.08,.015,'101 deleted records; content-only matching. *Documented compatibility patches.',fontsize=9)
    f.tight_layout(rect=(0,.04,1,1));f.savefig(fig/'performance.png',dpi=180);f.savefig(fig/'performance.svg');plt.close(f)
    f,ax=plt.subplots(figsize=(10,5.2))
    cases=[s['case'] for s in samples]
    for i,tool in enumerate(['undark','sqlite_dissect']):
        r={x['case']:x for x in per if x['tool']==tool}
        ax.plot(cases,[float(r[c]['recall']) for c in cases],marker='o',label=names[tool],color=colors[i])
    ax.set(ylim=(-.04,1.08),ylabel='Strict complete-record recall',title='Observed recovery varies across crafted cases')
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.2)
    f.tight_layout();f.savefig(fig/'recall_by_case.png',dpi=180);f.savefig(fig/'recall_by_case.svg');plt.close(f)
    manifest={'run_id':a.run_id,'source':'comparison.csv and per_case.csv in the corresponding results directory','metric':'strict content-only complete-record matching','files':['performance.png','performance.svg','recall_by_case.png','recall_by_case.svg']}
    (fig/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Figures and secondary tables saved:',a.run_id)
if __name__=='__main__':main()
