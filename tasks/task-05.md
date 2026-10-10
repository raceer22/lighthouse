# Task 05: World panel with Strength

**Depends on:** none
**Group:** World · **Source:** `.notes/new-features-decisions.md` items 12, 13 (Strength), 14, 18

## Goal
A World panel sits right after Lights, open by default, so the order is Lights, World, Intensity, Presets. For a simple setup, where *World Output → Surface* reaches a Background node directly, it shows that Background's Strength. Any other setup shows "Custom world setup, edit in Shader Editor". A scene with no world shows a short message.

## Scope
- `lighthouse/lights.py`:
  - `WorldSetup(state, source, background, environment)` NamedTuple. `state` is `'NONE'` (no world), `'CUSTOM'` or `'SIMPLE'`. `source` is the node linked to the active World Output's Surface (`node_tree.get_output_node('ALL')`), or `None`. `background` is that node when it is a Background node. `environment` is the Environment Texture linked to the Background's Color input, if any. Task 06 adds rotation and task 07 uses `source`.
  - `world_setup(scene)` builds it.
- `lighthouse/__init__.py`:
  - `LIGHTHOUSE_PT_world` (`bl_label = "World"`, same space, region and category as the other panels).
    - `SIMPLE`: `prop(background.inputs["Strength"], "default_value", text="Strength")`.
    - `CUSTOM`: the "Custom world setup, edit in Shader Editor" label.
    - `NONE`: "No world in this scene".
    - The controls are disabled for a read-only (library) world.
  - Register in this order: `LIGHTHOUSE_PT_lights`, `LIGHTHOUSE_PT_world`, `LIGHTHOUSE_PT_intensity`, `LIGHTHOUSE_PT_presets`. With no `bl_order`, registration order is the default panel order, so for new layouts Lights moves above Intensity and Presets. Layouts where the user dragged the panels keep their order.
- Update `tests/test_panels.py` (`PANELS` and the order).

## Open questions
Not decided:
- A Background whose Strength input is linked to another node. Default: treat it as `CUSTOM`, because the slider would do nothing.
- A world with `use_nodes` off (4.x). Default: `CUSTOM`.

## Out of scope
Rotation (task 06), Mute (task 07), Solo (task 08).

## Done when (testable)
- Test: the factory-startup world is `SIMPLE` with its Background and no environment. Adding an Environment Texture into Color gives `environment`.
- Test: a Mix Shader feeding the output, a node group feeding it, and a linked Strength each give `CUSTOM`. `scene.world = None` gives `NONE`. An output with nothing linked to Surface gives `CUSTOM` with `source = None`.
- Test (Recorder): the panel draws the Strength prop for `SIMPLE`, the custom label for `CUSTOM`, and the no-world label for `NONE`.
- Test: the four panels register in the order Lights, World, Intensity, Presets, all top-level in the Lights tab.
- Test (item 18): `scale_lights` with scope All and `step_exposure` with scope All leave the World strength unchanged.
- `make test` passes on 5.2 and on 4.2.
- Manual (GUI): the panel order is right in a fresh layout, dragging Strength updates the viewport, and Ctrl+Z reverts it.

## Afterwards
Append a `## v5 task 05: World panel` entry to ARCHITECTURE.md (detection rule and panel order). Add a `world_setup()` call on the factory world to `tests/smoke_engines.py`.
