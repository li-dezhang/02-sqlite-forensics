# Tests

Run `.venv/bin/python -m unittest discover -s tests -v` from P2. Eight tests exercise duplicate matching, partial credit, complete-match precedence, invalid values, REAL tolerance, null/empty differences, short rows and empty prediction sets. Integration verification uses actual recorded outputs through `scripts/verify.py`.
