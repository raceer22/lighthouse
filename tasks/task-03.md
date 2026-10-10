# Task 03: Active collection as the target folder

**Depends on:** none
**Group:** Collections · **Source:** `.notes/new-features-decisions.md` item 10

## Goal
Clicking a collection's name makes it Blender's active collection, and a light added with `+` lands there. This is the shortest end-to-end path for "choose where new lights go". It reuses `view_layer.active_layer_collection`, so it stays in sync with the Outliner and Shift+A in the viewport.

## Scope
- `lighthouse/lights.py`: make `_find_layer_collection()` public (`find_layer_collection()`) so operators can use it.
- `lighthouse/__init__.py`:
  - `lighthouse.set_active_collection` (`name`, `library`) finds the collection's non-excluded layer collection and sets `view_layer.active_layer_collection`. It never touches object selection or the active object. It cancels when the collection isn't found.
  - Undo: do what the Outliner does. Check whether clicking a collection in the Outliner pushes an undo step, set `UNDO` to match, and record the answer in ARCHITECTURE.md.
  - `draw_group()`: the `Name (N)` label becomes this operator's button, with the collection icon. It is flat normally, and embossed with `depress=True` when the collection is the active one, like the active light's name.
- `add_light` already links into the active collection and refuses a library collection. Add tests for both if they're missing.
- A library collection can still be made active (the Outliner allows it). `+` then refuses with its existing error.

## Out of scope
The Scene Collection (task 04, which adds a row with the same click), the New Collection button (task 07).

## Done when (testable)
- Test: `set_active_collection(name="Lamps")` makes `active_layer_collection.collection` be `Lamps`. Selected objects and the active object are unchanged.
- Test: after that, `add_light(type='SPOT')` puts the new light in `Lamps` and in no other collection.
- Test: a linked (library) collection can be made active, `add_light` then raises `RuntimeError`, and no object is created.
- Test: an unknown or excluded collection name returns `{'CANCELLED'}` and leaves the active collection unchanged.
- `make test` passes.
- Manual (GUI): the active collection's name is drawn pressed. Clicking a collection in the Outliner moves the pressed state, and Shift+A in the viewport adds into the collection chosen in the panel.

## Afterwards
Append a `## v4 task 03: active collection` entry to ARCHITECTURE.md. Add `set_active_collection` to `tests/smoke_engines.py`.
