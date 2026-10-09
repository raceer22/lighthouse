# Task 05: Mute and solo with exact visibility restore

**Depends on:** task-04

## Goal
Per-row mute and solo buttons that toggle `hide_render` and `hide_viewport` on the light object.

## Scope
- Mute: toggles both flags on that light only.
- Solo: on activation, save every light's current `hide_render`/`hide_viewport` (e.g. as a JSON custom property on the scene), then hide all other lights and unhide the soloed one.
- Un-solo: restore exactly the saved flags, then clear the saved state.
- Buttons show active state. Operators support undo.
- Handle edge cases: solo another light while soloing (switch solo without overwriting the saved snapshot), lights added or deleted during solo.

## Out of scope
Selection-based solo, multi-solo.

## Done when (testable)
- Mute hides only that light in viewport and render; pressing again unhides it (AC 10).
- Scene with lights A (visible), B (render-hidden), C (viewport-hidden): solo A hides B and C fully and the others; un-solo restores B and C to exactly their original flags (AC 10).
- Switching solo from A to B and then un-soloing restores the original state, not an intermediate one.
- No errors if a soloed light is deleted before un-solo.
