# Task 08: Reveal active light

**Depends on:** task-01, task-04
**Group:** Navigation · **Source:** `.notes/new-features-decisions.md` item 12

## Goal
A header button unfolds every collection and lights row that hides the active light, so a light selected in the viewport can be found in the list. A light added with `+` into a folded collection is revealed on its own.

## Scope
- `lighthouse/lights.py`: `reveal(view_layer, obj)`. For each non-excluded collection that holds `obj` directly, it expands that collection and its ancestors (`lighthouse_collapsed = False`) and unfolds the collection's lights row, or the Scene Collection's fold. It changes nothing else. `_collection_paths(view_layer, wanted)` already returns each matching collection with its ancestors. A light in two collections is revealed in both.
- `lighthouse.reveal_active_light` (`INTERNAL`, no `UNDO`, like `toggle_group`). `poll()` requires the active object to be a light, so the button is greyed out otherwise. It goes in the list header.
- `add_light` calls `reveal()` on the new light after linking it.
- No handler on selection change. Revealing on its own would undo your folding and mark the file as changed.
- The panel can't be scrolled from Python, so the button only unfolds. It doesn't jump to the row.

## Out of scope
Filters: a light hidden by the search or type filter stays hidden. Flat mode has nothing to unfold.

## Done when (testable)
- Test: `Bulb` is in `Set/Interior/Lamps`, every collection is collapsed and `Lamps`' lights row is folded (it has a sub-collection). After `reveal_active_light`, `Set`, `Interior` and `Lamps` are expanded, `Lamps`' lights row is open, and `list_entries()` contains `Bulb`.
- Test: a sibling collection `Props` stays collapsed.
- Test: a light linked into two collections is revealed in both.
- Test: a Scene Collection light behind a folded Scene Collection is revealed.
- Test: `poll()` is `False` with a mesh or nothing active.
- Test: `add_light` with a collapsed `Lamps` active leaves `Lamps` and its ancestors expanded.
- `make test` passes.
- Manual (GUI): the button is greyed out without an active light. Pressing it after clicking a light in the viewport shows its row.

## Afterwards
Append a `## v4 task 08: reveal active light` entry to ARCHITECTURE.md. Add `reveal_active_light` to `tests/smoke_engines.py`.
