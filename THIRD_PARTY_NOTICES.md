# Third-party notices

The project does not vendor the recovery tools, their binaries or Python dependency trees. Tool preparation retrieves pinned public source and retains its upstream notices locally. The small compatibility changes are disclosed below; neither is a new recovery algorithm.

| Component | Version/source | Terms and treatment |
|---|---|---|
| Undark | [0.7.1, commit 2e0bd78](https://github.com/inflex/undark/tree/2e0bd78bcb92597362c1fd93d0e392afe1adcbaa) | BSD Revised / three-clause terms. The copyright notice, conditions and disclaimer are retained verbatim in [UNDARK.txt](licenses/UNDARK.txt). `setup_tools.py` renames the local `ntohll` symbol to `undark_ntohll` to compile on the tested macOS host. Source and binaries stay ignored. |
| SQLite Dissect | [1.0.0, commit 6c0a742](https://github.com/dod-cyber-crime-center/sqlite-dissect/tree/6c0a742d70c27c3b48fd0bd275eac6bf21f96737) | DC3 SQLite Dissect Open Source License, with permission and warranty notices retained verbatim in [SQLITE_DISSECT.txt](licenses/SQLITE_DISSECT.txt). The included [compatibility patch](docs/evidence/dissect_bytes_compatibility.patch) changes three empty hashing accumulators from strings to bytes. The notice accompanies that patch and its source context. |
| SQLite Forensic Corpus v2.0 | [Official collection](https://digitalcorpora.org/corpora/sql/sqlite-forensic-corpus/) | Package CC0 1.0 Universal text retained in [DATA_CC0.txt](licenses/DATA_CC0.txt). Original databases/ZIPs are excluded. Small synthetic reference vectors and derived measurements are included with attribution. |

Python dependencies are declared in `requirements.txt`, installed locally and not redistributed as copies. Their licences remain in the installed distributions. There is no claim of endorsement by any tool or corpus author.

No overall open-source licence has yet been selected for the original portfolio code/report. These third-party permissions do not grant a licence to the entire project. The owner can decide whether to add one when approving public release; until then, do not describe the whole project as MIT-licensed or otherwise freely reusable.
