# Task 03: Name search, type filter, alphabetical sort

**Depends on:** task-02

## Goal
Make long light lists manageable.

## Scope
- Scene-level (or WindowManager) properties: `name_filter` (string, live-updating search) and `type_filter` (enum: All, Point, Sun, Spot, Area).
- Filter controls at the top of the panel.
- List sorted alphabetically (case-insensitive) by object name.

## Out of scope
Persisting filters across files, multi-type selection.

## Done when (testable)
- Typing "key" shows only lights whose names contain "key" (case-insensitive) (AC 4).
- Choosing type "Spot" shows only spot lights; combining with the search applies both (AC 4).
- Lights named "Zed", "alpha", "Beta" appear as alpha, Beta, Zed.
- Clearing filters restores the full list.
