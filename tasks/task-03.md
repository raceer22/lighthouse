# Task 03: Group header actions: collapse, select, move, hide

**Depends on:** task-02
**PRD-v2 sections:** Lights list header (collapse all), Groups (group header, collapsed state), Light rows (dimming) · **AC:** 7, 8, 9, 13

## Goal
Group headers become usable. A group can be collapsed (the state is saved with the file and creates no undo step), all of its lights can be selected, the selected lights can be moved into it, and it can be hidden. Rows inside a hidden group are drawn dimmed.

## Scope
- **Collapse:**
  - Register `Collection.lighthouse_collapsed` (BoolProperty) and remove it in `unregister()`.
  - The disclosure triangle is an operator, `lighthouse.toggle_group` (collection name, `bl_options` without `UNDO`), not a `prop()`, because `prop()` on ID data pushes an undo step.
  - `list_entries()` skips everything below a collapsed group. The header stays and keeps its count.
- **Collapse all:** a header button (grouped view only), `lighthouse.collapse_all_groups`, with no `UNDO`. It collapses every collection in the view layer tree.
- **Header order** (left to right): triangle, `Name (N)`, Select, Move selected here, Hide. Leave room for Solo, which comes in task 04.
- **Select** (`lighthouse.select_group`, `UNDO`):
  - Selects every listed light in the group and its sub-collections (it follows the type filter, like the count).
  - `invoke()` reads `event.shift` into an `extend` property. Click replaces the selection, and Shift+click adds to it.
  - When replacing, make the first light active unless the active object is already in the group.
- **Move selected here** (`lighthouse.move_to_group`, `UNDO`):
  - Links each selected light object into the target collection and unlinks it from every other collection, the Scene Collection included.
  - Read-only objects (`obj.library`, or a system override) are skipped.
  - Report how many lights were moved and how many skipped. Refuse with an error when the target collection is itself read-only.
- **Hide** (`lighthouse.hide_group`, `UNDO`):
  - Toggles the collection's own `hide_render` and `hide_viewport` together, the outliner's camera and monitor toggles. Like mute: both on unless both are already on.
  - Light object flags are never touched. The icon shows the hidden state with `depress=`.
- **Dimming:**
  - `row_state().dimmed` becomes `not obj.visible_get(view_layer=…)`, which covers lights in hidden groups. Keep v1's render-hidden case dimmed so the existing tests still hold.
  - `muted` still only reflects the object's own flags.

## Out of scope
Group solo and the solo rewrite (task 04). Drag and drop.

## Done when (testable)
- Test: `toggle_group` flips `lighthouse_collapsed`, and `'UNDO'` is not in the `bl_options` of `toggle_group` or `collapse_all_groups` (AC 13).
- Test: a collapsed group keeps its header and count, and its children and lights disappear from the entries.
- Test: after `save_as_mainfile` to a temp file and `open_mainfile`, the group is still collapsed (AC 13).
- Test: `collapse_all_groups` collapses every collection in the tree.
- Test: `select_group` on a parent selects the lights in it and its sub-collections and nothing else. With `extend=True`, the earlier selection is kept (AC 7).
- Test: a selected light linked into `A`, `B` and the Scene Collection ends up only in `C` after a move to `C`. An unselected light is untouched, and a library light (see the fixtures in `tests/test_row_states.py`) is skipped (AC 8).
- Test: hiding a group sets both collection flags, and the light flags don't change. A light muted before the hide is still muted after the unhide. While the group is hidden, its lights' rows are `dimmed` but not `muted` (AC 9).
- `make test` passes.
- Manual (GUI): the header order is correct, and Shift+click on Select adds to the selection. Edit › Undo History shows no entry for collapse or collapse all.

## Afterwards
Append a `## v2 task 03: group header actions` entry to ARCHITECTURE.md with (1) new components, (2) how data flows between them, (3) Blender API quirks encountered (for example whether `visible_get` needs `view_layer.update()` in tests).
