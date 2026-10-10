# Task 06: Operators find the exact light or collection, not just its name

**Depends on:** task-01. Touches the same operators as task-05, so do it after task-05 to avoid conflicts.
**Type:** robustness (row and group operators) · **Source:** polish review, "Lookups by name"

## Goal
With a linked library light or collection that has the same name as a local one, every row and header button acts on the item it is drawn for.

## Scope
- First check how Blender resolves `bpy.data.objects.get((name, library_filepath))`, and with `None` for local IDs, on 5.2 and on 4.2. Record the result. If tuple keys don't work, fall back to scanning `bpy.data.objects` for `(obj.name, obj.library)`.
- `lighthouse/lights.py`:
  - `id_key(id)` returns `(id.name, id.library.filepath if id.library else "")`.
  - `find_object(view_layer, name, library)` returns the object only if it is in the view layer.
  - `find_collection(name, library)` returns the matching collection.
- `lighthouse/__init__.py`:
  - Every operator that takes `name` gains `library: StringProperty(options={'HIDDEN'})` and uses the lookup helpers. That is `select_light`, `mute_light`, `solo_light`, `toggle_details`, `toggle_group`, `select_group`, `move_to_group`, `hide_group` and `solo_group`, plus `exit_solo` if it takes a target.
  - One draw helper, e.g. `target(op, id)`, sets both `name` and `library`, so the panel code doesn't repeat it.
- `library` defaults to `""` (local), so existing calls in tests and the smoke script keep working.

## Out of scope
Library overrides, which already have unique names. Linked data stays read-only as before.

## Done when (testable)
- Test: link a light `Key` and a collection `Lights` from a library file next to a local `Key` and `Lights`. Then:
  - `mute_light`, `solo_light` and `select_light` with `library=""` change only the local `Key`, and with the library path only the linked one.
  - `hide_group` and `select_group` do the same for the two `Lights` collections.
- Test: `find_object` returns `None` for a matching object that isn't in the view layer.
- `make test` and `tests/smoke_engines.py` pass unchanged.
- Manual (GUI): in a file with a linked `Key` and a local `Key`, the eye on each row hides only that row's light.

## Afterwards
Append a `## v3 task 06: lookup by name and library` entry to ARCHITECTURE.md, including how ID lookup by tuple key behaves.
