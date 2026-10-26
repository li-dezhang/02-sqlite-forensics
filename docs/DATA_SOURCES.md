# P2 verified data source — 2026-10-21

- Official collection page: https://digitalcorpora.org/corpora/sql/sqlite-forensic-corpus/
- Official hosting explanation: https://digitalcorpora.org/about-digitalcorpora/s3-information/
- Actual acquired object: https://digitalcorpora.s3.amazonaws.com/corpora/sql/sqlite_forensic_corpus_v2.0.zip
- Licence: package CC0 1.0 Universal; XML rights consistent with official public-domain description.
- Verified archive: 5,370,116 bytes, version 2.0; SHA-256 `8d71ff0ca595716b60ca7b6e9f0c7789e4612383f230e3742c9fc06ad39e95d8`.
- Actual contents: 141 DB/SQL/XML triples; 557 total files. Package version history identifies v2 as the original 77 examples plus 64 anti-forensic examples. All 556 supplied checksums match.
- Tested subset: 10 category 0C databases, 101 deleted and 189 live rows. XML labels, INSERT values, DELETE statements, schema and live rows agree. No missing answer file in this subset.
- Unassessed: deletion-reference eligibility of other categories; generalization beyond these crafted examples; other platforms and untested tool releases.

See `data/manifest.json`, `docs/evidence/acquisition_20261021.json`, `results/final-20261021/samples.csv`. This is an acquisition and experiment record, not a fabricated historical approval.
