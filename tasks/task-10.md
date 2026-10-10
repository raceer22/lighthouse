# Task 10: Presets become plain files

**Depends on:** none
**Group:** Presets · **Source:** `.notes/new-features-decisions.md` items 14, 16, 17

## Goal
The built-in presets become normal JSON files in the presets folder, so every preset can be applied, overwritten, re-saved or deleted the same way. A deleted default stays deleted after a restart.

## Scope
- `lighthouse/presets.py`:
  - Rename `BUILTIN_PRESETS` to `DEFAULT_PRESETS`. It is now only the source for writing the files, so its keys no longer matter.
  - `restore_default_presets(folder)` writes each default whose `preset_path()` is missing and returns the labels it wrote. It never overwrites an existing file. Task 11 reuses it.
  - `seed_default_presets(folder)`: if the marker file (for example `.defaults_installed`) is missing, it calls `restore_default_presets()` and then writes the marker. The marker isn't `*.json`, so `user_presets()` ignores it.
- `lighthouse/__init__.py`:
  - Seed once per session before the first read of the folder (for example in `cached_user_presets()`, behind a module-level flag).
  - `all_presets()` is just `cached_user_presets()`. `preset_items()` uses icon `'NONE'` and no "User preset" description, sorted by label ignoring case.
  - `save_preset`: remove the reserved-name check. Saving as `Candle` follows the normal exists / Overwrite flow.
  - `delete_preset`: offers every preset. When it deletes the preset that's shown, it selects the next one in dropdown order, or the new last one when it deleted the last. With no presets left, it assigns nothing (assigning `''` raises `TypeError`) and the dropdown reads `''`.
  - `LIGHTHOUSE_PT_presets`: Delete is shown whenever `settings.preset` is set. Apply is already greyed out for `''`.
  - Remove the `USER` icon, the built-in check and the `CANDLE` fallback.
- Known cost (item 17): a default's key changes from `CANDLE` to `USER:Candle`, so a .blend saved with a built-in selected opens with nothing selected. The panel already handles `''`. Document it and don't migrate.
- Update `tests/test_presets.py` and `tests/test_user_presets.py` (built-in keys, item order, icons) and `tests/smoke_engines.py`. Preset tests must use `run_installed`, because `extension_path_user()` needs the `bl_ext` package name.

## Done when (testable)
- Test: on a fresh user dir, the presets folder holds `Candle.json`, `60W Bulb.json`, `Daylight.json` and the marker. `preset_items()` returns `60W Bulb`, `Candle`, `Daylight`, all with icon `NONE`.
- Test: after deleting `Candle` and restarting with the same user dir, `Candle` is still gone.
- Test: with the marker present and no JSON files, nothing is seeded.
- Test: applying `USER:Candle` sets the same power, radius and Kelvin (or the RGB fallback below 5.0) as the old built-in.
- Test: saving a light as `Candle` without Overwrite is refused with the "exists" error. With Overwrite it replaces the file.
- Test: deleting the shown `Candle` selects `Daylight`. Deleting the shown `Daylight` (now last) selects `60W Bulb`. Deleting the only preset left leaves `settings.preset == ''`.
- `make test` passes.
- Manual (GUI): the dropdown has no icons, and the panel draws with an empty dropdown and a greyed-out Apply.

## Afterwards
Append a `## v4 task 10: presets as plain files` entry to ARCHITECTURE.md and mark the task 10 and v3 task 02 notes about built-ins and the `CANDLE` fallback as superseded. Mention the item 17 cost in the README.
