# Task 04: Panel order and Presets starts closed

**Depends on:** task-03
**Group:** Active Light panel · **Source:** `.notes/v6-decisions.md` items 7, 8

## Goal
The sidebar's Lights tab reads **Active Light → World → Intensity → Presets → Lights**. The short panels stay at fixed places and the tall Lights list goes last. Presets starts closed, and Intensity stays open.

## Scope
- Set the order with `bl_order` on each of the five panels. This replaces v5 decision 12's order (registration order).
- `LIGHTHOUSE_PT_presets`: `bl_options = {'DEFAULT_CLOSED'}`. Intensity keeps its default (open).
- **Verify first**: whether `bl_order` changes the layout of a file where the user already dragged panels, or only new ones. Write the result in ARCHITECTURE.md. If it overrides a dragged layout, say so in the README rather than working around it.

## Done when (testable)
- Test: the five panels' `bl_order` values sort into Active Light, World, Intensity, Presets, Lights.
- Test: `LIGHTHOUSE_PT_presets.bl_options` contains `DEFAULT_CLOSED`, and `LIGHTHOUSE_PT_intensity`'s doesn't.
- `make test` passes, and the existing panel-order test in `tests/test_panels.py` is updated to the new order.
- Manual (GUI): in a fresh file the tab shows the new order with Presets closed. Open a file saved with 1.3.x where panels were dragged, and note what happens (the Verify).

## Afterwards
Append a `## v6 task 04: Panel order` entry to ARCHITECTURE.md with the Verify result, replacing v5 decision 12's order wherever it is described.
