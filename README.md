# Evaluating the Reliability of Deleted-Record Recovery in SQLite Databases

## Overview

A reproducible **pilot study** for Dezhang Li's Master's Research Portfolio: compare two public SQLite recovery tools against known deleted records, then inspect their errors. The contribution is an executable evaluation pipeline, not a new recovery algorithm. Implementation and writing were AI-assisted; this is an unpublished research-training project awaiting researcher review.

[English Research Report](report/RESEARCH_REPORT.md) · [Final reproduction review](docs/FINAL_REVIEW.md) · [Results CSV](results/final-20261021/comparison.csv) · [Failure examples](results/final-20261021/FAILURE_ANALYSIS.md)

## Research Questions

- **RQ1:** How do strict complete-record precision, recall and F1 differ between the tools?
- **RQ2:** How do observed outcomes vary across the selected deletion/storage conditions?
- **RQ3:** What partial, incorrect and missing recovery patterns occur?

## Dataset

[SQLite Forensic Corpus v2.0](https://digitalcorpora.org/corpora/sql/sqlite-forensic-corpus/), official public distribution, **CC0 1.0 Universal**. The 5,370,116-byte archive contains 141 databases; this study uses only **10 crafted category 0C cases**, with **101 deleted and 189 live records** across 16 tables. The remaining cases are outside scope.

Publisher XML deletion labels are corroborated by supplied SQL INSERT/DELETE text, schemas and read-only queries of surviving rows. All 556 publisher checksums pass. Corpus SQL is never executed. The archive's SHA-256 is `8d71ff0ca595716b60ca7b6e9f0c7789e4612383f230e3742c9fc06ad39e95d8`.

[Acquisition and licence](data/README.md) · [File hashes](data/manifest.json) · [Sample statistics](results/final-20261021/samples.csv)

## Methods

**Undark 0.7.1** and **SQLite Dissect 1.0.0** run on identical database bytes, without answer files or journal sidecars. Both use pinned source revisions and disclosed compatibility fixes: an Undark symbol rename for compilation and three Dissect string-to-bytes hash-accumulator changes. See [tool metadata](docs/tool_versions.json) and [third-party notices](THIRD_PARTY_NOTICES.md).

The endpoint matches complete ordered column-value vectors, excluding table attribution and internal SQLite rowid. Integers/text match exactly; REAL fields use absolute tolerance `1e-5`, with no relative tolerance. Matching is one-to-one. TP counts complete matches, FP counts remaining candidates, and FN counts references without complete matches. Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN).

Allocated/live rows are excluded using independently queried live data; malformed vectors and fragments remain candidates. Dissect exports overlapping fragment candidates, while Undark has different output granularity. FP therefore means **failure to meet this full-vector endpoint**, not that every output is fictitious. Partial recovery is reported separately and earns no strict TP credit. No scoring threshold was changed during final review.

## Key Results

| Tool, with disclosed patch | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Undark 0.7.1 | 0 | 29 | 101 | 0.00% | 0.00% | 0.00% |
| SQLite Dissect 1.0.0 | 78 | 150 | 23 | 34.21% | 77.23% | 47.42% |

Undark's zero applies only to **strict complete-record matching**: it has 10 anchored partial recoveries. Exploratory REAL tolerances of `1e-4` and `1e-3` produce 2 and 8 complete matches; Dissect's counts remain unchanged. Dissect's 0C-03/04 cases contribute 124 of its 150 FP.

[Per-case results](results/final-20261021/per_case.csv) · [Record matching](results/final-20261021/record_matches.csv) · [Tolerance sensitivity](results/final-20261021/real_tolerance_sensitivity.csv)

## Figures

![Strict complete-record precision, recall and F1](figures/final-20261021/performance.png)

![Strict complete-record recall for each case](figures/final-20261021/recall_by_case.png)

Both figures are computed directly from the matching result CSVs. Asterisks identify the disclosed compatibility builds. SVG versions are available alongside the PNGs.

## Reproduction

