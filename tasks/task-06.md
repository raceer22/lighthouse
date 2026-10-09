# Task 06: Details accordion and new detail fields

**Depends on:** task-05
**PRD-v2 sections:** Light details, Constraints (version lookups, no-undo panel state) · **AC:** 14, 18 (details part)

## Goal
Opening one light's details closes the others, unless Shift is held. Which details are open is panel state: not saved, not undoable, and not lost on rename. The details box gains Name, Exposure and Temperature, and Exposure and Temperature are looked up so the addon still runs on Blender 4.2.

## Scope
- **Remove `Object.lighthouse_expanded`** (its registration and every use).
- **Storage:** `LIGHTHOUSE_PG_settings.expanded`, a `CollectionProperty` of a small PropertyGroup holding `obj: PointerProperty(type=bpy.types.Object)`. It lives on the WindowManager, so it is not saved and not part of undo, and the pointer survives renames.
- **Operator:** `lighthouse.toggle_details` (object name, `keep_others` bool, `bl_options` without `UNDO`).
  - `invoke()` sets `keep_others` from `event.shift`.
  - Opening clears every other entry unless `keep_others` is set. Closing removes only this light.
  - Prune entries whose `obj` is `None`.
  - The row triangle draws this operator, with the icon taken from whether the light is in `expanded`.
- **Multi-linked lights:** every row of the same object shares the same open state.
- **Version-safe lookup:** a helper in `lights.py`, for example `has_property(rna, name)` using `rna.bl_rna.properties`. Every property added after 4.2 is checked with it before use.
- **Details box, in order:**
  1. **Name** (`prop(obj, "name")`)
  2. **Exposure**, if the light has it
  3. **Use Temperature** and **Temperature** (K), if the light has them (Blender 5.0+)
  4. the existing soft size, influence, shadow and Cycles settings

  Extend `detail_properties()` so these show up in its output only when the light's RNA has them. The box follows the row's dimmed and read-only state, as before.

## Out of scope
Kelvin on the row and presets (task 07). A "collapse all details" button (not in the PRD).

## Done when (testable)
- Test: opening A, then B, leaves only B open. Opening C with `keep_others=True` leaves B and C open. Closing B leaves C (AC 14).
- Test: renaming an open light keeps it open.
- Test: `'UNDO'` is not in `toggle_details.bl_options`. `expanded` is registered on the WindowManager, and `bpy.types.Object` no longer has `lighthouse_expanded` (AC 14).
- Test: on 5.2, `detail_properties()` includes `exposure`, `use_temperature` and `temperature`. With a stub whose `bl_rna.properties` lacks them, they are left out and nothing raises (AC 18, AC 21 groundwork).
- `tests/test_details.py` is updated for the new storage, and `make test` passes.
- Manual (GUI): clicking triangles works like an accordion and Shift+click keeps the others open. Edit › Undo History gains no entries, and after a save and reopen no details are open (AC 14). The Name field renames the light.

## Afterwards
Append a `## v2 task 06: details accordion` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered. Check and record whether WindowManager ID pointers still resolve after Ctrl+Z. If they go stale, match by `ID.session_uid` instead.
