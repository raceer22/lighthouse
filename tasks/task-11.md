# Task 11: Load HDRI… swaps the image

**Depends on:** none
**Group:** Load HDRI · **Source:** `.notes/v6-decisions.md` items 24, 25

## Goal
A **Load HDRI…** button in the World panel opens Blender's image browser and puts the chosen image into the world's Environment Texture node. This task covers every world where that is only an image swap: any setup, simple or custom, with exactly one Environment Texture node. Task 12 adds the case where a node has to be added.

## Scope
- `lighthouse/lights.py`: a helper that finds the world's Environment Texture nodes and says whether Load HDRI can swap (exactly one) or not.
- `lighthouse/__init__.py`, a new `lighthouse.load_hdri` operator (`REGISTER`, `UNDO`):
  - `invoke` opens the file browser (`fileselect_add`) filtered to images, with a `filepath` property.
  - `execute` loads the image (`bpy.data.images.load`, reusing an already loaded one with `check_existing=True`) and sets it on the single Environment Texture. It never adds nodes.
  - Cancels with a warning for a read-only world, or when the world no longer has exactly one Environment Texture.
- World panel: the button shows for any setup with exactly one Environment Texture node. Custom setups with none or several get no button. Its place in the panel is near Strength and Rotation, also under the "Custom world setup" note for custom setups.
- The previous image is left to Blender: it loses a user and is dropped when the file is saved and reopened. Lighthouse doesn't remove it or give it a fake user.

## Done when (testable)
- Test: a simple setup with an Environment Texture: `load_hdri(filepath=...)` sets that node's image to the file. No node is added.
- Test: a custom setup (e.g. a Mix Shader) with exactly one Environment Texture: the image is swapped and the node count is unchanged.
- Test: a custom setup with two Environment Textures, or none: the button isn't drawn, and the operator cancels.
- Test: the previous image keeps no fake user and has one user fewer.
- Use a small image file checked into `tests/` (or written by the test) so nothing depends on downloads.
- `make test` passes.
- Manual (GUI): load an HDRI into a world that already has one, then render and see the new one.

## Afterwards
Append a `## v6 task 11: Load HDRI` entry to ARCHITECTURE.md (which setups get the button, what happens to the old image). Add `load_hdri` to `tests/smoke_engines.py`.
