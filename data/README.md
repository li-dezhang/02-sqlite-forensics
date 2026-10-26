# Dataset

Official page: https://digitalcorpora.org/corpora/sql/sqlite-forensic-corpus/

Official public object: https://digitalcorpora.s3.amazonaws.com/corpora/sql/sqlite_forensic_corpus_v2.0.zip

Acquired 2026-10-21: **5,370,116 bytes**; SHA-256 `8d71ff0ca595716b60ca7b6e9f0c7789e4612383f230e3742c9fc06ad39e95d8`.

The package's `license.txt` is CC0 1.0 Universal, consistent with the official public-domain description. XML rights statements also specify CC0. Local research use is within the user's authorization. No authentication or access restriction was bypassed.

557 extracted files: 141 `.db`, 141 `.sql`, 141 `.xml`, 64 `.db_recovery`, 64 `.log`, 6 `.txt`. The supplied checksum list covers 556 files (not itself); all pass. `manifest.json` records every extracted file's actual hash and size.

Run `python scripts/acquire.py` from the P2 directory. The downloader caps the research archive at 20 MB, checks its expected hash and licence, rejects unsafe ZIP paths, links, duplicate entries and oversized expansion, then makes extracted files read-only. Existing matching data is verified without downloading again. A changed upstream archive stops the script for source/version review. Do not execute supplied SQL. No unknown corpus program has been executed.

`raw/` holds the archive and extracted originals. `interim/runs/` holds actual tool stdout, stderr and CSV exports. Both are Git-ignored. Only derived summaries and small public synthetic-record matching examples are selected for publication. No original database or archive is included.

The study uses `raw/sqlite_forensic_corpus_v2.0/0C/0C-01.db` through `0C-10.db` with their matching SQL/XML documents. Labels are publisher XML deletion markers, corroborated by literal SQL and independently queried live rows; predictions are never reference labels. All ten cases are eligible for the defined content-recovery endpoint. The other 131 databases are **outside scope and unassessed**, not declared invalid or irrecoverable.
