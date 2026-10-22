# Task 06: Delete, Duplicate, Duplicate Linked on the selection

**Depends on:** task-05
**Group:** Right-click menu · **Source:** `.notes/v6-decisions.md` items 11–13

## Goal
The light right-click menu can delete and duplicate lights, which the list had no way to do. These entries act on the selection the way the Outliner does: every selected light when the clicked light is selected, otherwise only the clicked light.

## Scope
- A helper for the Outliner rule (clicked light plus its selection, or just the clicked light), used by these entries and again by task 07. Labels show the count: "Delete 3 Lights", and plain "Delete" for one.
- **Duplicate**: a full copy of the object and its light data (like Shift+D). **Duplicate Linked**: a new object sharing the light data (like Alt+D). Each copy goes into the same collection(s) as its original, with no move or grab afterward. The copies become the selection, with the clicked light's copy as the active object. Shared data already shows in the row's ⓘ tooltip, so nothing else is needed.
- **Delete**: removes the objects right away, with no confirmation. Ctrl+Z brings them back. Only the objects are removed, and light data left with no users is cleaned up by Blender, as with the Outliner's Delete.
- Read-only lights in scope are skipped and reported, the same way as other bulk actions. When every light in scope is read-only, the operator cancels with a warning.
- A light that is part of the current solo: deleting it leaves solo working (its snapshot item points at nothing, and `unsolo` already skips those). A duplicate made during solo is shown, since it's a new light the user just asked for.

## Done when (testable)
- Test: with 3 lights selected and the clicked one among them, Delete removes all 3, and the label says "Delete 3 Lights".
- Test: with 3 lights selected and the clicked one not among them, Delete removes only the clicked light.
- Test: Duplicate gives a new object with new light data in the same collection. Duplicate Linked gives a new object with the same `data`.
- Test: deleting a light whose data is shared leaves the other object and its data alone.
- Test: deleting a soloed light, then `exit_solo`, restores the other lights without errors.
- Test: a library light in the selection is skipped and reported.
- `make test` passes.
- Manual (GUI): select three lights, right-click one of them, then Delete and Ctrl+Z. Duplicate Linked a light and check the ⓘ tooltip on both rows.

## Afterwards
Append a `## v6 task 06: Delete and duplicate` entry to ARCHITECTURE.md (the selection rule, what Delete removes). Add the new operators to `tests/smoke_engines.py`.
