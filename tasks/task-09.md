# Task 09: Shift+click adds to solo

**Depends on:** task-08, task-05
**Group:** Additive solo · **Source:** `.notes/v6-decisions.md` items 10, 16–20, 22, 23

## Goal
Several lights and groups can be soloed together. Shift+click on a star adds that light or group to the current solo, or removes it if it's already soloed. A plain click works as now. The right-click menu gets **Add to Solo**, and Exit Solo's tooltip names what is soloed.

## Scope
- `solo_light` and `solo_group`: an `invoke` that reads `event.shift` into an `extend` property (`SKIP_SAVE`), so tests can pass `extend=True` directly. The row's tooltip mentions Shift+click.
- `lighthouse/lights.py`, solo with `extend`:
  - Not soloed yet: starts a solo with that one target, the same as a plain click.
  - The target isn't soloed: add it. If it is: remove it. **Removing the last target ends solo**, exactly like Exit Solo.
  - Lights and groups mix freely. The visible set is the union: each soloed light, plus every light in each soloed group. The collections unhidden are the union of each target's paths. Recompute visibility from the snapshot and the full list after every change.
  - The snapshot is still taken once, at the first solo. Later adds snapshot only lights and collections that have no item yet, as `_solo()` does now.
- Plain click while several items are soloed **replaces them** with the clicked item, even if it was already part of the solo. Plain click on the star of the only soloed item still ends solo.
- World: **Shift+click on the World's star works like a plain click** (World-only solo, which replaces a lamp solo). A lamp or group Shift+click during a World solo leaves World solo, as a plain click does now. The World stays exclusive (this supersedes v5 decision 17's "one thing at a time" only for lamps and groups).
- `row_state().soloed` and `group_soloed()` are True for every target in the list, so every soloed star is pressed.
- **Exit Solo tooltip**: up to 3 names, then "…" ("Exit Solo (Key, Practicals, Rim, …)"), following `shared_label`'s `SHARED_NAMES`. Deleted targets are dropped from the list of names, and "deleted" is used only when none are left.
- Right-click menu (task 05): **Add to Solo** after Solo, acting on the clicked light only. It runs `solo_light` with `extend=True`, and its label reads "Remove from Solo" when the light is already soloed.

## Done when (testable)
- Test: solo light A, then `extend` on light B: both A and B are shown and every other light is hidden. `extend` on A again leaves only B.
- Test: `extend` on the last soloed light ends solo and restores every snapshotted flag.
- Test: solo light A, then `extend` on group G: A and every light in G (and its sub-collections) are shown, and G's hidden parent collections are unhidden.
- Test: with A and B soloed, a plain click on A leaves only A soloed. A plain click on A again ends solo.
- Test: `extend` on the World behaves like `solo_world` and clears the lamp targets. `extend` on a lamp during a World solo restores the World's mute.
- Test: the Exit Solo description lists up to 3 names then "…", and drops deleted targets.
- Test: Add to Solo from the menu adds the clicked light, and its label reads "Remove from Solo" once it is soloed.
- `make test` passes.
- Manual (GUI): solo Key, then Shift+click Rim's star and a group's star. Hover Exit Solo. Shift+click Key's star again, then plain-click Rim's.

## Afterwards
Update the solo data-flow notes in ARCHITECTURE.md and append a `## v6 task 09: Additive solo` entry. Add an `extend` solo to `tests/smoke_engines.py`.
