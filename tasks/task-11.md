# Task 11: Light linking icon on the row

**Depends on:** task-10
**Group:** Light linking · **Source:** `.notes/new-features-decisions.md` item 23

## Goal
A light whose receiver collection isn't empty shows a link icon after its name, next to ⓘ. Like ⓘ, it is drawn only when needed and the name button shrinks to make room, so the columns don't shift. Its tooltip summarizes the linking, for example "Lights only 3 objects, excludes 1". Clicking it opens the light's details.

## Scope
- `lighthouse/lights.py`: `linking_tooltip(included, excluded)` builds the summary:
  - Includes only: "Lights only 3 objects".
  - Both: "Lights only 3 objects, excludes 1".
  - Excludes only: "Excludes 2 objects".
  - Neither: "", and no icon is drawn.
  Counts come from `receivers()`.
- `lighthouse/__init__.py`:
  - `lighthouse.light_linking_info` (`INTERNAL`): `name`, `library`, `included` and `excluded`. Its `description()` returns `linking_tooltip()`. `invoke` opens the light's details, closing others unless Shift is held, as `toggle_details` does. If they are already open it leaves them open, so it never closes them.
  - `draw_light()`: right after the ⓘ button, draw it with a link icon (for example `LINKED`) and no emboss, only when the tooltip isn't "".

## Open questions
Not decided: how child collections are counted in the tooltip. Default: name them separately when there are any, for example "Lights only 2 objects and 1 collection, excludes 1".

## Done when (testable)
- Test: `linking_tooltip()` for (3, 0), (3, 1), (0, 2), (1, 0) and (0, 0), including the singular wording.
- Test: `light_linking_info` on a light with closed details opens them and closes other lights' details. On a light whose details are already open, they stay open.
- Test (Recorder): a light with receivers draws the link button after `INFO` (when ⓘ is drawn) and before power. A light with no receiver collection, or an empty one, draws none.
- `make test` passes.
- Manual (GUI): the icon appears without shifting the power, color and toggle columns. The tooltip reads correctly, and clicking it opens the details at the Light Linking section.

## Afterwards
Append a `## v5 task 11: linking row icon` entry to ARCHITECTURE.md. Add `light_linking_info` to `tests/smoke_engines.py`.
