# Observed failure examples — final-20261021

These are observed output errors, not claims that the original records are inherently unrecoverable. Full source records and offsets are in `failure_examples.json` and `record_matches.csv`.

1. **REAL-value distortion, Undark, 0C-09, ID 20006.** Reference `2055417409.65816`; export `2055417409.658203`; absolute error `0.000042915`. All bytes for the reference double are present at database offset **7996** (`41dea0cb906a1f4b`). Undark's pinned `undark.c`, lines 1006–1015, converts the 64-bit integer bit pattern through a numeric double before reinterpreting it. Reproducing that conversion gives `2055417409.6582031`, which rounds to the observed six-decimal export. This directly supports a conversion-loss explanation for this example; it does not diagnose every failure.

2. **Text alteration, Undark, 0C-09, ID 20010.** Reference surname `König`; exported surname `K..nig`. The pinned source's `sqltdump` (lines 429–437) tests individual bytes with `isprint` and substitutes dots. This is consistent with alteration of UTF-8 bytes. It remains incorrect under exact-text scoring. Other fields also differ in this row.

3. **Overlapping fragment candidates, SQLite Dissect, 0C-03.** At offset 7863, the tool exports `[24942, "n", ""]`. At nearby offset 7853 it recovers the complete reference row `[20017, "Nele", "Baumann"]`. Many overlapping, differently aligned freeblock candidates therefore compete with valid records. The first candidate is an FP under complete-record scoring, even though its text byte may be genuinely residual content. Manual filtering was not applied.

4. **Missed complete records, SQLite Dissect, 0C-03.** `[20002, "Lukas", "Wolff"]` is listed as deleted in XML and corroborated by SQL. No complete matching output is present. Freeblock headers, neighboring deletions and signature alignment can damage record boundaries, but the exact causal chain for this missing row was not established. Do not call it unrecoverable.

5. **Wrong row shape, Undark, 0C-01.** Output `["1308622848", "36956", "-14497748"]` has three fields, while the database table has five integer columns. It is retained as an FP rather than discarded during parsing. Its alignment or decoding cause is not proven.

6. **Handled internal failure, SQLite Dissect, 0C-10.** The process exits successfully but logs a carving warning at file offset 7833. This is retained in the raw stderr log. A successful exit does not mean every candidate was processed successfully.

The primary REAL tolerance is 0.00001 with no relative tolerance. Post-hoc sensitivity at 0.0001 and 0.001 appears in `real_tolerance_sensitivity.csv`; it is not a replacement for the primary endpoint. The `partial` diagnostic requires a correct ID and at least one other correct field, so unanchored fragments are not falsely attributed to particular deleted records.
