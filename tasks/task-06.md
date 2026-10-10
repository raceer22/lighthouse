# Task 06: World rotation

**Depends on:** task-05
**Group:** World · **Source:** `.notes/new-features-decisions.md` items 13 (Rotation), 15

## Goal
When the simple setup has an Environment Texture, the World panel offers Rotation. If a Mapping node feeds the texture's Vector input, a slider drives its Z rotation. With nothing connected to Vector, an **Add Rotation** button inserts *Texture Coordinate (Generated) → Mapping*, and the slider appears in its place. When Vector is wired to anything else, rotation is hidden.

## Scope
- `lighthouse/lights.py`:
  - `WorldSetup` gains `mapping` (the Mapping node linked to the Environment Texture's Vector input, or `None`) and `rotation`: `'MAPPING'`, `'ADDABLE'` (Vector not linked), `'CUSTOM'` (Vector linked to a node that isn't a Mapping node) or `None` (no environment).
  - `add_world_rotation(node_tree, environment)` creates a Texture Coordinate and a Mapping node placed to the left of the texture, links Generated → Mapping Vector → Environment Vector, and returns the Mapping node.
- `lighthouse/__init__.py`:
  - `lighthouse.add_world_rotation` (`REGISTER`, `UNDO`). It refuses unless the scene's world is `SIMPLE` with `rotation == 'ADDABLE'` and not read-only.
  - Panel: for `MAPPING`, draw `prop(mapping.inputs["Rotation"], "default_value", index=2, text="Rotation")`. The socket is an Euler, so it shows in degrees. For `ADDABLE`, draw the Add Rotation button. For `CUSTOM` and `None`, draw nothing.

## Done when (testable)
- Test: an Environment Texture with Vector unlinked gives `ADDABLE`. After `add_world_rotation` the tree has exactly one new Texture Coordinate and one new Mapping node, with Generated → Vector → Vector linked, and `world_setup()` gives `MAPPING`.
- Test: setting the Mapping node's Rotation Z changes only Z, and `world_setup().mapping` is that node.
- Test: Vector linked straight from a Texture Coordinate node (no Mapping) gives `CUSTOM`, and the operator refuses and adds no nodes.
- Test: a Background without an environment gives `rotation = None`.
- Test (Recorder): the panel draws the slider, the button or nothing for the matching cases.
- `make test` passes.
- Manual (GUI): Add Rotation once, then drag the slider and the HDRI turns in the viewport. The new nodes sit tidily left of the texture in the Shader Editor. One Ctrl+Z removes both nodes.

## Afterwards
Append a `## v5 task 06: World rotation` entry to ARCHITECTURE.md. Add `add_world_rotation` on a world with an Environment Texture to `tests/smoke_engines.py`.
