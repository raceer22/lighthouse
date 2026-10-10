# Task 05: Solo you can always leave, and that keeps your changes

**Depends on:** task-01
**Type:** bug fix + UX (solo) · **Source:** polish review, "Solo can get stuck"

## Goal
While solo is on, the Lights panel shows a button that ends it, even if the soloed light or group has been deleted. Muting a light or hiding a group during solo is kept after un-solo instead of being overwritten by the snapshot.

## Scope
- **Exit Solo:**
  - `lighthouse/lights.py`: rename `_unsolo` to public `unsolo(solo)`. Add `solo_label(solo)`, which returns the soloed light's or collection's name, or `"deleted"` when the target is gone.
  - New `lighthouse.exit_solo` (`UNDO`) calls `unsolo(context.scene.lighthouse_solo)`. `poll()` requires `solo.active`.
  - `LIGHTHOUSE_PT_lights.draw()`: while `solo.active`, draw a full-width row under the header with `Exit Solo (<solo_label>)`, the `SOLO_ON` icon and `depress=True`.
- **Mute during solo:** in `LIGHTHOUSE_OT_mute_light`, while `solo.active` and the light has a snapshot item, write the new `hide_render`/`hide_viewport` to that item as well as to the object. Un-solo then restores the user's latest choice. The rule is that what you set during solo is what you get afterwards.
- **Group hide during solo:** in `LIGHTHOUSE_OT_hide_group`, do the same for the collection's snapshot item if it has one. Collections solo never touched have no item, and un-solo leaves them alone.
- Put both snapshot updates in one `lights.py` helper, e.g. `update_snapshot(solo, id, hide)`, so the operators stay thin.
- Remove the "Known limits" lines that this task resolves from the task-05 section of ARCHITECTURE.md, or mark them fixed.

## Out of scope
Several solo slots, solo per view layer.

## Done when (testable)
- Test: solo a light, delete it, then `exit_solo` restores every other light's and collection's flags exactly. `solo_label` read `"deleted"` before the exit.
- Test: `exit_solo` fails its poll when solo is off.
- Test: solo `Key`, then mute `Fill` (hidden by solo) to unmute it, and un-solo. `Fill` stays visible even though it was muted before solo.
- Test: solo `Key`, mute `Key`, un-solo: `Key` stays muted.
- Test: solo a light inside hidden group `Interior` (solo unhides it), hide `Interior` with `hide_group`, then un-solo. `Interior` stays hidden. A collection solo never touched isn't changed by un-solo.
- `make test` passes.
- Manual (GUI): the Exit Solo row appears and disappears with solo, its label follows renames, and one Ctrl+Z after Exit Solo brings solo back.

## Afterwards
Append a `## v3 task 05: exit solo and snapshot updates` entry to ARCHITECTURE.md with (1) new components, (2) how mute and hide now flow into the snapshot, (3) quirks.
