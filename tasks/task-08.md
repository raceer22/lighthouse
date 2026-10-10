# Task 08: World in solo

**Depends on:** task-07
**Group:** World · **Source:** `.notes/new-features-decisions.md` item 17

## Goal
The World can be soloed: this darkens every lamp and un-mutes the World if it was muted. Soloing a lamp or a group leaves the World alone; for a full solo the user mutes the World themselves. Only one thing is soloed at a time, and the header's Exit Solo button also ends a World solo, restoring the World's mute together with the lights.

## Scope
- `lighthouse/__init__.py`, `LIGHTHOUSE_PG_solo` gains:
  - `world_soloed`: the World is the solo target.
  - The World's snapshot: `world` (a PointerProperty to `bpy.types.World`), `world_node` (the muted node's name) and `world_muted` (its `mute` before solo), plus a flag saying whether the snapshot was taken. Only World solo takes it.
- `lighthouse/lights.py`:
  - `_solo()` (lamp and group solo) does not touch the World.
  - `toggle_solo_world(solo, view_layer, scene)` hides every light (snapshotting them like `_solo()`), snapshots the World node and un-mutes it. A scene with no world, or no node to mute, only hides the lights. Pressing it while the World is soloed calls `unsolo()`.
  - Switching between lamp, group and World solo keeps the existing light snapshot, as switching between lamps does today. Switching from World solo to a lamp or group solo restores the World node's `mute` from the snapshot right away and clears the World snapshot.
  - `unsolo()` restores the World node's `mute` when a World snapshot exists and the world and the node still exist, then clears the snapshot and `world_soloed`.
  - `update_snapshot()` also handles the World: `mute_world` during a World solo writes the new flag into the snapshot, so un-solo keeps it. Without a World snapshot (e.g. during a lamp solo) `mute_world` is a plain mute.
  - `solo_label()` returns "World" for a World solo.
- `lighthouse/__init__.py`:
  - `lighthouse.solo_world` (`REGISTER`, `UNDO`).
  - The World panel's top row gets Solo next to Mute (`SOLO_ON`/`SOLO_OFF`, pressed while the World is soloed).
  - `mute_world` calls `update_snapshot()`.

## Done when (testable)
- Test: soloing a lamp leaves the World's Background `mute` unchanged (both muted and unmuted), and un-solo leaves it unchanged too.
- Test: `solo_world` hides every light and leaves the World unmuted, also when it was muted before. Pressing it again restores every light's and the World's flags.
- Test: `solo_world` on a muted World, then soloing a lamp, re-mutes the World immediately. `exit_solo` then restores the lights and leaves the World muted.
- Test: `solo_world`, then `mute_world`, then un-solo leaves the World muted. `mute_world` during a lamp solo, then un-solo, leaves the World in the state chosen.
- Test: `solo_world` with `scene.world = None` hides the lights and un-solo restores them.
- Test: after deleting the World node during a World solo, un-solo still restores the lights.
- Test: `solo_label()` is "World" during a World solo, and `exit_solo`'s description says so.
- `make test` passes. The existing tests in `tests/test_mute_solo.py` and `tests/test_exit_solo.py` still pass unchanged.
- Manual (GUI): solo a lamp and the HDRI stays lit. Mute the World and solo it: only the HDRI lights the scene. Exit Solo brings everything back, with the World muted again.

## Afterwards
Append a `## v5 task 08: World in solo` entry to ARCHITECTURE.md and update the solo data-flow notes. Add `solo_world` and a lamp solo with a world (World left unchanged) to `tests/smoke_engines.py`.
