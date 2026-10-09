# Task 07: +1 EV / -1 EV buttons

**Depends on:** task-06

## Goal
One-click doubling and halving of light power.

## Scope
- Two buttons in the Intensity section: "+1 EV" (x2) and "-1 EV" (x0.5).
- Reuse the scale operator/core function from task 06 with factor 2 or 0.5, honouring the chosen scope.

## Out of scope
Fractional EV values.

## Done when (testable)
- A 100 W light becomes 200 W with +1 EV and 50 W with -1 EV (AC 8).
- Works on point, spot, area and sun lights (sun in W/m²) (AC 8).
- Scope All vs Selected is respected.
- One undo reverts a button press.