Verified on **macOS 27.0.1, Apple Silicon, Python 3.13.2, Apple clang 14.0.3**, including a new virtual environment. Other platforms are untested. Install Python 3.13 and Apple Command Line Tools if absent; these prerequisites may require manual installation. Public network access is needed for dependency/tool installation and the first dataset acquisition.

Run from this directory. The example uses `.venv-review`; the runner uses the environment that launches it. Choose an unused environment name when independently validating a fresh installation.

```bash
python3 -m venv .venv-review
.venv-review/bin/python -m pip install -r requirements.txt
.venv-review/bin/python scripts/setup_tools.py
.venv-review/bin/python scripts/acquire.py
.venv-review/bin/python -m unittest discover -s tests -v
RUN_ID="reproduce-$(date -u +%Y%m%dT%H%M%SZ)"
.venv-review/bin/python scripts/run_study.py --run-id "$RUN_ID"
.venv-review/bin/python scripts/summarize.py --run-id "$RUN_ID"
.venv-review/bin/python scripts/error_analysis.py --run-id "$RUN_ID"
.venv-review/bin/python scripts/verify.py --run-id "$RUN_ID"
```

Existing matching raw data is hash-verified without another download. The first acquisition is capped at 20 MB and safe extraction checks paths and sizes. A changed archive stops the script. Dissect is installed from the official source ZIP for the same pinned commit, with a SHA-256 check; this avoids a Git clone dependency. Undark source is hash-checked and compiled locally. Setup applies/verifies the documented compatibility patches automatically and retains a new build log each time.

Run directories are never overwritten. Outputs go to `results/<run-id>/` and `figures/<run-id>/`; original stdout, stderr and tool CSVs remain in ignored `data/interim/runs/<run-id>/`. Each `run.json` records commands, exit codes, input/output hashes, versions and source hashes. Verification compares the regenerated counts with the published pilot and stops on differences; it does not rewrite the report to hide them.

## Repository Structure

```text
src/p2study/          Reference validation and one-to-one scoring
scripts/             Acquisition, tool setup, execution, plots and verification
tests/               Eight scoring unit tests
requirements.txt     Pinned dependencies and tool source archive
data/                Acquisition instructions and manifest; raw/interim ignored
results/final-20261021/  Original measured CSVs, examples and run manifest
figures/final-20261021/  CSV-derived PNG/SVG figures
report/              English pilot report
docs/                Current design, source/tool records and review summary
licenses/            Unmodified third-party licence notices
```

## Limitations

Ten small synthetic cases; development cases included in the final descriptive comparison; one tested platform; compatibility-patched builds; no journal analysis or table-attribution score. Fragment usefulness differs from strict numeric/text fidelity. Differences across cases are descriptive, not causal. No real-case validation, held-out benchmark, population accuracy estimate or universal tool ranking is claimed.

Raw databases, archives, full tool copies, virtual environments, caches and private working files are excluded from publication. Historical approval materials remain local; the earlier Gate A was never approved and was superseded by the user's lightweight research authorization. Public release still requires the owner's decision. An overall licence for the original portfolio code/report has not yet been selected; see [third-party notices](THIRD_PARTY_NOTICES.md).

## References

- Nemetz, S., Schmitt, S., & Freiling, F. (2018). *A standardized corpus for SQLite database forensics.* [DOI: 10.1016/j.diin.2018.01.015](https://doi.org/10.1016/j.diin.2018.01.015).
- Meng, C., & Baier, H. (2019). *bring2lite: A structural concept and tool for forensic data analysis and recovery of deleted SQLite records.* [DOI: 10.1016/j.diin.2019.04.017](https://doi.org/10.1016/j.diin.2019.04.017). Related work, not an evaluated tool here.
- SQLite Project. [Database File Format](https://sqlite.org/fileformat2.html).
- Daniels, P. L. [Undark, pinned revision](https://github.com/inflex/undark/tree/2e0bd78bcb92597362c1fd93d0e392afe1adcbaa).
- DC3. [SQLite Dissect, pinned revision](https://github.com/dod-cyber-crime-center/sqlite-dissect/tree/6c0a742d70c27c3b48fd0bd275eac6bf21f96737).
