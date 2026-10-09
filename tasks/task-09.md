# Task 09: Built-in presets applied to selected lights

**Depends on:** task-02

## Goal
Apply a known setup (power, color, soft-size radius) to selected, compatible lights.

## Scope
- Ship built-in presets as data (e.g. `presets/builtin.json` or a Python dict): "Candle", "60W Bulb", "Daylight", each with `type_compat` (e.g. Point/Spot/Area vs Sun), `power`, `color`, `radius`.
- Preset dropdown in the panel plus an "Apply" operator.
- For each selected light of a compatible type: set `energy`, `color`, and the soft-size property (`shadow_soft_size` for point/spot/sun-angle equivalent as appropriate, `size` for area if applicable). Skip incompatible lights and report how many were skipped via `self.report`.
- Operator supports undo.

## Out of scope
Saving user presets (task 10).

## Done when (testable)
- Applying "60W Bulb" to a selected point light and a selected sun changes only the point light (AC 11).
- Power, color and radius all match the preset on the changed light (AC 11).
- Unselected lights are untouched, and a skipped-count message appears.
- One undo reverts the application.
