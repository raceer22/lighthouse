# Task 04: Scene Collection row

**Depends on:** task-01, task-02, task-03
**Group:** Collections · **Source:** `.notes/new-features-decisions.md` items 5, 10 (Scene Collection part)

## Goal
The grouped list starts with a `Scene Collection` header. From it you can fold the Scene Collection's own lights, move selected lights into it and make it the active collection. The rest of the tree doesn't shift: top-level collections stay at depth 0.

## Scope
- `lighthouse/lights.py`: in grouped mode with no search, `list_entries()` starts with an entry for `scene.collection` (for example a `GroupEntry` at depth 0, or a dedicated `SceneEntry`). Its own lights follow at depth 0 unless `scene.collection.lighthouse_lights_collapsed` is set, and the top-level collections follow at depth 0 as today. Flat mode and search have no Scene Collection row.
- Targeting the master collection: it is not in `bpy.data.collections`, so `find_collection()` can't return it. Use `name=""` to mean `context.scene.collection` (no ID can have an empty name) in the operators this row uses: `toggle_lights_row`, `move_to_group` and `set_active_collection`. Check that `lighthouse_lights_collapsed` on the master collection is saved with the scene.
- `draw_scene_row()`:
  - A triangle that folds the Scene Collection's own lights. This replaces the lights row from task 01 for this collection. When the Scene Collection has no listed lights of its own, draw a blank of the same width instead.
  - The name is the `set_active_collection` button, drawn pressed when the Scene Collection is active.
  - **Move selected here**. No Hide or Solo, because the master collection has no hide flags. Keep Move here in the same column as the other headers' Move here button.
- `toggle_all_groups`: when expanding, also unfold the Scene Collection's lights. Collapse All leaves them alone, and they don't count towards the "all collapsed?" check.
- `move_lights()` already unlinks from `scene.collection` (v2 quirk), so moving into it needs no new logic.

## Open questions
Not decided: whether the row shows Select, and whether its label shows a count. Defaults: no Select (leave a blank slot so the columns stay aligned) and the plain label `Scene Collection`.

## Out of scope
Empty collections (task 05), revealing a light (task 08).

## Done when (testable)
- Test: `list_entries()` starts with the Scene Collection entry, then `Sun` (a Scene Collection light) at depth 0, then `group Set 0 (…)`. Depths below are unchanged from task 01.
- Test: folding the Scene Collection hides `Sun` and nothing else.
- Test: `move_to_group(name="")` with `Bulb` (in `Lamps`) selected links it into the Scene Collection and unlinks it from `Lamps`.
- Test: `set_active_collection(name="")` makes the master layer collection active, and `add_light` then links into `scene.collection`.
- Test: Expand All unfolds the Scene Collection's lights. Collapse All leaves them unfolded.
- Test: the Scene Collection's fold survives `save_as_mainfile` and `open_mainfile`.
- `make test` passes.
- Manual (GUI): the row sits at the top without indenting the tree, Move here lines up with the other headers, and the name is pressed while the Scene Collection is active (also after clicking it in the Outliner).

## Afterwards
Append a `## v4 task 04: Scene Collection row` entry to ARCHITECTURE.md. Add a `name=""` call of `move_to_group` and `set_active_collection` to `tests/smoke_engines.py`.
