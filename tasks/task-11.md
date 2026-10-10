# Task 11: Restore default presets

**Depends on:** task-10
**Group:** Presets · **Source:** `.notes/new-features-decisions.md` item 15

## Goal
A Restore button brings back any default preset that was deleted, without touching presets you edited. To reset an edited default, delete it and press Restore.

## Scope
- `lighthouse.restore_default_presets` (no confirm, no `UNDO`, because preset files aren't part of undo). It calls `restore_default_presets(presets_folder())` from task 10 and clears the presets cache.
  - It reports `INFO` with what it restored (for example "Restored Candle, Daylight"), or that every default preset is already there.
- `LIGHTHOUSE_PT_presets`: a Restore button in the row with Save and Delete.

## Open questions
Not decided: whether Restore selects a preset when the dropdown is empty. Default: leave the selection alone.

## Done when (testable)
- Test: delete `Candle` and save over `Daylight` with a different power, then press Restore. `Candle` is back with its default values, and `Daylight` keeps the edited power.
- Test: with every default present, Restore writes no file (the folder's mtime is unchanged) and reports that nothing was missing.
- Test: user presets that aren't defaults are untouched.
- `make test` passes.
- Manual (GUI): Restore sits next to Save and Delete, and restored presets appear in the dropdown right away.

## Afterwards
Append a `## v4 task 11: restore default presets` entry to ARCHITECTURE.md. Add Restore to `tests/smoke_engines.py`.
