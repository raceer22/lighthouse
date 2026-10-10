# Task 07: World mute

**Depends on:** task-05
**Group:** World · **Source:** `.notes/new-features-decisions.md` items 13 (Mute), 16

## Goal
A Mute toggle in the World panel turns off the World's light by muting the node that feeds *World Output → Surface* (`node.mute`). Strength stays untouched. Like a muted lamp, the mute shows in the Shader Editor and is saved with the file. If the verify step allows, this also works for custom setups.

## Verify first
Does a muted Mix Shader or node group feeding World Output render black, or does it pass its first input through? Render a tiny image (for example 8×8 px, 1 sample, camera only) of a world with a Mix Shader of two bright Backgrounds, muted, in Cycles and EEVEE on 4.2 and 5.2, and read back the pixels. Do the same for a muted Background node.
- If both render black: mute `source` for every setup.
- Otherwise (the fallback in item 16): mute the detected Background for `SIMPLE` setups only, and grey out Mute for `CUSTOM` ones.

Record the result in ARCHITECTURE.md. If the render check runs in a few seconds, keep it as a test.

## Scope
- `lighthouse/lights.py`: `world_mute_node(setup)` returns the node Mute acts on, following the verified rule, or `None`. `world_muted(setup)` reports its `mute`.
- `lighthouse/__init__.py`:
  - `lighthouse.mute_world` (`REGISTER`, `UNDO`) flips `mute` on that node. It cancels when there is no node to mute or the world is read-only.
  - Panel: a top row with the world's name and Mute (`HIDE_ON`/`HIDE_OFF`, pressed when muted, like a light row). While muted, the panel's controls are drawn inactive. The row leaves room for task 08's Solo.

## Done when (testable)
- Test: on the factory world, `mute_world` sets the Background's `mute` and leaves Strength unchanged. A second call clears it.
- Test: for a Mix Shader setup, `mute_world` mutes the Mix Shader, or cancels and changes nothing if the fallback was chosen.
- Test: with no world, or nothing linked to Surface, it cancels.
- Test: the mute survives `save_as_mainfile` and `open_mainfile`.
- Test (Recorder): the panel draws Mute pressed when muted. Strength is still drawn, inactive.
- `make test` passes.
- Manual (GUI): Mute darkens the viewport in Rendered shading, the muted node shows red in the Shader Editor, and Ctrl+Z restores it.

## Afterwards
Append a `## v5 task 07: World mute` entry to ARCHITECTURE.md with the verify result. Add `mute_world` (twice) to `tests/smoke_engines.py`.
