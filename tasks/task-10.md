# Task 10: Light linking: exclude, clear and sharing

**Depends on:** task-09
**Group:** Light linking · **Source:** `.notes/new-features-decisions.md` items 20 (Include/Exclude, Exclude Selected, Clear), 22

## Goal
Each receiver row gets an Include/Exclude toggle. **Exclude Selected** and **Clear** join Link Selected above the list. Selected items already in the list only change state. When the receiver collection is shared with other lights, the section says so ("Shared with Key, Rim (3 lights)"), so editing it is a known change to all of them.

## Scope
- `lighthouse/lights.py`:
  - `link_receivers()` from task 09 already sets the state. Exclude Selected is the same call with `'EXCLUDE'`.
  - `clear_receivers(light_obj)` empties the receiver collection: every object and child collection is unlinked.
  - `receiver_users(collection)`: the light objects whose `light_linking.receiver_collection` is this collection, sorted by name.
  - `shared_label(obj)`: "Shared with Key, Rim (3 lights)", naming the other lights. The count includes this one. Empty when the collection isn't shared.
- `lighthouse/__init__.py`:
  - Above the list: Link Selected, Exclude Selected (`link_receivers` with `state='EXCLUDE'`) and Clear (`lighthouse.clear_receivers`, `REGISTER`, `UNDO`, greyed out when the list is empty).
  - Each row draws its `link_state` directly (`prop(item.light_linking, "link_state", text="", ...)`) as a two-state Include/Exclude control. Drawing the RNA property directly gives undo with no extra operator.
  - The shared label, with an `INFO` icon, sits under the buttons when `shared_label()` isn't empty.

## Open questions
Not decided:
- What Clear does to a shared collection. Default: empty it, keeping it assigned. That follows item 22: every sharing light changes, as the label warns. The alternative is to unassign the collection from this light only.
- How many names the label lists. Default: at most 3, then "…".

## Done when (testable)
- Test: Exclude Selected with `Cube` (already Include) and `Plane` (new) selected flips `Cube` to `EXCLUDE`, adds `Plane` as `EXCLUDE`, and leaves `Sphere` as `INCLUDE`, with no duplicates.
- Test: setting `link_state` on a row's item changes what `receivers()` reports.
- Test: `clear_receivers` leaves the collection assigned and empty. A second light sharing it is also empty.
- Test: `shared_label()` for `Key`, `Rim` and `Fill` sharing one collection, read from `Fill`, is "Shared with Key, Rim (3 lights)". An unshared light gives "".
- Test (Recorder): the section draws all three buttons, a `link_state` prop per row and the shared label only when shared. Clear is disabled for an empty list.
- `make test` passes.
- Manual (GUI, Cycles): exclude one object and it goes dark under that light. Two lights sharing a receiver collection both show the label, and an edit in one shows in the other.

## Afterwards
Append a `## v5 task 10: exclude, clear and sharing` entry to ARCHITECTURE.md. Add Exclude Selected and `clear_receivers` to `tests/smoke_engines.py`.
