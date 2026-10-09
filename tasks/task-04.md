# Task 04: Hidden, library, and linked-data row states

**Depends on:** task-02

## Goal
Rows correctly reflect lights that are hidden, come from a library, or share a datablock.

## Scope
- Include hidden lights (`hide_viewport`/`hide_render`/`hide_get()`) in the list, drawn greyed out (`row.active = False`) while staying listed.
- Library lights (`id.library` or `override_library` non-editable) draw with `enabled = False` so controls are read-only.
- Rows whose `light.users > 1` show a "linked" indicator (e.g. `LINKED` icon with tooltip).

## Out of scope
Mute/solo behaviour (task 05).

## Done when (testable)
- A light hidden in the viewport and render still appears, greyed out (AC 6).
- A linked-in library light appears and its slider and swatch cannot be edited (AC 6).
- Two objects sharing one light datablock both show the linked indicator; an unshared light does not.
- Editing power on one linked row changes both rows.
