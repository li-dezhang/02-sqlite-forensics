"""Content-only, one-to-one scoring. No table or SQLite rowid recovery claim."""
import math
REAL_ATOL = 1e-5  # Corpus REAL literals carry five decimal places; no relative tolerance.

def normalize(value, kind):
    if value is None:
        return None
    try:
        if kind == 'INTEGER':
            return int(value)
        if kind == 'REAL':
            return float(value)
    except (ValueError, TypeError, OverflowError):
        return value  # Preserve malformed outputs, never silently drop a candidate.
    return value

def field_equal(a, b, kind):
    if a is None or b is None:
        return a is b
    if kind == 'REAL' and isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= REAL_ATOL
    return type(a) is type(b) and a == b

def row_equal(a, b, kinds):
    return len(a) == len(b) == len(kinds) and all(field_equal(x,y,k) for x,y,k in zip(a,b,kinds))

def metrics(tp, fp, fn):
    return dict(tp=tp, fp=fp, fn=fn,
                precision=tp/(tp+fp) if tp+fp else None,
                recall=tp/(tp+fn) if tp+fn else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)

def score(predictions, gold, kinds):
    """Gold/predictions are value vectors. Duplicates remain FP after one TP.

    Partial is diagnostic only: an unmatched, uniquely identified gold row has
    the same first-column ID and at least one other correct field. It stays FN;
    its candidate stays FP under strict complete-record scoring.
    """
    unused=set(range(len(gold)))
    labels=[{'outcome':'incorrect_or_unattributed','gold_index':None} for _ in predictions]
    for i,p in enumerate(predictions):
        matches=[j for j in sorted(unused) if row_equal(p,gold[j],kinds)]
        if matches:
            j=matches[0]; unused.remove(j)
            labels[i]={'outcome':'complete','gold_index':j}
    tp=len(gold)-len(unused)
    partial=set()
    for i,p in enumerate(predictions):
        if labels[i]['outcome']=='complete' or len(p)!=len(kinds):continue
        matches=[j for j in sorted(unused-partial)
                 if field_equal(p[0],gold[j][0],kinds[0])
                 and any(field_equal(x,y,k) for x,y,k in zip(p[1:],gold[j][1:],kinds[1:]))]
        if len(matches)==1:
            j=matches[0];partial.add(j)
            labels[i]={'outcome':'partial','gold_index':j}
    return dict(metrics(tp,len(predictions)-tp,len(gold)-tp),
                partial=len(partial),not_recovered=len(unused-partial),
                incorrect_or_unattributed=len(predictions)-tp-len(partial)),labels
