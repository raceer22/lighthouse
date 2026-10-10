# Task 07: New Collection button

**Depends on:** task-03, task-05
**Group:** Collections · **Source:** `.notes/new-features-decisions.md` item 11

## Goal
A button in the list header creates a collection inside the active one and makes it active. A following `+` then puts a light straight into it. With empty collections shown (task 05, on by default), the new collection appears right away as `(0)`.

## Scope
- `lighthouse.new_collection` (`UNDO`):
  - The parent is `view_layer.active_layer_collection.collection`, which is the Scene Collection when the master is active.
  - It refuses a library (`is_read_only`) parent with an `ERROR` report before creating anything, like `add_light`.
  - It creates `bpy.data.collections.new("Collection")` (Blender adds `.001` on a clash), links it into `parent.children` and makes its layer collection active.
  - It doesn't touch object selection.
- Header: an icon button (for example `COLLECTION_NEW`) next to `+`.

## Open questions
Not decided: whether creating inside a collapsed collection expands it so the new one is visible. Default: leave folding alone.

## Done when (testable)
- Test: with `Set` active, the new collection is a child of `Set`, is the active collection, and is the only new collection in `bpy.data.collections`.
- Test: with the Scene Collection active, the new collection is a top-level child of `scene.collection`.
- Test: with a linked collection active, the operator raises `RuntimeError` and `bpy.data.collections` is unchanged.
- Test: selected objects and the active object are unchanged.
- Test: `list_entries(show_empty=True)` lists the new collection with count 0, under its parent.
- `make test` passes.
- Manual (GUI): click New Collection and then `+`, and the light lands in the new collection. One Ctrl+Z removes the collection.

## Afterwards
Append a `## v4 task 07: New Collection` entry to ARCHITECTURE.md. Add `new_collection` to `tests/smoke_engines.py`.
