# Task 02: Expand All opens lights rows

**Depends on:** task-01
**Group:** Objects (lights row) · **Source:** `.notes/new-features-decisions.md` item 3

## Goal
Expand All shows everything, folded lights rows included. Collapse All and the header icon still only consider collections, so a folded lights row never changes what the button does.

## Scope
- `lighthouse.toggle_all_groups`: when it expands (every listed collection is collapsed), it also sets `lighthouse_lights_collapsed = False` on every collection from `listed_groups()`. When it collapses, lights rows are left as they are.
- The "all collapsed?" check, used both for the action and for the `FULLSCREEN_ENTER` / `FULLSCREEN_EXIT` icon, still reads only `lighthouse_collapsed`. That's today's code. Pin it with a test.
- The tooltip mentions lights rows, for example "Expand every collection and lights row when all collections are collapsed, otherwise collapse every collection".

## Out of scope
The Scene Collection's fold (task 04 adds it to Expand All).

## Done when (testable)
- Test: `Set` (own lights plus `Lamps`) and `Props` are both collapsed, and `Set`'s lights row is folded. One `toggle_all_groups` call expands both collections and unfolds `Set`'s lights row.
- Test: with everything expanded and `Set`'s lights row folded, one call collapses both collections and the row stays folded.
- Test: with every collection expanded and only lights rows folded, the next call collapses: folded rows don't count as "collapsed".
- `make test` passes.
- Manual (GUI): the header icon doesn't change when you fold or unfold a lights row.

## Afterwards
Append a `## v4 task 02: Expand All and lights rows` entry to ARCHITECTURE.md.
