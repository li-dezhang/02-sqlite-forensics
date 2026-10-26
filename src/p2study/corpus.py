"""Read immutable originals; validate reference labels without executing corpus SQL."""
import hashlib, re, sqlite3
import xml.etree.ElementTree as ET
from .scoring import normalize, row_equal

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def inserted_rows(sql, table):
    """Strict parser for this corpus's literal INSERT tuples; no SQL execution."""
    bodies=re.findall(r'INSERT\s+INTO\s+'+re.escape(table)+r'\b[^;]*?VALUES\s*(.*?);',sql,re.I|re.S)
    rows=[]
    token=re.compile(r"\s*('(?:''|[^'])*'|NULL|[-+]?\d+(?:\.\d+)?)\s*(,|$)",re.I)
    for body in bodies:
        for raw in re.findall(r'\(([^()]*)\)',body):
            values=[];offset=0
            while offset<len(raw):
                m=token.match(raw,offset)
                if not m:raise ValueError('Unsupported SQL literal')
                value=m[1]
                if value.startswith("'"):values.append(value[1:-1].replace("''","'"))
                elif value.upper()=='NULL':values.append(None)
                else:values.append(float(value) if '.' in value else int(value))
                offset=m.end()
            rows.append(values)
    return rows

def publisher_checksums(root):
    count=0
    for line in (root/'sha256sums.txt').read_text().splitlines():
        if not line.strip():continue
        expected,name=line.split(maxsplit=1);p=root/name.removeprefix('./')
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe checksum path')
        if sha(p)!=expected:raise ValueError('Publisher checksum mismatch: '+name)
        count+=1
    return count

def read_case(db):
    tree=ET.parse(db.with_suffix('.xml')).getroot()
    sql=db.with_suffix('.sql').read_text(encoding='utf-8-sig')
    conn=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    conn.execute('PRAGMA query_only=ON')
    assert conn.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
    tables=[];gold=[];live=[];kinds=None
    for e in tree.findall('element'):
        if e.findtext('meta/type')!='table':continue
        name=e.findtext('meta/name');cols=e.findall('sql/columnDefinition')
        names=[c.findtext('meta/name') for c in cols]
        types=[c.findtext('columnTypeName') for c in cols]
        if kinds is None:kinds=types
        if kinds!=types:raise ValueError('Different type layouts need a separate adapter')
        qt='"'+name.replace('"','""')+'"'
        actual_cols=[r[1] for r in conn.execute('PRAGMA table_info('+qt+')')]
        assert actual_cols==names,(db,name,'schema mismatch')
        actual=[list(r) for r in conn.execute('SELECT * FROM '+qt)]
        alive=[];deleted=[]
        for r in e.findall('entries/row'):
            cs=r.findall('column');assert [c.findtext('name') for c in cs]==names
            vals=[normalize(c.findtext('content'),k) for c,k in zip(cs,types)]
            (deleted if r.get('deleted')=='1' else alive).append(vals)
        assert len(alive)==int(e.findtext('meta/rowsAlive'))
        assert len(deleted)==int(e.findtext('meta/rowsDeleted'))
        assert len(alive)+len(deleted)==int(e.findtext('meta/rowsTotal'))
        inserted=inserted_rows(sql,name)
        assert len(inserted)==len(alive)+len(deleted),'INSERT/reference count mismatch'
        for r in alive+deleted:
            hits=[i for i,a in enumerate(inserted) if row_equal(r,a,types)]
            assert len(hits)==1,(db,name,'INSERT/XML value mismatch',r)
            inserted.pop(hits[0])
        assert len(alive)==len(actual)
        remaining=actual.copy()
        for r in alive:
            hits=[i for i,a in enumerate(remaining) if row_equal(r,a,types)]
            assert len(hits)==1,(db,name,r,'live mismatch')
            remaining.pop(hits[0])
        # Only supported literal DELETE statements are parsed, never executed.
        statements=re.findall(r'DELETE\s+FROM\s+'+re.escape(name)+r'\b([^;]*);',sql,re.I)
        assert statements,(db,name,'no DELETE evidence')
        ids=[];all_deleted=False
        for s in statements:
            if not s.strip():all_deleted=True;continue
            m=re.fullmatch(r'\s*where\s+'+re.escape(names[0])+r'\s*==\s*(-?\d+)\s*',s,re.I)
            assert m,(db,name,'unsupported DELETE',s)
            ids.append(int(m[1]))
        if all_deleted:assert not alive and len(deleted)>0
        else:assert sorted(ids)==sorted(r[0] for r in deleted),(db,name,'DELETE/XML mismatch')
        assert re.search(r'PRAGMA\s+secure_delete\s*=\s*0\s*;',sql,re.I)
        for r in deleted:gold.append({'table':name,'values':r})
        live.extend(actual)
        tables.append({'name':name,'columns':names,'types':types,'alive':len(alive),'deleted':len(deleted)})
    conn.close()
    for i,r in enumerate(gold):
        assert not any(row_equal(r['values'],v,kinds) for v in live),'Deleted/live ambiguity'
        assert not any(row_equal(r['values'],v['values'],kinds) for v in gold[:i]),'Content attribution ambiguity'
    return dict(case=db.stem,db=db,tables=tables,kinds=kinds,gold=gold,live=live,
                condition='all_deleted' if not live else 'partial_deletion',bytes=db.stat().st_size,
                sha256=sha(db),xml_sha256=sha(db.with_suffix('.xml')),sql_sha256=sha(db.with_suffix('.sql')))
