<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/7734f020-498f-4692-bfb2-450799e814ff" />
# Lighthouse

Every light in the scene in one panel in the 3D Viewport, with bulk intensity, solo and mute, and presets.

## Why Lighthouse

Blender's light workflow gets slow once a scene has more than a few lights:

- Each light's power, color and visibility sit in the Properties editor, one light at a time, reached by selecting it first.
- Changing the overall lighting means clicking through the lights one by one.
- There's no quick way to solo a light or a group, or to apply a known setup such as a 60W bulb.
- Interiors, lookdev and cinematic setups, where lighting is tuned over and over, feel it most.

## Features

**Lighthouse** is a Blender extension that adds a **Lights** tab to the 3D Viewport sidebar (N), with five panels, in this order (Presets starts closed):

- **Active Light**: the active object's row (type, name, power, color or Kelvin, mute, solo) and its details, so you can edit it without scrolling the list. With no light active it says "Select a light" and keeps its place.
- **World**: the world's Strength, when the world is *simple*: World Output › Surface comes from a Background node whose Strength isn't driven by another node. Anything else (a Mix Shader, a node group, nodes off) is shown as custom and left alone. With an Environment Texture, **Add Rotation** inserts a Mapping node and then shows its Z rotation. **Mute** mutes the Background node (red in the Shader Editor, saved with the file). **Solo** darkens every light and un-mutes the World, so only the HDRI lights the scene; lamp and group solo leave the World alone, and Exit Solo restores everything. **Load HDRI…** opens the file browser and puts the image in the world's Environment Texture. It works on any world with exactly one Environment Texture node (simple or custom). A simple world with only a Background (like a new file's) gets an Environment Texture added in front of it; Add Rotation then offers rotation. Custom worlds with no or several Environment Textures, and a Background whose Color comes from another node, get no button. The previous image is left to Blender, which drops it on save once nothing uses it.
- **Intensity**: scale all or selected lights by a factor, or step them by −1, −½, −¼, +¼, +½ or +1 EV. Keyframes scale too. The World's strength is never scaled.
- **Presets**: apply, save, overwrite or delete presets of power, color, radius, exposure and Kelvin temperature. The first run writes three defaults (Candle, 60W Bulb, Daylight) as plain files, which you can change or delete like your own (Preferences › Restore Default Presets brings missing ones back). They use Kelvin on Blender 5.0+ and an RGB color on older versions. A .blend saved by an older version with a built-in preset selected opens with no preset selected.
- **Lights**: every light in the view layer, grouped by collection as in the outliner or as a flat list, with search and type filters. Each row has a details toggle, type, name, power, color (or a Kelvin field for lights using temperature), mute and solo. Click a name to select it, Shift+click to select a range, Ctrl+Shift+click to toggle it in the selection, Ctrl+click to rename and Alt+click to frame it. Group headers count their lights and can select, collapse, hide or solo the group, or move the selected lights into it.
  - **Adding**: the header's single `+` menu adds a light (at the 3D cursor) or a collection to the active collection. Right-clicking a collection's name (or the Scene Collection row) adds there instead.
  - **Color or Kelvin**: on Blender 5.0+, the toggle next to `+` sets whether new lights start in Color or in Kelvin for this file. The default for every file is in Edit › Preferences › Add-ons › Lighthouse ("New lights start in"). A file whose toggle was never flipped follows that default.
  - **Light linking**: a light's details end with a Light Linking section. **Link Selected** makes the light light only the selected objects, **Exclude Selected** keeps it off them, each row toggles Include/Exclude, `×` removes one and **Clear** removes all. Lights with linking show a link icon on their row, whose tooltip sums it up and whose click opens the details. When lights share a receiver collection the section says so, and an edit changes all of them. Only receivers are edited (no shadow linking). Collections selected in the Outliner are not picked up: link objects, or add a collection to the light's receiver collection in Object Properties.
  - **Right-click a light's name**: Rename, Frame, Duplicate, Duplicate Linked, Delete, Apply Preset ▸, Mute, Solo and Add to Solo appear above Blender's own entries. Rename, Frame, Solo and Add to Solo act on the clicked light. The others act like the Outliner: on every selected light if the clicked one is selected, otherwise on the clicked light only, and the label shows the count ("Delete 3 Lights"). Delete has no confirmation (Ctrl+Z brings the lights back). Library lights are skipped and reported. A muted light is never selected in Blender, so Unmute acts on the clicked light only.
  - **Additive solo**: Shift+click a light's or a group's solo star to add it to the current solo, or to take it out if it's soloed. Lights and groups mix, and taking out the last one ends solo. A plain click solos only that item. Lights you mute during a solo stay dark when you add or remove targets. The World's solo is always on its own: Shift+click on it works like a click, and soloing a lamp or group leaves it. Exit Solo's tooltip names up to three soloed items.
  - **Alt+drag** (or Alt+Enter) on a row's power, color or Kelvin field changes every selected light, as anywhere in Blender. The field tooltips can't say so, because they are Blender's own.

Light linking by engine (render probe, see [ARCHITECTURE.md](docs/ARCHITECTURE.md)):

| Blender | Cycles | EEVEE | Workbench |
|---|---|---|---|
| 4.2 | yes | no | no |
| 5.2 | yes | yes | no |

Under an engine that doesn't render it, the Light Linking section shows a note and stays editable; the links take effect when you switch.

- Blender 4.2 or later. Tested on 4.2.23 LTS and 5.2.2 LTS, under Cycles and EEVEE. Kelvin temperature needs 5.0+ and light exposure needs 4.4+. Light linking renders in Cycles, and in EEVEE on 5.0+ (see the table above). On older versions, presets set the RGB color instead.
- Pure Python, with no dependencies.
- License: GPL-3.0-or-later (see `lighthouse/LICENSE`).

## Install

```sh
./build.sh                # validates the manifest, then writes dist/lighthouse-<version>.zip
```

In Blender, go to Edit › Preferences › Get Extensions › ▾ › Install from Disk… and pick the zip. Or run `make install`.

## Develop

Set up once:

```sh
python -m venv .venv && .venv/bin/pip install pytest
```

```sh
make test                 # pytest, driving headless Blender
make test BLENDER=/path/to/blender   # the same against another Blender binary
make validate             # blender --command extension validate
make build                # same as ./build.sh
make bench                # time the Lights panel's draw with 500 lights (prints only)
```

`tests/acceptance.md` walks every [PRD-v2](docs/history/PRD-v2.md) acceptance criterion, with a manual GUI checklist. `tests/smoke_engines.py` runs every operator under Cycles and EEVEE against an installed copy. [ARCHITECTURE.md](docs/ARCHITECTURE.md) describes the components and the Blender API quirks.

## Permissions

None declared. User presets are JSON files in the extension's own user folder (`bpy.utils.extension_path_user`), which Blender manages. The extension doesn't read or write anything outside Blender's directories, and it uses no network, clipboard, camera or microphone.
