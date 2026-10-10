# Task 04: Lights list: empty state and expand/collapse all

**Depends on:** task-01
**Type:** UX polish (Lights panel) · **Source:** polish review, "Empty list", "Collapse all has no opposite"

## Goal
The Lights panel explains why it is empty and offers a way out. The header's collapse button becomes a toggle that also expands every group.

## Scope
- **Empty state:**
  - `lighthouse/lights.py`: `empty_message(view_layer, name_filter, type_filter)` returns `None` when `list_entries()` would draw rows. Otherwise it returns `"No lights in this view layer"` or `"No lights match the filters"`. Keeping this in a function makes it testable without drawing.
  - `LIGHTHOUSE_PT_lights.draw()`: when there is a message, draw it as a label with the `INFO` icon. In the filter case, add a **Clear Filters** button.
  - New `lighthouse.clear_filters` (`INTERNAL`, no `UNDO`) sets `name_filter = ""` and `type_filter = 'ALL'`.
  - A view layer whose lights are all inside collapsed groups is not empty: the group headers still draw.
- **Expand/collapse all:**
  - `lighthouse/lights.py`: `listed_groups(view_layer, type_filter)` returns every collection with a listed light, directly or in a sub-collection, ignoring collapse state, so collapsed parents don't hide their children from the check.
  - Replace `lighthouse.collapse_all_groups` with `lighthouse.toggle_all_groups` (`INTERNAL`, no `UNDO`). If every collection from `listed_groups()` is collapsed, it expands all of them. Otherwise it collapses all of them.
  - Header icon: `FULLSCREEN_ENTER` when everything is collapsed (the next press expands), `FULLSCREEN_EXIT` otherwise. The tooltip names both behaviours.
  - Update `tests/smoke_engines.py` and `tests/acceptance.md` for the new idname.

## Out of scope
Showing collections without lights, per-group "collapse children".

## Done when (testable)
- Test: `empty_message` returns the view-layer message with no lights, the filter message when the search matches nothing or the type filter excludes every light, and `None` when everything is collapsed but lights exist.
- Test: `clear_filters` resets both filters.
- Test: with `Set/Lamps` and `Props` holding lights, `toggle_all_groups` collapses all three. A second call expands all three. With only `Props` collapsed, a call collapses the rest instead of expanding.
- Test: `toggle_all_groups` has no `UNDO` in `bl_options`. Replaces the existing collapse-all test.
- `make test` passes.
- Manual (GUI): each empty message shows, Clear Filters restores the list, and the header icon flips after each press.

## Afterwards
Append a `## v3 task 04: empty state and expand/collapse all` entry to ARCHITECTURE.md.
