# Task 11: Expandable detail section and render-engine robustness

**Depends on:** task-04

## Goal
Expose the remaining light properties per row, only where they exist, and verify behaviour under both render engines.

## Scope
- Per-row expand toggle (state stored per object, e.g. a custom property or a WindowManager set) revealing: soft-size radius / sun angle, specular factor, diffuse/volume factors, shadow toggle, and Cycles-only options (e.g. `cycles` settings such as max bounces, cast shadow, multiple importance) when `scene.render.engine == 'CYCLES'`.
- Use `hasattr`/`getattr` guards so no property access fails on lights lacking it (e.g. sun has no radius, area lacks spot options).
- No shape parameters or type switching.

## Out of scope
Spot size, area shape, light type changes.

## Done when (testable)
- Expanding a point, sun, spot and area light under EEVEE shows only properties valid for each type, with no console errors (AC 13).
- Switching the render engine to Cycles and back updates visible properties without errors (AC 13).
- Details edit the real light and appear in the Properties editor.
- Collapsed rows stay compact.
