# Task 05: Show empty collections

**Depends on:** task-01
**Group:** Collections · **Source:** `.notes/new-features-decisions.md` items 6, 7, 8

## Goal
The grouped list can show every collection, including ones without (matching) lights. Then you can click an empty collection to make it active, or move lights into it. A toggle turns this off and gives back exactly today's list.

## Scope
- `LIGHTHOUSE_PG_settings.show_empty`: a BoolProperty, default `True`, on the WindowManager (not saved, not undone). `clear_filters` doesn't reset it. It is drawn as an icon toggle next to the grouped toggle (for example `OUTLINER_COLLECTION`). It only changes the grouped list, since search stays flat.
- `lighthouse/lights.py`:
  - `list_entries(..., show_empty=False)`: when on, every non-excluded collection is listed, and one without listed lights gets count `0` (so under a type filter, `(0)` means "no lights of this type"). The default stays `False`, so existing callers and tests keep today's behaviour. The panel, `select_light`'s `RANGE` and `toggle_all_groups` pass `settings.show_empty`.
  - The lights row rule from task 01 ("at least one listed sub-collection") counts empty sub-collections while they are shown.
  - `GroupEntry` says whether anything is under the collection (own listed lights or listed sub-collections, empty ones included), for example as a `foldable` field.
  - `listed_groups(..., show_empty=False)` follows the same rule, so Expand/Collapse All covers what is drawn. Collections with nothing under them are left out of the "all collapsed?" check, because they have no triangle that could show the state.
- `draw_group()`:
  - Triangle only when `foldable`. Otherwise draw a blank of the same width (for example `label(text="", icon='BLANK1')`) so names stay aligned.
  - With count `0`, Select and Solo are drawn but disabled (`enabled = False` on a sub-row), and Move here and Hide stay enabled. All four are always drawn so the columns line up.

## Out of scope
What the panel does when no lights match at all. It still returns early with the message until task 06.

## Done when (testable)
- Test: with `show_empty=True`, an empty `Props` is listed as `group Props 0 (0)`, nested empty `A/B` are both listed, and an excluded collection isn't listed.
- Test: with type filter `SUN`, a collection holding only point lights is listed with count 0 when `show_empty` is on and dropped when it is off.
- Test: with `show_empty=False`, the output matches the existing `tests/test_grouped_lights.py` expectations, unchanged.
- Test: `foldable` is `False` for an empty leaf and `True` for a collection whose only child is an empty collection.
- Test: a collection with its own lights and one empty sub-collection gets a lights row with `show_empty` on, and no lights row with it off.
- Test: `show_empty` defaults to `True`, and `clear_filters` leaves it as it is.
- `make test` passes.
- Manual (GUI): names line up whether or not a triangle is drawn. On a `(0)` collection, Select and Solo are greyed out, and Move here and Hide work.

## Afterwards
Append a `## v4 task 05: show empty collections` entry to ARCHITECTURE.md.
