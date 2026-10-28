# Lighthouse: PRD

## Problem

Managing lights in a Blender scene is slow. Each light's power, color and visibility sit in a separate Properties editor tab, reached by selecting the light first. Adjusting overall lighting means clicking through lights one by one. Power in Watts is also hard to tune by hand, and there is no quick way to solo a light or apply a known setup such as "60W bulb".

## Solution

A Blender extension, **Lighthouse** (id `lighthouse`), that adds a **Lights** tab to the 3D Viewport sidebar (N-panel). It lists every light in the scene with inline controls, and adds bulk intensity tools and per-light presets.

### Light list
- Shows lights in the current view layer, including hidden ones (greyed out). Library lights are read-only.
- Filter by name (search) and by type. Sorted alphabetically.
- One row per light object. Lights that share a datablock show a "linked" indicator.
- Each row has a type icon, a name (click to select the light), a power slider, a color swatch, and mute and solo buttons.
- An expandable detail section holds the remaining properties.
- Type switching and shape parameters (spot size, area shape) stay in the Properties editor.
- Sun lights are shown in W/m², all others in W.

### Intensity controls
- **Scale slider**: multiplies power by a factor, destructively, with normal undo. It applies to all lights or to the selected lights only.
  - Example: three lights at 100 W, 200 W and 400 W scaled by 0.5 become 50 W, 100 W and 200 W.
- **EV buttons**: +1 EV and -1 EV double or halve power. Example: 100 W becomes 200 W with +1 EV.
- **Keyframed lights**: F-curve keyframes are scaled along with the value, so animation is not overwritten on the next frame change.

### Solo and mute
- Both toggle `hide_render` and `hide_viewport` on the light object.
- Solo hides every other light. Un-solo restores the visibility flags saved when solo was turned on.

### Presets
- A preset stores **power, color and soft-size radius**.
- Built-in presets ship with the addon, for example "Candle", "60W Bulb" and "Daylight".
- Users can save their own presets into the Blender user config folder, so they are available in every .blend file.
- Applying a preset sets it on all selected lights of a compatible type. Incompatible lights are skipped.
  - Example: applying "60W Bulb" to a selected point light and a selected sun changes only the point light.

## Constraints

- Target Blender 4.2 and later (the first extension-capable LTS). Tested on Blender 5.2.2 LTS.
- Works with both Cycles and EEVEE. It shows only the properties that exist on each light type.
- Packaged as a Blender extension with `blender_manifest.toml`. License is GPL-3.0-or-later, as extensions require.
- Personal use for now, but nothing should block publishing later.
- Edits go through Blender's normal operators and properties so undo/redo works.
- Python only, with no external dependencies.

## Acceptance Criteria

1. The addon installs as an extension in Blender 5.2.2 and enables without errors.
2. A "Lights" tab appears in the 3D Viewport N-panel and lists all lights in the current view layer.
3. Changing a row's power slider or color updates the light, and the Properties editor reflects it.
4. The name filter and the type filter narrow the list correctly.
5. Clicking a light's name selects it and makes it active.
6. Hidden lights are listed greyed out, and library lights cannot be edited.
7. Scaling by 0.5 halves the power of all lights, or of only the selected lights, depending on the scope chosen. One undo restores the previous values.
8. +1 EV doubles and -1 EV halves power, for all light types including sun.
9. Scaling a keyframed light scales its keyframes too, and the animated value after a frame change matches the scaled value.
10. Solo hides all other lights, and un-solo restores their exact previous visibility flags. Mute hides only that light.
11. Built-in presets apply power, color and radius to the selected compatible lights, and skip incompatible ones.
12. A user preset saved in one .blend file is available after opening another.
13. The addon behaves correctly under both Cycles and EEVEE, with no errors for lights that lack a property.
14. The manifest validates (`blender --command extension validate`) and the extension builds into a zip.

## Out of Scope

- Whole-scene lighting rigs, such as a 3-point or studio setup that creates lights.
- Scene snapshots of light intensities (day/night recall).
- Changing a light's type or editing shape parameters in the panel.
- A non-destructive master multiplier that stores base values.
- Publishing to extensions.blender.org, including its review requirements. The packaging should allow it, but the submission itself is later work.
- Any support for Blender versions below 4.2.

## Additionally
- After implementing each task, append a brief entry to ARCHITECTURE.md detailing: (1) newly added components, (2) how data flows between them, and (3) key Blender API quirks encountered.
