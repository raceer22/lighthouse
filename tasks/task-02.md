# Task 02: Row controls: select, power, color

**Depends on:** task-01

## Goal
Each row becomes usable: type icon, clickable name that selects the light, power slider, and color swatch, all editing the real light data.

## Scope
- Row layout: type icon (POINT/SUN/SPOT/AREA), name button, power slider (`light.energy`), color swatch (`light.color`).
- Name button runs an operator that deselects all, selects the object and makes it active.
- Units: suffix "W/m²" for sun, "W" for others.
- Controls bind directly to light data properties so undo/redo works through Blender's normal system.

## Out of scope
Mute/solo, filters, expandable details, linked/hidden/library states.

## Done when (testable)
- Dragging a row's power slider changes the light, and the Properties editor Light tab shows the same value (AC 3).
- Changing the swatch updates the light color in the Properties editor (AC 3).
- Clicking a name selects that light only and makes it active (AC 5).
- Sun rows show W/m², other rows show W.
- Ctrl+Z reverts a slider change.
