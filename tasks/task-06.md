# Task 06: Scale slider with All/Selected scope

**Depends on:** task-02

## Goal
A destructive intensity scale that multiplies light power by a factor, with one-step undo.

## Scope
- Panel section "Intensity" with a factor slider/field (default 1.0) and a scope toggle (All lights / Selected lights).
- "Apply" operator multiplies `light.energy` by the factor for the scoped lights. Each light datablock is scaled once even if shared by several objects.
- Scope is the whole view layer or the selection, regardless of the list filters. Skip library (non-editable) lights.
- Operator registered with `UNDO` so a single Ctrl+Z restores all values.

## Out of scope
EV buttons (task 07), keyframes (task 08).

## Done when (testable)
- Lights at 100 W, 200 W, 400 W with factor 0.5 and scope All become 50, 100, 200 W (AC 7).
- With scope Selected, only selected lights change (AC 7).
- One Ctrl+Z restores every previous value (AC 7).
- A shared datablock is scaled once, not twice.
