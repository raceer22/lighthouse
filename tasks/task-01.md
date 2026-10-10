# Task 01: Own lights before sub-collections (green suite)

**Depends on:** `master` at 19a1f57
**Type:** bug fix · **Source:** polish review, bug 1

## Goal
Make `make test` pass again. Commit 6adf632 changed the tests and ARCHITECTURE.md to "a collection's own lights come before its sub-collections, and Scene Collection lights come first". The code was never updated, so 5 tests fail. This is the smallest end-to-end fix, and every later task needs a green suite to start from.

## Scope
- `lighthouse/lights.py` `_collection_entries()`: build `own` (sorted by name, ignoring case) first, and add its `LightEntry` rows and `lights` entries before the child-collection loop. Then append each child's `GroupEntry` and, unless it is collapsed, the child's entries.
  - `lights` stays an ordered dict, so `group_lights()` returns own lights first. Group select then makes the group's first own light active, and Shift+click ranges follow the new order without further changes.
- `list_entries()` docstring: "each followed by its own lights sorted by name ignoring case, then its sub-collections … Scene Collection lights come first, with no header."

## Out of scope
Any other change to grouping, counts or collapse.

## Done when (testable)
- These five tests pass with no edits to the tests:
  - `test_grouped_lights.py::test_collections_without_lights_are_left_out_and_scene_collection_lights_have_no_header`
  - `test_grouped_lights.py::test_search_flattens_the_list_and_clearing_it_restores_groups`
  - `test_grouped_lights.py::test_a_collections_own_lights_come_before_its_sub_collections`
  - `test_group_actions.py::test_select_group_selects_only_the_lights_in_it_and_its_sub_collections`
  - `test_row_controls.py::test_range_runs_upwards_too_and_skips_lights_in_collapsed_groups`
- `make test` passes in full (103 tests).
- Manual (GUI): in grouped view, Scene Collection lights are at the top, and inside `Set` its own lights come before the `Lamps` sub-group.

## Afterwards
Append a `## v3 task 01: own lights first` entry to ARCHITECTURE.md. Note that the ordering note at the end of the file now matches the code.
