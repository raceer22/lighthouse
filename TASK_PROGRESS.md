# Task progress

## TICKET-01: Own lights before sub-collections
- `_collection_entries()` now lists a collection's own lights before its sub-collections, so Scene Collection lights come first.
- Updated the `list_entries()` docstring and added a v3 task 01 entry to ARCHITECTURE.md.
- `make test`: all 103 pass. The 5 failing ordering tests are fixed and the tests themselves were not edited. The manual GUI check has not been done.
