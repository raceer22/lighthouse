# Task 10: Mutes made during a solo stick

**Depends on:** task-09
**Group:** Additive solo · **Source:** `.notes/v6-decisions.md` item 21

## Goal
A light muted during a solo stays hidden when the solo changes later. Without this, Shift+adding another target recomputes visibility and quietly shows a light the user just muted.

## Scope
- `LIGHTHOUSE_PG_solo_object`: a "muted during solo" flag.
- `update_snapshot()`: set the flag when a light is muted during solo, and clear it when it is unmuted. This covers the row's Mute, the Active Light panel's Mute and the right-click menu's Mute, since all of them call it.
- Recomputing visibility (task 09's adds, removes and replaces) keeps lights with the flag hidden, even when they belong to a soloed target.
- Un-solo is unchanged: it restores the snapshot flags, which `update_snapshot()` already set to muted.
- A new solo started from scratch (after Exit Solo) starts with every flag cleared.

## Done when (testable)
- Test: solo group G, mute light A inside G, then Shift+add light B: A stays hidden and B is shown.
- Test: same, then unmute A: A is shown again, and a later Shift+add keeps it shown.
- Test: solo G, mute A, then a plain click on another light (replace) and Shift+add G back: A stays hidden.
- Test: solo, mute A, Exit Solo: A is muted. Solo again: A's flag starts cleared, and the solo shows or hides it as the targets say.
- `make test` passes, and task 09's tests still pass.
- Manual (GUI): solo a group, mute one light in it, then Shift+click another light's star. The muted light stays dark.

## Afterwards
Add the flag to the solo data-flow notes in ARCHITECTURE.md (`## v6 task 10: Mutes during solo`).
