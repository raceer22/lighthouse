# Task 02: Presets that stay correct

**Depends on:** task-01
**Type:** bug fix + polish (presets) · **Source:** polish review, bugs 2–3 and "Saving a preset", "Presets are read from disk on every redraw"

## Goal
The preset dropdown always points at the preset you picked, even after presets are added or deleted. Deleting the last user preset no longer breaks the panel. Library lights are never changed by a preset. Saving is safe and selects what you saved. The panel no longer reads every preset file on each redraw.

## Scope
Work through this in order. Each step is testable on its own.

1. **Stable dropdown identity** (`lighthouse/__init__.py` `preset_items`): give each item a number derived from its key, e.g. `zlib.crc32(key.encode()) & 0x7FFFFFFF`, instead of `enumerate()`. The stored value then follows the preset itself, not its position. Update the ARCHITECTURE.md:116 caveat.
2. **Deleting the selected preset:** `LIGHTHOUSE_OT_delete_preset.execute()` sets `settings.preset` to the first built-in (`'CANDLE'`) when it deletes the preset the dropdown shows.
3. **Draw guard:** in `LIGHTHOUSE_PT_presets.draw()`, if `settings.preset` is `''` (preset file removed outside Blender), don't assign it to the operator. Draw Apply disabled and hide Delete. Assigning `''` to an enum raises `TypeError` and stops the panel drawing.
4. **Library lights** (`lighthouse/presets.py` `apply_preset`): skip objects whose light data `is_read_only()`, as `scale_lights` does. Return `(changed, incompatible, read_only)`. `preset_summary` names both skip reasons, e.g. `Applied Candle to 2 lights (1 skipped: incompatible type, 1 skipped: read-only)`.
5. **Saving:**
   - Overwrite check: if `preset_path(folder, label)` already exists, `execute()` refuses with an error unless a new `overwrite` BoolProperty is set. Checking the file path, not the label, also catches labels that sanitize to the same file (`Key/Fill` and `Key_Fill`). The dialog's `draw()` shows a warning line and the Overwrite checkbox when the typed name matches an existing file.
   - After a successful save, set `settings.preset` to the new preset's key, so the dropdown shows it.
6. **Cache user presets:** keep a module-level cache of `user_presets(presets_folder())`, keyed by the folder's `stat().st_mtime_ns`, which changes when files are added, removed or renamed. Save and delete clear it explicitly. Editing an existing file in place outside Blender is only picked up after a restart: document that.

## Out of scope
New built-in presets, renaming presets, preset import/export.

## Done when (testable)
Use `run_installed` as in `test_user_presets.py`.
- Test: with user presets `Alpha` and `Beta`, select `Beta`, save a new `Aardvark`, and the dropdown still reads `USER:Beta`.
- Test: select `Alpha` and delete it. The dropdown reads `CANDLE`, not `USER:Beta`. Delete the last user preset, and the dropdown is a built-in, never `''`.
- Test: `apply_preset` on a linked library light plus a local one changes only the local one, and returns and reports 1 read-only skip. Reuse the library setup from `test_group_actions.py`.
- Test: saving `My Key` twice fails the second time without `overwrite`, and succeeds with it. Saving `Key/Fill` after `Key_Fill` is treated as an overwrite.
- Test: after `save_preset(name="Fresh")`, `settings.preset == "USER:Fresh"`.
- Test: two `all_presets()` calls in a row parse the JSON files once (wrap `presets.json.loads` with a counter). After a save, they are parsed again.
- `make test` passes, with existing `preset_summary` / `apply_preset` tests updated to the new return shape.
- Manual (GUI): delete the last user preset, and the panel still draws with Apply working. The save dialog shows the overwrite warning for an existing name.

## Afterwards
Append a `## v3 task 02: presets` entry to ARCHITECTURE.md with (1) new components, (2) data flow (dropdown value → cache → files), (3) Blender API quirks (enum numbers as identity, `''` on a missing item, whether dialogs redraw while typing).
