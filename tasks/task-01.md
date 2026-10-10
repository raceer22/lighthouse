# Task 01: Foldable lights row

**Depends on:** none
**Group:** Objects (lights row) · **Source:** `.notes/new-features-decisions.md` items 1, 2, 4

## Goal
A collection that has its own lights **and** at least one listed sub-collection shows those lights under a foldable `Lights (N)` row. You can then open a big collection to reach its sub-collections without all of its lights showing. A leaf collection still lists its lights directly.

## Scope
- `lighthouse/lights.py`:
  - New `LightsEntry(collection, depth, count)` NamedTuple. `count` is the number of the collection's own listed lights.
  - `_collection_entries()` emits a `LightsEntry` at the collection's content depth when the collection has own listed lights and at least one listed sub-collection. Its lights move one level deeper. When the row is folded, its lights are dropped and the sub-collections still follow.
  - A leaf collection (no listed sub-collections) lists its lights at its content depth with no row, as today.
  - `is_lights_folded(collection)` reads `lighthouse_lights_collapsed` with a `False` default, like `is_collapsed()`, so `list_entries()` still works while the add-on is unregistered.
  - Folding never changes what a collection holds: the `GroupEntry.count`, `group_lights()` and `listed_groups()` still include every light (item 4).
  - Scene Collection lights are unchanged in this task (depth 0, no row). Task 04 gives them a fold.
- `lighthouse/__init__.py`:
  - `Collection.lighthouse_lights_collapsed`: a BoolProperty, default `False` (starts open), registered and removed next to `lighthouse_collapsed`. Like that property, it is saved in the .blend.
  - `lighthouse.toggle_lights_row` (`INTERNAL`, no `UNDO`, `name` and `library` set through `target()`) flips it.
  - `draw_lights_row()`: indent, disclosure triangle (the toggle, no emboss), then a `Lights (N)` label with a light icon (for example `LIGHT`). No action buttons.
  - Every `list_entries()` consumer now handles three entry types. The panel draw loop gets a third branch. `select_light`'s `RANGE` keeps only `LightEntry` rows: today it keeps everything that isn't a `GroupEntry`, which would let a `LightsEntry` in.
- Update `tests/test_grouped_lights.py` cases where a collection has both its own lights and sub-collections. They now expect the row.

## Out of scope
Expand All / Collapse All and lights rows (task 02), the Scene Collection's lights (task 04), revealing a light (task 08).

## Done when (testable)
- Test: `Set` holds `Key` and `Fill` plus the sub-collection `Lamps` (holding `Bulb`). It lists `group Set 0 (3)`, `lights Set 1 (2)`, `light Fill 2`, `light Key 2`, `group Lamps 1 (1)`, `light Bulb 2`.
- Test: a leaf collection `Props` with two lights lists them directly, with no lights row.
- Test: folding `Set`'s lights row drops `Fill` and `Key` and keeps `Lamps` and `Bulb`. `Set` still counts 3, and `group_lights(Set)` still returns all three.
- Test: with the lights row folded, collapsing and then expanding `Set` leaves the row folded.
- Test: `toggle_lights_row` has no `UNDO` in `bl_options`. The property defaults to `False` and survives `save_as_mainfile` and `open_mainfile`.
- Test: with `Set`'s lights row folded, a Shift+click range from a Scene Collection light (`Sun`, above `Set`) to `Bulb` selects only `Sun` and `Bulb`.
- `make test` passes.
- Manual (GUI): the row's triangle, icon and label line up with sibling headers. Folding survives saving and reopening.

## Afterwards
Append a `## v4 task 01: foldable lights row` entry to ARCHITECTURE.md. Add `toggle_lights_row` to `tests/smoke_engines.py`.
