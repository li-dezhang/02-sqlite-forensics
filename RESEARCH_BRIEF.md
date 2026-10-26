# P2 — Evaluating the Reliability of Deleted-Record Recovery in SQLite Databases

Current scope: **completed descriptive pilot, awaiting researcher review**, under the lightweight workflow authorized on 2026-10-21. The historical Gate A was never approved. See [workflow](docs/WORKFLOW.md); the earlier brief is preserved locally in `docs/history/RESEARCH_BRIEF_PHASE0.md` (excluded from the public release). No remote publication is authorized.

## Questions and data

RQ1: How do strict complete-record precision, recall and F1 differ between two public recovery tools? RQ2: How do their observed outcomes vary across the corpus's deletion and storage conditions? RQ3: What kinds of missed, partial and incorrect outputs occur?

Use the official SQLite Forensic Corpus v2.0 ZIP (CC0, 5,370,116 bytes). This pilot evaluates all ten 0C databases, not all 141 databases in the package. 0C contains 101 deleted and 189 live records across 16 tables. The 0C XML files are original v1 examples retained inside the v2 distribution; they are not mislabeled new v2 anti-forensic cases. No private or real-case data is used. 0D/0E and anti-forensic extensions are outside scope.

The database is the experimental case. The scored unit is a complete ordered vector of column values. Table identity and SQLite rowid recovery are not evaluated because Undark does not provide equivalent table attribution. Reference XML supplies `deleted="1"` labels; supplied SQL INSERT values and DELETE statements, actual live rows, schema and publisher checksums are cross-checked. SQL is parsed as text and never executed. No ambiguous deleted/live content overlap or duplicate reference vectors occurred in these ten cases.

## Design and methods

A four-case development pilot (0C-01/03/05/09) was followed by an all-ten-case descriptive run and repeat verification. These are not a training/test split or blinded evaluation. No models were trained; no population significance claim is made. The previous proposed 30/70 split and timing study are superseded for this small pilot.

Compare independent implementations: Undark 0.7.1 and SQLite Dissect 1.0.0 at pinned commits. The former has a symbol-name portability patch; the latter has a three-line byte-string hashing compatibility patch. Both are disclosed and reproducible in `scripts/setup_tools.py`. FQLite was not selected for the headless workflow; unused candidate tools are not counted as experiments. Unpatched Dissect failed during development; those logs remain available.

Both receive only the same original database, no XML/SQL answers and no sidecar journals. Inputs are read-only and hashed before/after. Undark uses `-i`; Dissect uses `-n -c -f -e csv`. Each invocation has a 60-second timeout. This is correctness evaluation, not a runtime benchmark; memory is not claimed to have been capped. Dissect can use surviving database schema/records as part of its own algorithm.

## Scoring and interpretation

Integer and text fields match exactly; REAL fields use absolute tolerance 1e-5 and zero relative tolerance. Shape mismatch, malformed values and duplicate candidates are retained, not silently dropped. Explicitly allocated Dissect rows are not recovery candidates; for either tool, exact matches to independently queried live rows are removed and counted separately.

One output can match one reference at most, and vice versa. TP = complete matching deleted vectors; FP = all remaining candidate vectors; FN = deleted reference vectors lacking a complete match. Precision = TP/(TP+FP); recall = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN). Undefined zero-denominator ratios are missing, not invented zeros.

Partial recovery is a secondary, conservative diagnostic: a unique unmatched reference has the same first-column ID and at least one additional matching field. It remains both FP and FN under the primary strict endpoint. Unanchored fragments are labeled incorrect/unattributed; this does not mean all their bytes are fabricated. A post-hoc tolerance sensitivity analysis is reported separately. Tool crashes are execution failures, not automatic zero-score runs.

## Deliverables and limits

Runnable Python, pinned requirements/tool preparation, scoring tests, acquisition hashes, actual per-case logs, sample and comparison CSVs, record matching records, figures, failure examples, and an English Pilot Study report. README commands reproduce the analysis. No raw databases, archives, binaries, virtual environments, secrets or temporary outputs are selected for Git publication.

Researcher review should check interpretation, scope and final wording before public release. It is not an acquisition gate and has not been signed by the assistant. Results describe these crafted cases and patched builds on the recorded platform, not performance in real investigations or universal tool rankings.
