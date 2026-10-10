# Task 09: Light linking: link selected objects

**Depends on:** none
**Group:** Light linking · **Source:** `.notes/new-features-decisions.md` items 19, 20 (list, Link Selected, remove), 21

## Goal
A light's details end with a Light Linking section. **Link Selected** adds the selected objects to the light's receiver collection as Include, so the light lights only them. The list shows each receiver, object or child collection, with a remove `×`. Selected items already in the list are not added twice.

## Verify first
Can Link Selected also pick up collections selected in the Outliner, as Blender's own `object.light_linking_receivers_link` does? From the sidebar, try reading `selected_ids` under a `context.temp_override()` of an Outliner area. If that works, include those collections. Otherwise, link objects only and note the limit in ARCHITECTURE.md and the README.

## Scope
- `lighthouse/lights.py`:
  - `Receiver(id, kind, state)` NamedTuple, where `kind` is `'OBJECT'` or `'COLLECTION'`. `receivers(obj)` lists the light's receiver collection: child collections first, then objects, each sorted by name ignoring case. Each state comes from `collection_children[...]` / `collection_objects[...]` `.light_linking.link_state`. Without a receiver collection the list is empty.
  - `link_receivers(light_obj, ids, state)` creates the receiver collection when it is missing, named like Blender's ("Light Linking for <light>"). It links each id not already in it, sets `state` on every given id, and skips the light itself. It returns how many were added and how many updated.
  - `remove_receiver(light_obj, id)` unlinks one object or child collection.
- `lighthouse/__init__.py`:
  - `lighthouse.link_receivers` (`REGISTER`, `UNDO`): `name`, `library` and `state` (default `INCLUDE`). It warns "No objects selected" and cancels when nothing is selected apart from the light. It refuses a read-only light or receiver collection.
  - `lighthouse.remove_receiver` (`REGISTER`, `UNDO`): the light's `name`/`library`, plus `receiver`, `receiver_library` and `kind`.
  - `draw_details()`: at the bottom, a "Light Linking" label, a Link Selected button, then one row per receiver with its icon (`OBJECT_DATA` or `OUTLINER_COLLECTION`), its name and `×` (`X`, no emboss).

## Out of scope
Exclude Selected, the Include/Exclude toggle, Clear and the Shared label (task 10). The row icon (task 11). The engine note (task 12). Shadow linking, the reverse view, a picker and drag and drop (item 19, 21).

## Done when (testable)
- Test: with `Key` open and `Cube` and `Sphere` selected, `link_receivers(name="Key")` creates `Key`'s receiver collection holding both objects as `INCLUDE`. `receivers(Key)` returns them sorted.
- Test: running it again with `Cube` and `Plane` selected adds only `Plane`, with no duplicates.
- Test: the light itself, if selected, is not added.
- Test: with nothing else selected, the operator cancels with the warning and creates no collection.
- Test: `remove_receiver` drops `Cube` and leaves `Sphere`.
- Test: a child collection in the receiver collection is listed as `COLLECTION` before the objects.
- Test (Recorder): the open details draw Link Selected and one row per receiver with `×`.
- `make test` passes on 5.2 and on 4.2.
- Manual (GUI, Cycles): Link Selected with one cube selected, and in a Rendered viewport only that cube gets the light. `×` removes it and the whole scene is lit again. Ctrl+Z works for both.

## Afterwards
Append a `## v5 task 09: light linking receivers` entry to ARCHITECTURE.md with the verify result. Add `link_receivers` and `remove_receiver` to `tests/smoke_engines.py`.
