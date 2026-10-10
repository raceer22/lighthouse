# Task 08: World in solo

**Depends on:** task-07
**Group:** World · **Source:** `.notes/new-features-decisions.md` item 17

## Goal
Soloing a lamp or a group also mutes the World, so a solo shows only that light. The World can be soloed itself, which darkens every lamp. Only one thing is soloed at a time, and the header's Exit Solo button also ends a World solo, restoring the World's mute together with the lights.

## Scope
- `lighthouse/__init__.py`, `LIGHTHOUSE_PG_solo` gains:
  - `world_soloed`: the World is the solo target.
  - The World's snapshot: `world` (a PointerProperty to `bpy.types.World`), `world_node` (the muted node's name) and `world_muted` (its `mute` before solo), plus a flag saying whether the snapshot was taken. It is taken the first time solo touches the World, like the light snapshots.
- `lighthouse/lights.py`:
  - `_solo()` (lamp and group solo) mutes `world_mute_node()` after snapshotting it. A scene with no world, or no node to mute, is left alone.
  - `toggle_solo_world(solo, view_layer, scene)` hides every light (snapshotting them like `_solo()`) and un-mutes the World node. Pressing it while the World is soloed calls `unsolo()`.
  - Switching between lamp, group and World solo keeps the existing snapshot, as switching between lamps does today.
  - `unsolo()` restores the World node's `mute` when the world and the node still exist, then clears the snapshot and `world_soloed`.
  - `update_snapshot()` also handles the World: `mute_world` during solo writes the new flag into the snapshot, so un-solo keeps it.
  - `solo_label()` returns "World" for a World solo.
- `lighthouse/__init__.py`:
  - `lighthouse.solo_world` (`REGISTER`, `UNDO`).
  - The World panel's top row gets Solo next to Mute (`SOLO_ON`/`SOLO_OFF`, pressed while the World is soloed).
  - `mute_world` calls `update_snapshot()`.

## Done when (testable)
- Test: soloing a lamp mutes the World's Background. Un-solo restores it to unmuted, and to muted if it was muted before.
- Test: `solo_world` hides every light and leaves the World unmuted. Pressing it again restores every light's and the World's flags.
- Test: lamp solo, then `solo_world`, then `exit_solo` restores the original flags of both the lights and the World.
- Test: `mute_world` during a lamp solo, then un-solo, leaves the World in the state chosen during solo.
- Test: lamp solo with `scene.world = None` works as before.
- Test: after deleting the World node during solo, un-solo still restores the lights.
- Test: `solo_label()` is "World" during a World solo, and `exit_solo`'s description says so.
- `make test` passes. The existing tests in `tests/test_mute_solo.py` and `tests/test_exit_solo.py` still pass unchanged.
- Manual (GUI): solo a lamp and the HDRI goes dark. Solo the World and only the HDRI lights the scene. Exit Solo brings everything back.

## Afterwards
Append a `## v5 task 08: World in solo` entry to ARCHITECTURE.md and update the solo data-flow notes. Add `solo_world` and a lamp solo with a world to `tests/smoke_engines.py`.
