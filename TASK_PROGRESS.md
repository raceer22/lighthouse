# Task progress

## TICKET-01: Own lights before sub-collections
- `_collection_entries()` now lists a collection's own lights before its sub-collections, so Scene Collection lights come first.
- Updated the `list_entries()` docstring and added a v3 task 01 entry to ARCHITECTURE.md.
- `make test`: all 103 pass. The 5 failing ordering tests are fixed and the tests themselves were not edited. The manual GUI check has not been done.

## TICKET-02: Presets that stay correct
- The dropdown keeps its preset (enum numbers are key CRCs). Deleting the shown preset falls back to Candle, and an empty value no longer breaks the panel draw.
- Library and system-override lights are skipped and reported as read-only. Save refuses to overwrite without `overwrite`, catching sanitized-name collisions, and selects what it saved.
- User presets are cached by folder mtime and cleared on save and delete. 6 new tests, `make test`: 109 pass. Not done yet: the manual GUI checks (empty-value draw guard, whether the dialog warning updates live).
