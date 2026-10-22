# Task 12: Load HDRI… on a Background-only world

**Depends on:** task-11
**Group:** Load HDRI · **Source:** `.notes/v6-decisions.md` item 24

## Goal
A simple world with only a Background node (a plain color, like a new scene's world) also gets **Load HDRI…**. It adds an Environment Texture in front of the Background and loads the image into it. Adding nodes is only safe where the panel fully understands the tree, so this applies to simple setups only.

## Scope
- `lighthouse/lights.py`: a helper that adds an Environment Texture node with the image, linked to the Background's Color and placed to its left (like `add_world_rotation()` places its nodes).
- `load_hdri`: in a `SIMPLE` setup with no Environment Texture, add the node, then load the image. Custom setups with no Environment Texture still get no button (task 11).
- It leaves Rotation alone. The existing **Add Rotation** button then offers it.
- **Verify**: the new node gives a `world_setup()` result of `SIMPLE` with `environment` set and `rotation == 'ADDABLE'`, so the panel shows Strength and Add Rotation, and Add Rotation works on it. Also check that World mute and World solo still act on the Background.

## Done when (testable)
- Test: on a world whose Surface is only a Background, `load_hdri` adds one Environment Texture linked to the Background's Color, with the image set.
- Test: afterwards `world_setup()` is `SIMPLE`, `environment` is the new node, and `rotation` is `'ADDABLE'`. `add_world_rotation` then gives `'MAPPING'`.
- Test: the button is drawn for a Background-only world and not for a custom setup with no Environment Texture.
- Test: Background-only with a linked Color input (some other node) counts as having no Environment Texture: no button, or a cancel. Pick one and pin it with a test.
- `make test` passes, and task 11's tests still pass.
- Manual (GUI): in a new file, Load HDRI, then Add Rotation, then turn Rotation and see the HDRI turn.

## Afterwards
Update the `v6 task 11` entry in ARCHITECTURE.md with the added node and the Verify result.
