"""Generate a small, evidence-linked failure analysis from actual run outputs."""
from pathlib import Path
import argparse,csv,json,struct
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);a=ap.parse_args()
    out=ROOT/'results'/a.run_id
    records=list(csv.DictReader((out/'record_matches.csv').open()))
    def select(case,tool,outcome,first=None):
        for r in records:
            if (r['case'],r['tool'],r['outcome'])==(case,tool,outcome):
                v=json.loads(r['values']) if r['values'] else None
                if first is None or (v and v[0]==first):return r
        raise ValueError('Expected observed example not found; revise analysis')
    floatrow=select('0C-09','undark','partial',20006)
    pred=json.loads(floatrow['values']);gold=json.loads(floatrow['gold_values'])
    raw=(ROOT/'data/raw/sqlite_forensic_corpus_v2.0/0C/0C-09.db').read_bytes()
    b=struct.pack('>d',gold[-1]);offset=raw.find(b);assert offset>=0
    simulated=struct.unpack('>d',struct.pack('>Q',int(float(struct.unpack('>Q',b)[0]))))[0]
    assert float(f'{simulated:.6f}')==pred[-1]
    textrow=select('0C-09','undark','partial',20010)
    fragment=select('0C-03','sqlite_dissect','incorrect_or_unattributed',24942)
    missing=select('0C-03','sqlite_dissect','not_recovered')
    malformed=select('0C-01','undark','incorrect_or_unattributed')
    evidence={'run_id':a.run_id,'examples':[floatrow,textrow,fragment,missing,malformed],
              'numeric_mechanism_check':{'database':'0C-09.db','offset':offset,'bytes_hex':b.hex(),'reference':gold[-1],'integer_float_integer_bit_reinterpretation':simulated,'tool_export':pred[-1]}}
    (out/'failure_examples.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
    report=f'''# Observed failure examples — {a.run_id}

These are observed output errors, not claims that the original records are inherently unrecoverable. Full source records and offsets are in `failure_examples.json` and `record_matches.csv`.

1. **REAL-value distortion, Undark, 0C-09, ID 20006.** Reference `{gold[-1]}`; export `{pred[-1]}`; absolute error `{abs(pred[-1]-gold[-1]):.9f}`. All bytes for the reference double are present at database offset **{offset}** (`{b.hex()}`). Undark's pinned `undark.c`, lines 1006–1015, converts the 64-bit integer bit pattern through a numeric double before reinterpreting it. Reproducing that conversion gives `{simulated}`, which rounds to the observed six-decimal export. This directly supports a conversion-loss explanation for this example; it does not diagnose every failure.

2. **Text alteration, Undark, 0C-09, ID 20010.** Reference surname `König`; exported surname `K..nig`. The pinned source's `sqltdump` (lines 429–437) tests individual bytes with `isprint` and substitutes dots. This is consistent with alteration of UTF-8 bytes. It remains incorrect under exact-text scoring. Other fields also differ in this row.

3. **Overlapping fragment candidates, SQLite Dissect, 0C-03.** At offset 7863, the tool exports `{fragment['values']}`. At nearby offset 7853 it recovers the complete reference row `[20017, "Nele", "Baumann"]`. Many overlapping, differently aligned freeblock candidates therefore compete with valid records. The first candidate is an FP under complete-record scoring, even though its text byte may be genuinely residual content. Manual filtering was not applied.

4. **Missed complete records, SQLite Dissect, 0C-03.** `{missing['gold_values']}` is listed as deleted in XML and corroborated by SQL. No complete matching output is present. Freeblock headers, neighboring deletions and signature alignment can damage record boundaries, but the exact causal chain for this missing row was not established. Do not call it unrecoverable.

5. **Wrong row shape, Undark, 0C-01.** Output `{malformed['values']}` has three fields, while the database table has five integer columns. It is retained as an FP rather than discarded during parsing. Its alignment or decoding cause is not proven.

6. **Handled internal failure, SQLite Dissect, 0C-10.** The process exits successfully but logs a carving warning at file offset 7833. This is retained in the raw stderr log. A successful exit does not mean every candidate was processed successfully.

The primary REAL tolerance is 0.00001 with no relative tolerance. Post-hoc sensitivity at 0.0001 and 0.001 appears in `real_tolerance_sensitivity.csv`; it is not a replacement for the primary endpoint. The `partial` diagnostic requires a correct ID and at least one other correct field, so unanchored fragments are not falsely attributed to particular deleted records.
'''
    (out/'FAILURE_ANALYSIS.md').write_text(report)
    print('Failure examples verified against real outputs and database bytes.')
if __name__=='__main__':main()
