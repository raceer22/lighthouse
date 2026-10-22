# Task 08: Prefactor: solo holds a list of targets

**Depends on:** none
**Group:** Additive solo · **Source:** `.notes/v6-decisions.md` items 16, 23

## Goal
Solo stores what is soloed as a list of targets (each a light or a group) instead of one `light` or one `group`. Nothing changes for the user: a list with one item behaves exactly like today. This makes task 09's Shift+click a small change. It also answers how files saved in the middle of a solo with the old layout load.

## Scope
- `lighthouse/__init__.py`, `LIGHTHOUSE_PG_solo`: a `targets` CollectionProperty whose items hold either an object or a collection, in place of the `light` and `group` pointers. The visibility snapshot (`objects`, `collections`) and the World fields stay unchanged.
- `lighthouse/lights.py`: `toggle_solo_light`, `toggle_solo_group`, `group_soloed`, `row_state` (its `soloed`), `_solo`, `unsolo` and `solo_label` read and write the list. The behavior is the same as now: a click replaces the target, and clicking the only target ends solo.
- **Verify first**: save a file during a lamp solo and a group solo with the current add-on, then load it with this change. Decide from what happens:
  - If the old `light` / `group` values are still readable, move them into `targets` on load (a `load_post` handler), then drop the old properties.
  - If not, the solo still ends cleanly: `exit_solo` restores the snapshot (which hasn't changed) and the label falls back to "deleted".
  - Keep a small `.blend` from the old version as a test fixture if the suite can load one, otherwise describe the manual check.

## Done when (testable)
- `tests/test_mute_solo.py`, `tests/test_exit_solo.py`, `tests/test_world_solo.py` and every other existing solo test pass unchanged.
- Test: after soloing a light, `targets` holds one item pointing at it. After soloing a group, one item pointing at the collection.
- Test: soloing a second light replaces the target, and the list still has one item.
- The Verify result is written down, with a test or a manual check showing that an old mid-solo file can be un-soloed.
- `make test` passes.

## Afterwards
Update the solo data-flow notes in ARCHITECTURE.md and append a `## v6 task 08: Solo targets` entry with the Verify result.
