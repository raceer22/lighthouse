# Task 07: Mute and Apply Preset ▸ on the selection

**Depends on:** task-06
**Group:** Right-click menu · **Source:** `.notes/v6-decisions.md` items 11, 14

## Goal
The light right-click menu can mute and apply a preset to several lights at once, using the same selection rule as task 06.

## Scope
- **Mute** acts on the lights given by task 06's rule. On a mixed selection it follows the clicked light: if that light is unmuted, every light in scope is muted, and if it is muted, they're all unmuted (like Ctrl+click on the Outliner's eye). The label says which: "Mute 3 Lights" / "Unmute 3 Lights", and plain "Mute" / "Unmute" for one.
  - Each light changed goes through `update_snapshot()`, exactly like the row's mute, so un-solo keeps the choice.
- **Apply Preset ▸**: a submenu listing the presets. Picking one applies it to the lights given by the rule. Today `apply_preset` acts on the selection only. Give it a way to take the menu's lights instead (e.g. a target light plus the rule) while the Presets panel keeps acting on the selection. Skipped lights are reported as now.
- Read-only lights in scope are skipped and reported, as in task 06.

## Done when (testable)
- Test: two muted lights and one unmuted, clicked on the unmuted one: all three end up muted. Clicked on a muted one instead: all three end up unmuted.
- Test: the Mute label reads "Mute 3 Lights" or "Unmute 3 Lights" to match.
- Test: Mute from the menu during a solo, then `exit_solo`, keeps those lights muted.
- Test: Apply Preset from the menu on an unselected light changes only that light. On a selected light it changes the whole selection.
- Test: the Presets panel's Apply still acts on the selection, unchanged.
- `make test` passes.
- Manual (GUI): with a mixed selection, right-click a muted light and an unmuted one in turn, and check the labels. Apply a preset to an unselected light from its menu.

## Afterwards
Update the `v6 task 05` entry in ARCHITECTURE.md (or add a `v6 task 07` entry) with the Mute rule and how Apply Preset gets its lights.
