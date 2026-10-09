# Task 04: Pointer-based solo for lights and groups

**Depends on:** task-03
**PRD-v2 sections:** Solo, Group header (solo icon) · **AC:** 10, 11, 12

## Goal
Replace v1's name-keyed JSON solo with a pointer-based snapshot that also covers collections. That makes solo survive renames, work for lights inside hidden groups, and work for whole groups.

## Scope
- **Storage:** `Scene.lighthouse_solo`, a `PointerProperty` to `LIGHTHOUSE_PG_solo` with:
  - `active` (bool)
  - `light` (`PointerProperty(type=bpy.types.Object)`)
  - `group` (`PointerProperty(type=bpy.types.Collection)`)
  - `objects`: a `CollectionProperty` of items holding an object pointer plus `hide_render` / `hide_viewport`
  - `collections`: the same for collection pointers

  It is saved in the .blend file and recorded by undo. Remove the JSON code and `SOLO_KEY`. An old `scene["lighthouse_solo"]` is ignored (no migration).
- **Logic** stays in `lighthouse/lights.py` and takes the solo property group as an argument, so it can be tested without the UI.
- **Solo a light:**
  - Show it (object flags off) and hide every other light in the view layer (object flags).
  - Unhide every collection that contains it, plus their ancestors (`hide_render` / `hide_viewport` off).
- **Solo a group:**
  - Show every light in the group and its sub-collections, and hide every other light.
  - Unhide the group, its sub-collections and its ancestors.
- **Snapshot:**
  - The first solo saves every light's flags.
  - Each collection's flags are saved the first time solo changes that collection.
  - Switching target (light ↔ light, light ↔ group, group ↔ group) keeps the first snapshot. It only adds lights and collections that aren't in the snapshot yet, before changing them.
  - Collections unhidden for an earlier target stay unhidden until un-solo.
- **Un-solo:**
  - Pressing solo on the current target restores every item whose pointer is still set, then clears the snapshot and sets `active` off.
  - Items whose target was deleted are skipped.
  - If the soloed light itself was deleted, keep v1's behaviour: solo any light, then press it again to restore.
- **UI:**
  - Add a group header **Solo** icon, `lighthouse.solo_group` (`UNDO`), after Hide.
  - Light rows keep `lighthouse.solo_light`.
  - Each button is depressed when its target is the soloed one.

## Out of scope
Migrating v1 JSON snapshots. Multi-solo.

## Done when (testable)
- Test: soloing a light inside a hidden group makes it visible (`visible_get`). Un-solo restores every light flag and collection flag exactly, starting from mixed initial flags (AC 10).
- Test: group solo shows only that group's lights, sub-collections included. Switching light → group → another light, then un-soloing, restores the state from before the first solo (AC 11).
- Test: renaming the soloed light, another light and a hidden collection during solo, then un-soloing, restores all three (AC 12).
- Test: deleting a snapshotted light during solo, then un-soloing, raises no error and restores the rest.
- Test: saving and reopening the file mid-solo, then un-soloing, restores the original state.
- Port the v1 cases in `tests/test_mute_solo.py` to the new storage. Mute keeps working, and `make test` passes.
- Manual (GUI): the solo icons on rows and headers show the soloed state, and one Ctrl+Z reverts a solo.

## Afterwards
Append a `## v2 task 04: pointer-based solo` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered. Check and record whether Python ID pointers add users, and whether deleting an object from the outliner sets them to `None`.
